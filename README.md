# phlix-plugins

The default **plugin catalog** for [Phlix](https://github.com/detain/phlix-server).

`plugins.json` lists the official Phlix plugins and where to install them from.
The Phlix admin **Plugins** section loads this catalog by default, so you can
browse and install plugins in one click — or add another catalog URL, or paste a
single plugin repo URL directly.

## Plugins

| Plugin | Type | Repo |
|---|---|---|
| AniDB | metadata-provider | [phlix-plugin-anidb](https://github.com/detain/phlix-plugin-anidb) |
| MyAnimeList | metadata-provider | [phlix-plugin-myanimelist](https://github.com/detain/phlix-plugin-myanimelist) |
| Trakt | scrobbler | [phlix-plugin-trakt](https://github.com/detain/phlix-plugin-trakt) |

## Catalog format (`plugins.json`)

```json
{
  "schemaVersion": 1,
  "name": "Phlix Official Plugins",
  "plugins": [
    {
      "name": "phlix-plugin-anidb",
      "title": "AniDB",
      "type": "metadata-provider",
      "summary": "Anime metadata from AniDB.",
      "description": "AniDB metadata provider — …",
      "repo": "https://github.com/detain/phlix-plugin-anidb",
      "tags": ["anime", "metadata"]
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `name` | The plugin's manifest name (`phlix-plugin-*`). |
| `title` | Display name. |
| `type` | Plugin category (`metadata-provider`, `scrobbler`, …). |
| `summary` / `description` | Short / long description. |
| `repo` | Git repo URL the plugin installs from. |
| `tags` | Free-form tags. |

## Add your own

Fork this repo (or create your own), edit `plugins.json`, and add its URL as a
plugin source in the Phlix admin **Plugins** section.

## License

MIT — see [LICENSE](LICENSE).
