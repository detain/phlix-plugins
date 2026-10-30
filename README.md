# phlix-plugins

The default **plugin catalog** for [Phlix](https://github.com/detain/phlix-server).

`plugins.json` lists the official Phlix plugins and where to install them from.
The Phlix admin **Plugins** section loads this catalog by default — at a pinned
catalog **release tag**, not at `master` (see
[Publishing a catalog release](#publishing-a-catalog-release-what-servers-actually-read);
a merge to master is not live for operators until a tag is cut and the server's
pin follows it) — so you can browse and install plugins in one click, or add
another catalog URL, or paste a single plugin repo URL directly.

## Plugins

The catalog currently carries **21 plugin names / 41 entries** — a name normally
appears twice (a semver `release` entry plus a `"dev"` twin, see the `version`
field below; the dev twins are omitted from the table). This table mirrors the
release entries of [`plugins.json`](plugins.json) **at this commit** — that file
is the source of truth, and remember `master` is not operator-live until a
catalog release tag is cut
([Publishing a catalog release](#publishing-a-catalog-release-what-servers-actually-read)).

| Plugin | Type | Release | Min Server | Verified | Repo |
|---|---|---|---|---|---|
| AniDB | `metadata-provider` | 0.3.0 | ≥ 1.2.0 | true | [phlix-plugin-anidb](https://github.com/detain/phlix-plugin-anidb) |
| AniList | `metadata-provider` | 0.2.0 | ≥ 1.2.0 | true | [phlix-plugin-anilist](https://github.com/detain/phlix-plugin-anilist) |
| Arctic Jade Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-arctic-jade-theme](https://github.com/detain/phlix-plugin-arctic-jade-theme) |
| Emerald Abyss Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-emerald-abyss-theme](https://github.com/detain/phlix-plugin-emerald-abyss-theme) |
| Example | `metadata-provider` | 0.1.1 | ≥ 0.10.0 | false | [phlix-plugin-example](https://github.com/detain/phlix-plugin-example) |
| Jade Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-jade-theme](https://github.com/detain/phlix-plugin-jade-theme) |
| Last.fm | `scrobbler` | 1.1.0 | ≥ 1.2.0 | true | [phlix-plugin-lastfm](https://github.com/detain/phlix-plugin-lastfm) |
| MusicBrainz | `metadata-provider` | 0.2.0 | ≥ 1.2.0 | true | [phlix-plugin-musicbrainz](https://github.com/detain/phlix-plugin-musicbrainz) |
| MyAnimeList | `metadata-provider` | 0.2.0 | ≥ 1.2.0 | true | [phlix-plugin-myanimelist](https://github.com/detain/phlix-plugin-myanimelist) |
| Mystic Jade Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-mystic-jade-theme](https://github.com/detain/phlix-plugin-mystic-jade-theme) |
| Obsidian Flame Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-obsidian-flame-theme](https://github.com/detain/phlix-plugin-obsidian-flame-theme) |
| OMDb | `metadata-provider` | 0.2.0 | ≥ 1.2.0 | true | [phlix-plugin-omdb](https://github.com/detain/phlix-plugin-omdb) |
| OpenSubtitles | `subtitle-provider` | 0.2.0 | ≥ 1.2.0 | true | [phlix-plugin-opensubtitles](https://github.com/detain/phlix-plugin-opensubtitles) |
| Phantom Mint | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-phantom-mint](https://github.com/detain/phlix-plugin-phantom-mint) |
| Phantom Mint Theme | `ui-theme` | — (dev-only) | ≥ 0.44.0 | false | [phlix-plugin-phantom-mint-theme](https://github.com/detain/phlix-plugin-phantom-mint-theme) |
| Phantom Violet Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-phantom-violet-theme](https://github.com/detain/phlix-plugin-phantom-violet-theme) |
| Sample Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | true | [phlix-plugin-sample-theme](https://github.com/detain/phlix-plugin-sample-theme) |
| Spectral Dusk Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-spectral-dusk-theme](https://github.com/detain/phlix-plugin-spectral-dusk-theme) |
| Trakt | `scrobbler` | 1.2.0 | ≥ 1.2.0 | true | [phlix-plugin-trakt](https://github.com/detain/phlix-plugin-trakt) |
| Void Bloom Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-void-bloom-theme](https://github.com/detain/phlix-plugin-void-bloom-theme) |
| Volcanic Ember Theme | `ui-theme` | 1.0.0 | ≥ 0.44.0 | false | [phlix-plugin-volcanic-ember-theme](https://github.com/detain/phlix-plugin-volcanic-ember-theme) |

## Catalog format (`plugins.json`)

The document shape is described by [`plugins.schema.json`](plugins.schema.json)
(JSON Schema, Draft 2020-12) and validated in CI by
[`.github/workflows/validate-catalog.yml`](.github/workflows/validate-catalog.yml),
which also asserts entries are in canonical order (sorted by `name`, release before
the `dev` entry within a name) with unique (`name`, `version`) pairs, and that each
pinned plugin's `plugin.json` satisfies the phlix-shared manifest schema (the
same contract the server enforces at install time — fetched at a **pinned tag**
and sha256-digest-verified, never a floating branch) — plus a `pytest` job that
runs the catalog test suite in `tests/test_catalog.py`, including tripwires that
pin the CI workflows' own trust laws. The structural half of that gate lives in
[`scripts/catalog-gate.jq`](scripts/catalog-gate.jq): the single-source filter the
updater ALSO re-runs on its computed file before every bot push. `schemaVersion`
is now `2`:
every entry **pins an exact commit** (`ref`) and the **sha256 of the codeload
tarball** for that commit (`artifactSha256`), so the Phlix server can verify the
bytes it downloads before installing. Installs always target that one immutable
commit, never a moving branch — including a `dev` entry: its commit is the
default branch's HEAD *as re-captured by the updater at the last refresh*, so the
dev channel follows the branch by re-pinning forward, not by asking installers
to resolve a branch name.

```json
{
  "schemaVersion": 2,
  "name": "Phlix Official Plugins",
  "plugins": [
    {
      "name": "phlix-plugin-anidb",
      "title": "AniDB",
      "type": "metadata-provider",
      "summary": "Anime metadata from AniDB.",
      "description": "AniDB metadata provider — …",
      "repo": "https://github.com/detain/phlix-plugin-anidb",
      "ref": "3bf51b6822b15ec990832169be0443189e28a729",
      "artifactSha256": "6de62ceef330f18faebc1e1b400dd4566ba4b25578164950b36d439ddb692b85",
      "version": "0.3.0",
      "minServerVersion": "1.2.0",
      "verified": true,
      "deprecated": false,
      "yanked": false,
      "tags": ["anime", "metadata"]
    }
  ]
}
```

Catalog **top-level** fields (per `plugins.schema.json`):

| Field | Required | Meaning |
|---|---|---|
| `schemaVersion` | yes | Catalog format version — currently `2`. |
| `name` | yes | Human-readable catalog name (`"Phlix Official Plugins"`). |
| `plugins` | yes | The entries array below; at least one entry. |
| `description` | no | Optional long description of the catalog itself. |
| `homepage` | no | Optional catalog homepage URL. |

Per-**entry** fields (each object in `plugins`):

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | The plugin's manifest name (`^phlix-plugin-[a-z0-9][a-z0-9-]*$`). |
| `title` | yes | Display name. |
| `type` | yes | Plugin category — the full schema enum is `metadata-provider`, `scrobbler`, `subtitle-provider`, `notifier`, `player`, `integration`, `ui-theme`. (`ui-theme` — a plugin registering a `Phlix\Theming\ThemeSourceInterface` entry class — is the catalog's largest category by name count, 12 of the 21 current names.) |
| `repo` | yes | Human repo URL the plugin lives at (`github.com/detain/phlix-plugin-*`). |
| `ref` | yes | 40-char lowercase commit sha the entry is **pinned** to (not a branch/tag). |
| `artifactSha256` | yes | Bare 64-hex sha256 of `…/archive/<ref>.tar.gz` (no `sha256:` prefix). |
| `version` | yes | Semver at the pinned `ref` (from its `plugin.json`), or the literal `"dev"` for a plugin's dev-channel entry (HEAD of the default branch — re-pinned every catalog refresh, always `verified: false`). A plugin normally appears as a release entry plus, once the updater has seen it, a `dev` entry with the same `name` — **at most two entries per name**. The pairing can lawfully degrade to **dev-only**: a repo with no usable semver tag, or whose latest tag fails the install-contract gate (invalid/missing `plugin.json` at the tag), is kept as a dev entry while its release entry is skipped (the updater logs `SKIP <name>: release entry skipped … keeping dev entry only`). |
| `minServerVersion` | no | Minimum Phlix server version the plugin declares (from its `phlix_min_server_version` at the pinned `ref`). **Catalog metadata only:** the current server does not include this field in its catalog wire shape and does not pre-gate the admin UI with it — it enforces compatibility at install time, after download, from the plugin's own manifest (`PluginLoader::satisfiesServerVersion`). |
| `maxServerVersion` | no | Maximum Phlix server version supported (exclusive upper bound). Same metadata-only status as `minServerVersion`. |
| `verified` | no | Whether this entry has been reviewed by the catalog maintainer. Un-verified entries are install-blocked by the server in default-deny mode. Dev-channel entries are always `false`; auto-discovered entries start `false`. The updater RESETS a carried `true` to `false` as a re-attestation event whenever an auto pin move is not a fast-forward of the previously pinned commit, or a tag is recreated (same version, different commit). |
| `deprecated` | no | Whether this plugin is deprecated. Deprecated entries may still be installable but the server warns operators. |
| `yanked` | no | Whether this version has been withdrawn. Yanked entries are hidden from the catalog listing. |
| `deprecationMessage` | no | Human-readable message shown for deprecated/yanked entries. |
| `summary` / `description` | no | Short / long description. |
| `author` | no | Catalog-declared author/owner. |
| `tags` | no | Free-form tags; the updater unions repo topics (minus a dynamic majority-family denylist **and** an owner-curated static floor such as `media-server`/`plex`/`composer-package`) with curated tags (minus the static floor only). |

The official catalog is the trust root: any change to a `ref` is a reviewable
git diff, so a malicious silent rewrite of an install target is visible in
history. Operators adding their own catalog SHOULD pin `ref` + `artifactSha256`
or the server will refuse the install in default-deny mode.

One consequence of GitHub's event model worth knowing (and the reason the
updater carries its own gate): commits pushed by the updater's `GITHUB_TOKEN`
do **not** re-trigger workflows — GitHub skips workflow starts for bot pushes
made with that token. The bot's own pushes therefore pass only the structural
gate (`scripts/catalog-gate.jq`, re-run inside the updater as a pre-push step:
valid input, canonical order, pair uniqueness, schema-shape mirror,
dev-never-verified); ajv's full schema check, the pytest suite, the pin-drift
re-hash and the manifest-contract gate run against every HUMAN push and PR —
including the human review push of a bot commit, which is how a bot-era
regression still reaches a red gate. Trust-boundary decisions the structural
gate cannot make (lineage of a carried `verified`, org ownership of a fetch
target) are enforced inside the updater itself — see its workflow header.

## How the catalog is regenerated (`update-checksums.yml`)

Despite the file name, the scheduled workflow
([`.github/workflows/update-checksums.yml`](.github/workflows/update-checksums.yml))
is a **catalog generator**, not a checksum fixer: it rebuilds every *discovered*
plugin's entry from the plugin repo's current state, then pushes when anything
moved.

- **Admission contract:** a plugin is in the official catalog iff its repo is in
  the `detain` org, carries the `phlix-plugin` topic, and ships a `plugin.json`
  that validates against the phlix-shared manifest contract. There is no
  allow-list step — the topic IS the opt-in.
- **Per discovered plugin:** a `release` entry at the latest semver tag (version
  read from that tag's `plugin.json`, `ref` = the tag commit, `artifactSha256` =
  sha256 of the codeload `archive/<ref>.tar.gz` bytes), plus a `dev` entry pinned
  to the default-branch HEAD (`version` literal `"dev"`, always
  `verified: false`). Release entries whose version no longer matches the latest
  tag are removed (stale-version cleanup); repo tags sync into `tags` minus a
  dynamic majority-family denylist and the owner-curated static floor.
- **Curated fields survive roll-forwards:** `title` (own > derived), `summary`
  and `description` carry forward; `verified` carries only while the pin ADVANCES
  along fast-forward lineage — a recreated tag (same version, new commit) or a
  non-ancestor pin move resets it to `false` (re-attestation, see the workflow
  header). New auto-discovered entries start `verified: false`.
- **Triggers:** a 6-hourly cron, a push to `master`/`main`, and manual
  `repository_dispatch` of type `plugin-push` (the payload is never read — a
  dispatch just means "run now").
- **Shape:** one PHP-first job (`shell_exec` of `gh`/`curl`/`sha256sum` — no
  Python there by owner law), self-gated before push via
  `scripts/catalog-gate.jq` because its own `GITHUB_TOKEN` pushes do not re-run
  CI (see the trust-root note above).

### Hand-repinning — and what survives the bot

For plugins the updater **discovers** (the official set), pins are derived, not
authored:

- A release entry's `ref`/`artifactSha256`/`version` follow the plugin's
  **semver tags**. Hand-pinning a discovered release entry to an untagged commit
  is deleted or re-pinned by the bot on the very next run — the stale-version
  cleanup sees a version that doesn't match the latest tag.
- A `dev` entry re-pins to HEAD every run; hand edits there don't survive
  either (that is the channel's purpose).
- To move an official pin: cut the tag in the plugin repo (release), or push the
  default branch and dispatch `plugin-push` (dev). Do not edit `plugins.json` by
  hand for discovered plugins.

Entries the updater does **not** discover — your own fork's catalog, or a plugin
whose repo lost its topic — are never touched, and there the manual recipe is
authoritative. `ref` and `artifactSha256` **must always move in lockstep** —
they describe the same commit:

```bash
# 1. resolve the new commit sha
ref=$(git ls-remote https://github.com/detain/phlix-plugin-<x> HEAD | cut -f1)

# 2. recompute the tarball digest for THAT commit
sha=$(curl -sL https://github.com/detain/phlix-plugin-<x>/archive/$ref.tar.gz | sha256sum | cut -d' ' -f1)

# 3. read the plugin's semver at that ref (from its plugin.json) and update
#    "ref", "artifactSha256" and "version" together in plugins.json
```

Compute `artifactSha256` **only** from the archive-form tarball shown in step 2 —
`https://github.com/<owner>/<repo>/archive/<ref>.tar.gz`. GitHub's *API* tarball
endpoint (`https://api.github.com/repos/<owner>/<repo>/tarball/<ref>`) serves
**different bytes** for the same commit, so its digest never matches a
codeload-based pin and bumping with it poisons the entry (this exact mix-up
poisoned every pin in the catalog once; CI's pin-drift job hashes the
archive form).

Never bump `ref` without recomputing `artifactSha256` (and vice versa); CI
validates shape, sort order and every pinned plugin's `plugin.json` manifest,
the blocking pin-drift job re-hashes each pinned tarball on pushes, and the
server rejects an install whose downloaded bytes do not hash to the recorded
`artifactSha256`.

## Publishing a catalog release (what servers actually read)

Server-side Phlix does **not** track this repo's `master`. The stable channel
resolves the official catalog at an immutable release *tag* pinned in server
code — `CatalogSourceResolver::OFFICIAL_PINNED_REF` in
[phlix-server](https://github.com/detain/phlix-server) (operators can override
that ref with the `PHLIX_PLUGINS_CATALOG_REF` environment variable). Bot commits
and reviewed merges to `master` therefore change what *reviewers* see, not what
*installs* happen — do not treat a "review those commits" style push as a
release action.

To publish catalog changes to operators:

1. Land them on `master` (a human push, or the updater's refreshed push).
2. Cut a catalog release tag here (semver, e.g. `v2.5.0`) — release waves are
   maintainer-scheduled; the automation never tags.
3. Bump `OFFICIAL_PINNED_REF` in phlix-server to the new tag (or have operators
   set `PHLIX_PLUGINS_CATALOG_REF`).

## Validating locally

```bash
# ajv-cli needs ajv-formats for the "uri" format keyword — exact versions, the
# same pins the CI schema job uses (floating @5/@2 re-resolve to upstream-next):
npx --yes -p ajv-cli@5.0.0 -p ajv-formats@2.1.1 ajv validate \
  --spec=draft2020 -c ajv-formats -s plugins.schema.json -d plugins.json
# or with check-jsonschema:
#   python3 -m pip install check-jsonschema
#   check-jsonschema --schemafile plugins.schema.json plugins.json

# The canonical-order / (name,version) dedup / shape-mirror gate (single source
# of truth — the same script CI runs, and the updater runs before pushing):
jq -e -r -f scripts/catalog-gate.jq plugins.json
```

The same assertions (schema conformance, canonical order, `(name, version)`
uniqueness, `ref`/`artifactSha256` lockstep and format, `dev` entries never
`verified`) — plus tripwires pinning the CI workflows' own trust laws — are
covered by the pytest suite in [`tests/test_catalog.py`](tests/test_catalog.py)
(fixtures in [`tests/conftest.py`](tests/conftest.py), config in [`pytest.ini`](pytest.ini)):

```bash
# --require-hashes installs exactly the hash-locked closure CI installs:
python3 -m pip install --require-hashes -r requirements-test.txt
python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing
```

## Exercising the updater locally (simulation)

The updater is ~900 lines of PHP living inside a YAML heredoc — deliberate (the
PHP-first single-job law keeps it next to its trigger), but it is still fully
runnable **off** GitHub Actions against fixtures. Extract the script, then drive
it with the four seam variables the script itself reads:

| Env var | Effect |
|---|---|
| `PHLIX_DISCOVERY_JSON` | JSON array of repo names — replaces the Phase A `gh api` topic search (nothing else may set it; without it, discovery hits GitHub live) |
| `PHLIX_SKIP_FETCH` | any non-empty value — Phase B reads fixture state files instead of `gh`/`curl` |
| `PHLIX_STATE_DIR` | where the Phase B state files AND the pristine `plugins.json` are read from (default `/tmp` — exactly what CI uses) |
| `PHLIX_PHASE_B_ONLY` | any non-empty value — stop after Phase B, so Phase C merges can be re-run against the same captured state |

```bash
scratch=$(mktemp -d /tmp/opencode/phlix-plugins-sim.XXXXXX)

# 1. extract the heredoc PHP (body indented 10 spaces inside the run step)
sed -n "/php << 'PHPEOF'/,/^          PHPEOF\$/p" .github/workflows/update-checksums.yml \
  | sed '1d;$d;s/^          //' > "$scratch/updater.php"
php -l "$scratch/updater.php"

# 2. fixtures: one discovered plugin pinned at a syntactically valid HEAD
#    (state-file layout documented in the heredoc; digests may be literal test
#    values in sim — Phase B is skipped, nothing re-hashes them)
cp plugins.json "$scratch/plugins.json"
printf '%s\n' "$(printf 'a%.0s' $(seq 1 40))" > "$scratch/ref_phlix-plugin-anidb.txt"
printf '%s\n' "$(printf '0%.0s' $(seq 1 64))" > "$scratch/sha256_phlix-plugin-anidb.txt"
printf '%s\n' '["anime","metadata"]' > "$scratch/topics_phlix-plugin-anidb.json"

# 3. run the merge with GITHUB_WORKSPACE pointed at the SCRATCH copy — never
#    the checkout — and read the rewrite back as a diff
PHLIX_STATE_DIR="$scratch" PHLIX_SKIP_FETCH=1 PHLIX_DISCOVERY_JSON='["phlix-plugin-anidb"]' \
  GITHUB_WORKSPACE="$scratch" php "$scratch/updater.php"
diff "$scratch/plugins.json" plugins.json
```

A `manifest_<name>.json` fixture (the plugin's `plugin.json` at the ref) makes
the run behave like production for the title/type/version/minServerVersion
paths; without one, the merge SKIPs the repo at the manifest gate, which is
itself a useful thing to see locally.

## Add your own

Fork this repo (or create your own), edit `plugins.json` (keeping it valid
against `plugins.schema.json` — pin `ref` + `artifactSha256` + `version` per
entry), and add its URL as a plugin source in the Phlix admin **Plugins**
section.

**On a fork, delete or disable `.github/workflows/update-checksums.yml` before
enabling Actions.** The updater is hardcoded to the `detain` org end to end
(org-scoped discovery, detain tarball fetches, `repo`-field construction): left
enabled it would rewrite your `plugins.json` into a copy of the official catalog
— it now aborts with an error step instead of doing that silently, but the
correct fork posture is removal. The rest of the toolchain is fork-safe with one
edit: relax the `^https://github\.com/detain/` repo pattern in
`plugins.schema.json` (and the same mirror in `scripts/catalog-gate.jq`) to your
own org.

## License

MIT — see [LICENSE](LICENSE).
