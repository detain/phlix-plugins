# Changelog

All notable changes to this repo — the Phlix official plugin **catalog** and the
automation that regenerates `plugins.json`. Format loosely follows Keep a
Changelog. This file started 2026-10-30, retrospectively: the trust-hardening
wave below shipped behavior breaks with no changelog to point at (review
`phlix-plugins__writer` M-PHLIX-PLUGINS-26). `plugins.json` pin churn from the
updater's own bot commits is deliberately NOT logged here — the git history is
that record.

## Unreleased

### Changed — dependency upgrade (2026-11-13)
- Workflows: actions/checkout v6.1.0 -> v7.0.1, actions/setup-node v6.5.0 -> v7.1.0, actions/setup-python v5.6.0 -> v7.1.0 (SHA-pinned). Node 24 and Python 3.12 CI targets unchanged (still supported).
- requirements-test.txt: coverage 7.17.0 -> 7.17.3 (hashes refreshed); every other pin was already the latest release.
- Workflows + README: ajv-formats 2.1.1 -> 3.0.1 (ajv-cli stays 5.0.0, its latest; ajv-formats 3 peers ajv ^8, verified `plugins.json valid` locally).

### Fixed — deferred minors (CAT-S3/CAT-S6, 2026-11-13)
- update-checksums.yml: the fetch census is now an `emitFetchCensus()` helper and also runs on the "all discovered repos skipped/failed" red exit, so the failing run prints it too (log-only; never gates).
- tests: the census is driven with (seconds, curl exit) samples incl. exit 28; the all-skipped census path and the CAT-3 pin-drift step (`set -u -o pipefail`, no curl-fed `sha256sum` pipe, fetchfail exit-1, fake-curl run) are pinned.

### Fixed — plugins-catalog fix program, round-2026-11-11 (2026-11-12)
- validate-catalog.yml: daily attestation cron `17 6 * * *` -> `47 6 * * *` UTC, clearing the updater's 06:00-06:30 run window (CAT-8).
- README truth pass (CAT-5/6/7/11/12): the bot-push trust-root note now names the
  daily schedule as the attestation trigger that re-validates bot-era content
  (pytest stays push/same-repo-PR only); the admission contract states the real
  discovery filter (org + topic + not archived) and separates the updater's
  pin-time manifest subset from the full phlix-shared schema check owned by the
  downstream blocking manifest job; the `signature` cohort is re-counted at the
  current pins (17 `null` incl. all twelve themes / 4 absent — the older entry
  below records the count as of its own date); `title` carry documents the
  three-tier ladder (own > carried sibling > derived); the simulation seam table
  stops claiming `PHLIX_DISCOVERY_JSON` "may not be set" by anything else and
  lists `GITHUB_WORKSPACE` as the write target to point at scratch.
- README: one-line footnote under the Plugins table records the owner ruling of
  2026-11-12 — the bare `phlix-plugin-phantom-mint` is retired, `phlix-plugin-phantom-mint-theme`
  is kept; the bare name remains in the generator-owned catalog while its repo is
  still discovered, and once the repo is archived or loses its `phlix-plugin` topic
  the updater keeps the entries unchanged, so they must then be hand-removed (see
  *Hand-repinning*) (CAT-10). The admission-contract line now notes manifest `name` is only
  compared when present at HEAD (the tagged re-check requires it).

### Fixed — review→fix wave 3, lane w06L10 (2026-11-06)
- README: the Plugins table was regenerated from `plugins.json` — twelve rows were
  stale at the review commit (AniDB 0.3.0→0.4.1, AniList 0.2.0→0.4.0, Example
  0.1.1→0.1.2, Last.fm 1.1.0→1.2.0, MusicBrainz 0.2.0→0.4.0, MyAnimeList
  0.2.0→0.3.0, OMDb 0.2.0→0.3.0, OpenSubtitles 0.2.0→0.6.0, Phantom Mint Theme
  dev-only→1.0.0, Phantom Violet Theme 1.0.0→1.0.1, Trakt 1.2.0→1.5.0) and the
  count line said 41 entries while the catalog carried 42. The stalest cell was
  operator-facing: Sample Theme was advertised `verified: true` after the updater
  had legitimately reset the attestation on a non-fast-forward pin move (review
  plugins-catalog__devops #1[M] + plugins-catalog__docmaint #3[M], PG-216).
- The mirror is durable, not hopeful: new `TestReadmeTableMirrorCatalog` derives
  every table row AND the count line from `plugins.json` and compares byte-exactly
  (reddened at exactly the twelve stale rows + the 41-vs-42 count before the
  README landed), so every future catalog wave forces a human re-sync — the
  updater rewrites the catalog on a 6-hour bot cadence and never touches README,
  which is how the table rotted. The projection is catalog-driven (a teeth test
  mutates a copy and requires exactly the bumped rows to move) and it honors the
  documented dev-only degradation instead of inventing a version.
- update-checksums.yml: `fetchTargetTarball()` now CAPTURES curl's transfer status
  (`-w '%{url_effective}\t%{exitcode}'`) and refuses any non-zero exit before the
  bytes are trusted, and adds a full `gzip -t` stream-integrity pass before
  `sha256sum`. Previously the exit code was thrown away: an HTTP 200 whose body was
  cut mid-stream — exactly what unauthenticated codeload throttling of shared
  runner IPs looks like — left a non-empty file starting with the gzip magic, so
  every old guard passed and the TRUNCATED bytes' digest could become the pinned
  `artifactSha256`. Reproduced locally (200 + half body: old size>0 and magic-byte
  guards both pass; `gzip -t` exits 1 and the new status guard exits 18) and the
  happy path re-proven live (trakt's pin fetched through the new guards hashes to
  the catalog digest) (devops #3[m], PG-217).
- README: the illustrative `plugins.json` entry no longer uses a real plugin name
  with real-shaped stale pins — the pin values are now the unmistakable synthetic
  placeholders (a×40 ref / 0×64 digest) the simulation fixtures already teach, and
  a tripwire refuses any regression toward a copy-pasteable pin
  (docmaint #7[i], PG-123).
- Prose currency: the updater size claim now matches the measured heredoc
  (~1,100 PHP lines, was "~900") (docmaint #5[m], PG-121); validate-catalog's
  pin-drift timeout/advisory comments say "one re-hash per catalog entry" instead
  of a stale "~41" (docmaint #6[m], PG-122); the fixture state-layout doc gained
  the `tagged_name_<name>.txt` line the loader actually reads (docmaint #8[i],
  PG-124).

### Fixed — review→fix wave 2, lane w02L9 (2026-11-06)
- README + schema: `verified` is now documented as what it actually is — a
  maintainer ATTESTATION the server never parses. The default-deny install gate is
  the `ref` + `artifactSha256` pin (`CatalogEntry::verified()` recomputes from pin
  presence; `PHLIX_PLUGINS_ALLOW_UNVERIFIED=1` is the operator override), which is
  also why always-`false` dev entries are installable — the old wording
  contradicted itself. Both test docstrings that recited the false flag-gating law
  were reworded to the pin truth (review plugins-catalog__docmaint #1[M] + #4[m],
  PG-119).
- README + schema: `deprecated`, `yanked` and `deprecationMessage` carry the honest
  "Catalog metadata only" label (the `minServerVersion` idiom): grep across
  phlix-server `src/` has zero consumers of the three fields — nothing warns
  operators, nothing hides entries from listings, nothing renders the message
  (docmaint #2[M], PG-120).
- Both truths are durable, not prose hopes: new `TestOperatorFacingFieldTruth`
  tripwires pin the README rows and schema descriptions to the pin-based reality
  and refuse the reintroduction of the old false claims (reddened at exactly the
  claimed phrases before the docs landed).
- validate-catalog.yml: a daily schedule trigger (`17 6 * * *` UTC) re-attests
  master continuously — the full data-trust legs (ajv schema, blocking pin-drift
  re-hash, manifest gate) run on schedule events; the pytest leg keeps its
  push/same-repo-PR guard (docmaint/devops #2[m] class, PG-116).
- update-checksums.yml Push step: `git fetch --deepen=50` before the rebase retry
  loop — the fetch-depth: 1 checkout could not find a merge base when master
  advanced by two or more commits mid-run (devops #4[i], PG-117); and
  `git diff --cached --stat` moved BEFORE the commit, where it can actually show
  the landed change instead of printing nothing (devops #5[i], PG-118). Both legs
  pinned by new `TestWorkflowContract` tripwires.
- README: the `signature` cohort shape split recorded as deliberate triage
  (LW-039) — five official repos carry the manifest key as `null` (including the
  copy-me example), four omit it; both shapes validate against the phlix-shared
  manifest contract and install identically (`SignatureVerifier` accepts
  missing/null as unsigned). Unnormalized by design pending the owner
  signature-policy ruling (estate reel LW-100).

### Changed — minors campaign batch W-min86 (2026-10-30, vein final)
- Update-checksums push trigger is `master`-only; the dead `main` entry (and the
  README's `master`/`main` prose) implied mixed-branch semantics the updater
  never had (M-PHLIX-PLUGINS-02).
- The updater now names — loudly, every run — catalog entries whose repos are
  absent from discovery. The keep-unchanged contract stands; silence was the
  defect. Automatic `verified: false`/yank of such entries remains an owner
  policy call (M-PHLIX-PLUGINS-11).
- Tags are bounded three ways with one shared law — schema
  (`items.pattern` + `maxItems: 20`), `scripts/catalog-gate.jq` mirror, and
  `computeSyncedTags()` (charset filter + sorted-order cap, every drop WARNed
  through `logSafe`) — so repo-topic farming can no longer mint unbounded
  published tag lists (M-PHLIX-PLUGINS-12).
- `minServerVersion` is now a REQUIRED entry field: an entry whose plugin
  cannot declare a minimum server version predates the install contract. A
  relaxed fork edits its own schema copy — the escape hatch is the fork
  (M-PHLIX-PLUGINS-13). Six test fixtures rotated to the new law while keeping
  each rejection discriminating on its own defect.

### Changed — minors campaign batch W-min85 (2026-10-30)
- Updater log hygiene (M-PHLIX-PLUGINS-10): every untrusted string that reaches
  the job log now passes through a new `logSafe()` — printable-ASCII only,
  GitHub Actions `::` workflow-command tokens defused, capped at 80 chars.
  Wrapped sites: discovery-failure raw dump, gh metadata error body,
  transfer/rename owner/full_name echo, rejected branch/ref echoes, tag name on
  release-fetch failure, manifest name/type rejections, the release-skip reason,
  the pre-guard invalid-repo-name echo, and the fork-guard effective-URL refusal.
- README: the pin recipe now states the codeload-versus-API digest law (the
  `api.github.com` tarball endpoint serves different bytes — the mix-up poisoned
  every pin once) next to the "recompute the digest" step
  (M-PHLIX-PLUGINS-21), and the automation is called by one actor noun, "the
  updater" (M-PHLIX-PLUGINS-20).
- Workflow header: the Robustness contract now enumerates all seven `exit(1)`
  causes including state-file write failure and the shape-invalid catalog
  (M-PHLIX-PLUGINS-24). Three new tripwire tests pin the sanitizer call sites,
  the exit inventory and both README laws.

### Changed — minors campaign batch W-min84 (2026-10-30)
- Removed the two tracked `coverage --cov-report=annotate` junk files
  (`tests/conftest.py,cover`, `tests/test_catalog.py,cover`); `.gitignore` now
  carries `*.cover` (M-PHLIX-PLUGINS-04).
- Completed the updater's local-simulation seam: Phase C's pristine catalog read
  now honors `PHLIX_STATE_DIR` (CI behavior byte-identical — it defaults to
  `/tmp`), and the README gained an "Exercising the updater locally" section
  documenting all four seam env vars with a verified extract-and-run recipe
  (M-PHLIX-PLUGINS-05).
- Resource caps + scratch hygiene (M-PHLIX-PLUGINS-09): `timeout-minutes` on all
  five jobs across both workflows; `--max-time` on every `curl -f` fetch; the
  updater now unlinks each fetched tarball and removes each extract dir once the
  digest and manifest are captured (and on every early-failure path). Four new
  workflow-contract tripwires pin all of this.

### Changed — minors campaign batch W-min82 (2026-10-30, review phlix-plugins minors)
- README: the Plugins table now lists **every** catalog name (it carried 8 of 21;
  the whole `ui-theme` family, `phlix-plugin-example`, and the `verified: true`
  sample-theme were absent) (M-PHLIX-PLUGINS-01/-16).
- README: entry-pairing law told truthfully — release+dev pairing can degrade to
  dev-only when a repo has no usable semver tag or its latest tag fails the
  install-contract gate (M-PHLIX-PLUGINS-18).
- plugins.json: sample-theme curated description spelling `colour` → `color`
  (single British outlier against the theme vocabulary's American `color-*`)
  (M-PHLIX-PLUGINS-26).
- CHANGELOG.md created (M-PHLIX-PLUGINS-26).

### Trust-hardening wave (2026-10-30, majors review `phlix-plugins__devops`/`__seceng`/`__writer`)
Behavior-affecting; **breaking** where flagged.
- `9ac5979` manifest+pin-drift loops can no longer vacuously pass on a broken/empty
  catalog — they fail loud (breaking: a previously-"green" empty run now fails).
- `443fad2` catalog gates travel with the bot push: new shared
  `scripts/catalog-gate.jq`, re-run inside `update-checksums` as a pre-push gate
  (breaking: a computed catalog violating order/dedup/shape now blocks the push).
- `c3c47cb` contain the CI trust surface (breaking: pytest no longer runs on fork
  PRs; `validate-catalog` push trigger scoped to `master`; pin-drift blocks pushes).
- `9f3dbbd` `verified: true` no longer survives recreated tags or
  non-fast-forward lineage — such moves reset it to `false` (re-attestation;
  breaking for trust carry-over; fetches/tarballs must stay `detain`-owned).
- `3719a41` executable tripwires pin the codeload-URL law, updater regex gates,
  trust guards, and the shared gate.
- `ee4a3a5` validator toolchain pinned: every `uses:` action at a full commit SHA,
  ajv at exact versions, requirements hash-locked and consumed with
  `--require-hashes` (breaking: un-annotated bump-style edits rejected by tests).
- `2697c41` the blocking manifest-schema fetch pinned to a `phlix-shared` release
  tag with a committed sha256 digest (breaking: floating-master contract drift
  now fails the job).
- `b63b26a` the updater aborts loudly outside the `detain` org (breaking for forks
  that enabled Actions: previously they were silently rewritten into a copy of
  the official catalog).
- `d403d85` README rewritten to tell the truth: the scheduled workflow is a catalog
  **generator**, the admission contract, triggers, bot-push no-retrigger, the
  release-tag publish flow, install-time-only server version enforcement, and the
  fork posture warning.
- `d96c44d` hash-lock corrected to the python<3.13 marker dependency actually in
  CI's 3.12 install closure.
