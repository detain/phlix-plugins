# Changelog

All notable changes to this repo — the Phlix official plugin **catalog** and the
automation that regenerates `plugins.json`. Format loosely follows Keep a
Changelog. This file started 2026-10-30, retrospectively: the trust-hardening
wave below shipped behavior breaks with no changelog to point at (review
`phlix-plugins__writer` M-PHLIX-PLUGINS-26). `plugins.json` pin churn from the
updater's own bot commits is deliberately NOT logged here — the git history is
that record.

## Unreleased

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
