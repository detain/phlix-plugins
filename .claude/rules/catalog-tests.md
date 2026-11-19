---
name: catalog-tests
description: pytest conventions for the plugins.json catalog test suite
globs: tests/**/*.py, pytest.ini, requirements-test.txt
---

# Catalog tests (`tests/`)

- Run locally with `python3 -m pytest tests/ -v --tb=short`; install deps from
  `requirements-test.txt` (`pytest`, `pytest-cov`, `jsonschema`). Config lives in
  `pytest.ini` (`testpaths = tests`, `test_*.py`, `Test*` classes, `test_*` functions).
- CI runs the same suite in the `pytest` job of
  `.github/workflows/validate-catalog.yml` with `--cov=. --cov-report=term-missing`.
- Load catalog data through the fixtures in `tests/conftest.py` — `repo_root`,
  `plugins_json`, `schema_json`, `catalog`, `plugins` — never re-open
  `plugins.json` / `plugins.schema.json` inline.
- Group assertions into `Test*` classes by invariant (schema, sort order, name,
  repo, ref, sha, version, required fields) and include the offending plugin
  name in every assert message.
- Invariants the suite must keep enforcing, matching the CI `jq` gate:
  canonical order `[name, dev-last, version]`, unique `(name, version)` pairs,
  `ref` 40-char lowercase hex, `artifactSha256` 64-char lowercase hex, `version`
  either semver or the literal `"dev"`, and `dev` entries always `verified: false`.
- Curation checks (`summary`, `description`, `tags`) apply only to entries with
  `verified: true` — auto-discovered entries start un-verified and un-curated.
