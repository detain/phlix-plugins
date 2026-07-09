# phlix-plugins

The default **plugin catalog** for [Phlix](https://github.com/detain/phlix-server).

`plugins.json` lists the official Phlix plugins and where to install them from.
The Phlix admin **Plugins** section loads this catalog by default, so you can
browse and install plugins in one click — or add another catalog URL, or paste a
single plugin repo URL directly.

## Plugins

| Plugin | Type | Version | Min Server | Repo |
|---|---|---|---|---|
| AniDB | metadata-provider | 0.1.0 | ≥ 0.10.0 | [phlix-plugin-anidb](https://github.com/detain/phlix-plugin-anidb) |
| AniList | metadata-provider | 0.1.0 | ≥ 0.14.0 | [phlix-plugin-anilist](https://github.com/detain/phlix-plugin-anilist) |
| Last.fm | scrobbler | 1.0.0 | ≥ 0.15.0 | [phlix-plugin-lastfm](https://github.com/detain/phlix-plugin-lastfm) |
| MusicBrainz | metadata | 0.1.0 | ≥ 0.14.0 | [phlix-plugin-musicbrainz](https://github.com/detain/phlix-plugin-musicbrainz) |
| MyAnimeList | metadata-provider | 0.1.0 | ≥ 0.10.0 | [phlix-plugin-myanimelist](https://github.com/detain/phlix-plugin-myanimelist) |
| OMDb | metadata | 0.1.0 | ≥ 0.15.0 | [phlix-plugin-omdb](https://github.com/detain/phlix-plugin-omdb) |
| OpenSubtitles | subtitle-provider | 0.1.0 | ≥ 0.10.0 | [phlix-plugin-opensubtitles](https://github.com/detain/phlix-plugin-opensubtitles) |
| Trakt | scrobbler | 1.0.0 | ≥ 0.14.0 | [phlix-plugin-trakt](https://github.com/detain/phlix-plugin-trakt) |
| Example | metadata-provider | 0.1.0 | ≥ 0.10.0 | [phlix-plugin-example](https://github.com/detain/phlix-plugin-example) |

## Catalog format (`plugins.json`)

The document shape is described by [`plugins.schema.json`](plugins.schema.json)
(JSON Schema, Draft 2020-12) and validated in CI. `schemaVersion` is now `2`:
every entry **pins an exact commit** (`ref`) and the **sha256 of the codeload
tarball** for that commit (`artifactSha256`), so the Phlix server can verify the
bytes it downloads before installing. Installs target the pinned commit, never a
moving branch.

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
      "ref": "852b472a6aa73b80192af96310fcc789dbcaf8d7",
      "artifactSha256": "e8277e0ed419e4eb02245ad86896025bb6bb8ce90c348d2a7c7ea958724ce08c",
      "version": "0.1.0",
      "minServerVersion": "0.10.0",
      "verified": true,
      "deprecated": false,
      "yanked": false,
      "tags": ["anime", "metadata"]
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `schemaVersion` | yes (top level) | Catalog format version — currently `2`. |
| `name` | yes | The plugin's manifest name (`^phlix-plugin-[a-z0-9][a-z0-9-]*$`). |
| `title` | yes | Display name. |
| `type` | yes | Plugin category (`metadata-provider`, `scrobbler`, …). |
| `repo` | yes | Human repo URL the plugin lives at (`github.com/detain/phlix-plugin-*`). |
| `ref` | yes | 40-char lowercase commit sha the entry is **pinned** to (not a branch/tag). |
| `artifactSha256` | yes | Bare 64-hex sha256 of `…/archive/<ref>.tar.gz` (no `sha256:` prefix). |
| `version` | yes | The plugin's semver at the pinned `ref` (from its `plugin.json`). |
| `minServerVersion` | no | Minimum Phlix server version required (from the plugin's `phlix_min_server_version` at the pinned `ref`). The admin UI shows "incompatible" pre-download when the running server is older. |
| `maxServerVersion` | no | Maximum Phlix server version supported (exclusive upper bound). |
| `verified` | no | Whether this entry has been reviewed by the catalog maintainer (`true` for all official entries). Un-verified entries are install-blocked by the server in default-deny mode. |
| `deprecated` | no | Whether this plugin is deprecated. Deprecated entries may still be installable but the server warns operators. |
| `yanked` | no | Whether this version has been withdrawn. Yanked entries are hidden from the catalog listing. |
| `deprecationMessage` | no | Human-readable message shown for deprecated/yanked entries. |
| `summary` / `description` | no | Short / long description. |
| `author` | no | Catalog-declared author/owner. |
| `tags` | no | Free-form tags. |

The official catalog is the trust root: any change to a `ref` is a reviewable
git diff, so a malicious silent rewrite of an install target is visible in
history. Operators adding their own catalog SHOULD pin `ref` + `artifactSha256`
or the server will refuse the install in default-deny mode.

### Updating a pin

`ref` and `artifactSha256` **must always move in lockstep** — they describe the
same commit. To re-pin a plugin to a newer commit:

```bash
# 1. resolve the new commit sha
ref=$(git ls-remote https://github.com/detain/phlix-plugin-<x> HEAD | cut -f1)

# 2. recompute the tarball digest for THAT commit
sha=$(curl -sL https://github.com/detain/phlix-plugin-<x>/archive/$ref.tar.gz | sha256sum | cut -d' ' -f1)

# 3. read the plugin's semver at that ref (from its plugin.json) and update
#    "ref", "artifactSha256" and "version" together in plugins.json
```

Never bump `ref` without recomputing `artifactSha256` (and vice versa); CI
validates shape, and the server rejects an install whose downloaded bytes do not
hash to the recorded `artifactSha256`.

## Validating locally

```bash
# ajv-cli needs ajv-formats for the "uri" format keyword:
npx --yes -p ajv-cli@5 -p ajv-formats@2 ajv validate \
  --spec=draft2020 -c ajv-formats -s plugins.schema.json -d plugins.json
# or with check-jsonschema:
#   python3 -m pip install check-jsonschema
#   check-jsonschema --schemafile plugins.schema.json plugins.json
```

## Add your own

Fork this repo (or create your own), edit `plugins.json` (keeping it valid
against `plugins.schema.json` — pin `ref` + `artifactSha256` + `version` per
entry), and add its URL as a plugin source in the Phlix admin **Plugins**
section.

## License

MIT — see [LICENSE](LICENSE).
