# scripts/catalog-gate.jq — the canonical STRUCTURAL gate for plugins.json.
#
# Single source of truth shared by BOTH workflows:
#   - validate-catalog.yml runs it as the blocking sort/dedup/shape step, and
#   - update-checksums.yml re-runs it on the COMPUTED plugins.json immediately
#     before the bot push (GITHUB_TOKEN commits do not re-trigger CI, so the
#     push must carry its own gate — review phlix-plugins__devops M-01).
#
# Fails loudly (halt_error 1 → jq exit 1) when:
#   * plugins.json is unparseable (jq itself exits non-zero on bad JSON),
#   * .plugins is missing/not an array/EMPTY — a zero-entry loop is never a
#     validation (vacuous-pass refusal, review phlix-plugins__devops M-03),
#   * an entry violates the plugins.schema.json core shape: required fields
#     (minServerVersion included, M-PHLIX-PLUGINS-13),
#     name/ref/artifactSha256/repo/version patterns, type enum, the tags
#     charset/count bounds (M-PHLIX-PLUGINS-12), and the
#     dev-entries-are-never-verified law,
#   * entries are out of canonical order (name asc, dev last within name,
#     version tie-break — byte-equivalent to the update-checksums PHP usort
#     comparator AND to the jq sort the old inline gate pinned), or
#   * a (name, version) pair is duplicated.
#
# The ajv JSON-Schema step remains the authoritative FULL-schema check; this
# mirror exists so the PHP-first updater can gate without pulling a Node
# toolchain into its job. Keep both in sync when the schema contract moves
# (tests/test_catalog.py runs this file against the live catalog as a tripwire).

def SEMVER: "^(?:0|[1-9]\\d*)\\.(?:0|[1-9]\\d*)\\.(?:0|[1-9]\\d*)(?:-(?:[0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?(?:\\+[0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*)?$";
def VERSION: "^(?:dev|" + (SEMVER[1:-1]) + ")$";
def TYPES: ["metadata-provider","scrobbler","subtitle-provider","notifier","player","integration","ui-theme"];
def NAME_RE: "^phlix-plugin-[a-z0-9][a-z0-9-]*$";
def REPO_RE: "^https://github\\.com/detain/phlix-plugin-[a-z0-9][a-z0-9-]*/?$";
def TAG_RE: "^[a-z0-9](?:[a-z0-9._-]{0,48}[a-z0-9])?$";
def TAG_MAX: 20;
def badstr($f; $re): (getpath([$f]) | (type == "string" and test($re)) | not);

.plugins as $p
| if ($p | type) != "array" then
    "ERROR: plugins.json has no .plugins array — refusing vacuous gate pass" | halt_error(1)
  elif ($p | length) == 0 then
    "ERROR: plugins array is empty — refusing vacuous gate pass" | halt_error(1)
  else . end
| ($p | map(select(
    badstr("name"; NAME_RE)
    or (((.title | type) != "string") or (.title == ""))
    or badstr("type"; ".")
    or ((.type as $t | (($t | type) == "string" and ((TYPES | index($t)) != null))) | not)
    or badstr("repo"; REPO_RE)
    or badstr("ref"; "^[0-9a-f]{40}$")
    or badstr("artifactSha256"; "^[0-9a-f]{64}$")
    or badstr("version"; VERSION)
    or badstr("minServerVersion"; SEMVER)
    or (.version == "dev" and .verified == true)
    or ((.tags != null) and (
          ((.tags | type) != "array")
          or ((.tags | length) > TAG_MAX)
          or (([.tags[] | (type == "string" and test(TAG_RE))] | all) | not)
        ))
  ))) as $bad
| if ($bad | length) > 0 then
    "ERROR: " + (($bad | length) | tostring) + " malformed entry(ies): "
    + ([$bad[] | ((.name // "?") + "@" + (.version // "?"))] | join(", "))
    | halt_error(1)
  else . end
| ($p | map([.name, .version])) as $pairs
| ($p | sort_by([.name, (if .version == "dev" then 1 else 0 end), .version])) as $sorted
| if $p != $sorted then
    "ERROR: plugins.json is not sorted canonically (name asc, dev last within name; version tie-break).\n  got:  \($pairs | tostring)\n  want: " + (($sorted | map([.name, .version])) | tostring)
    | halt_error(1)
  elif (($pairs | unique) | length) != ($pairs | length) then
    "ERROR: duplicate (name, version) pair(s): "
    + ([$pairs[] | select(. as $kv | ([$pairs[] | select(. == $kv)] | length) > 1)] | unique | tostring)
    | halt_error(1)
  else
    "OK: \($pairs | length) entries — valid JSON, canonical order (name, dev-last within name, version tie-break), schema-shape mirror clean (incl. dev-never-verified), no duplicate (name, version) pairs."
  end
