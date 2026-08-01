"""
Tests for phlix-plugins catalog validation.

This module tests the plugins.json catalog against the rules documented
in the README and enforced by CI:
1. JSON Schema conformance
2. Sorted by name with no duplicates
3. Lockstep ref + artifactSha256
4. Plugin name format
5. Repo URL format
6. Ref (commit SHA) format
7. artifactSha256 format
8. Version semver format
9. Required fields present
"""
import json
import re
import pytest
import jsonschema


class TestCatalogSchema:
    """Tests for JSON Schema conformance."""

    def test_plugins_json_is_valid_json(self, repo_root):
        """plugins.json must be parseable as valid JSON."""
        with open(repo_root / "plugins.json") as f:
            # This will raise json.JSONDecodeError if invalid
            json.load(f)

    def test_schema_version_is_2(self, catalog):
        """schemaVersion must be exactly 2."""
        assert catalog["schemaVersion"] == 2

    def test_catalog_has_required_fields(self, catalog):
        """Catalog must have required top-level fields."""
        assert "schemaVersion" in catalog
        assert "name" in catalog
        assert "plugins" in catalog

    def test_catalog_name_is_non_empty(self, catalog):
        """Catalog name must be a non-empty string."""
        assert isinstance(catalog["name"], str)
        assert len(catalog["name"]) > 0

    def test_plugins_array_is_non_empty(self, plugins):
        """Plugins array must contain at least one entry."""
        assert len(plugins) > 0

    def test_no_additional_properties_at_top_level(self, catalog, schema_json):
        """Top-level must not have unexpected properties."""
        # Define the allowed properties based on schema
        allowed = {"schemaVersion", "name", "description", "homepage", "plugins"}
        actual = set(catalog.keys())
        extra = actual - allowed
        assert not extra, f"Unexpected properties: {extra}"

    def test_plugins_json_validates_against_schema(self, repo_root, schema_json):
        """plugins.json must validate against plugins.schema.json."""
        with open(repo_root / "plugins.json") as f:
            data = json.load(f)
        # jsonschema.validate returns None on success, raises on failure
        jsonschema.validate(data, schema_json)


class TestSortOrder:
    """Tests for sort order and deduplication."""

    def test_plugins_sorted_by_name(self, plugins):
        """Plugins array must be sorted by name."""
        names = [p["name"] for p in plugins]
        sorted_names = sorted(names)
        assert names == sorted_names, f"Plugins not sorted. Got: {names}"

    def test_no_duplicate_plugin_names(self, plugins):
        """Plugin names must be unique (no duplicates)."""
        names = [p["name"] for p in plugins]
        unique_names = set(names)
        assert len(names) == len(unique_names), f"Duplicate names found: {[n for n in names if names.count(n) > 1]}"


class TestPluginName:
    """Tests for plugin name format."""

    PLUGIN_NAME_PATTERN = re.compile(r"^phlix-plugin-[a-z0-9][a-z0-9-]*$")

    def test_all_plugin_names_match_pattern(self, plugins):
        """All plugin names must match the required pattern."""
        for plugin in plugins:
            name = plugin["name"]
            assert self.PLUGIN_NAME_PATTERN.match(name), f"Invalid name format: {name}"

    def test_plugin_names_are_unique(self, plugins):
        """Plugin names must be unique within the catalog."""
        names = [p["name"] for p in plugins]
        assert len(names) == len(set(names)), "Duplicate plugin names found"


class TestPluginRepo:
    """Tests for plugin repo URL format."""

    REPO_PATTERN = re.compile(r"^https://github\.com/detain/phlix-plugin-[a-z0-9][a-z0-9-]*/?$")

    def test_all_plugin_repos_match_pattern(self, plugins):
        """All plugin repo URLs must match the required GitHub pattern."""
        for plugin in plugins:
            repo = plugin["repo"]
            assert self.REPO_PATTERN.match(repo), f"Invalid repo URL: {repo}"


class TestPluginRef:
    """Tests for plugin ref (commit SHA) format."""

    REF_PATTERN = re.compile(r"^[0-9a-f]{40}$")

    def test_all_refs_match_pattern(self, plugins):
        """All refs must be 40-character lowercase hex strings (git commit SHA)."""
        for plugin in plugins:
            ref = plugin["ref"]
            assert self.REF_PATTERN.match(ref), f"Invalid ref format: {ref}"


class TestArtifactSha256:
    """Tests for artifact SHA256 format."""

    SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

    def test_all_artifact_shas_match_pattern(self, plugins):
        """All artifactSha256 must be 64-character lowercase hex strings."""
        for plugin in plugins:
            sha = plugin["artifactSha256"]
            assert self.SHA256_PATTERN.match(sha), f"Invalid artifactSha256 format: {sha}"


class TestPluginVersion:
    """Tests for plugin version (semver) format."""

    SEMVER_PATTERN = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
    )

    def test_all_versions_match_semver(self, plugins):
        """All versions must be valid semantic versions."""
        for plugin in plugins:
            version = plugin["version"]
            assert self.SEMVER_PATTERN.match(version), f"Invalid semver: {version}"


class TestPluginType:
    """Tests for plugin type enum."""

    VALID_TYPES = {
        "metadata-provider",
        "scrobbler",
        "subtitle-provider",
        "notifier",
        "player",
        "integration"
    }

    def test_all_types_are_valid(self, plugins):
        """All plugin types must be from the allowed enum."""
        for plugin in plugins:
            plugin_type = plugin["type"]
            assert plugin_type in self.VALID_TYPES, f"Invalid type: {plugin_type}"


class TestServerVersion:
    """Tests for server version fields."""

    VERSION_PATTERN = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
    )

    def test_min_server_version_is_valid_semver_if_present(self, plugins):
        """minServerVersion, if present, must be valid semver."""
        for plugin in plugins:
            if "minServerVersion" in plugin:
                version = plugin["minServerVersion"]
                assert self.VERSION_PATTERN.match(version), f"Invalid minServerVersion: {version}"

    def test_max_server_version_is_valid_semver_if_present(self, plugins):
        """maxServerVersion, if present, must be valid semver."""
        for plugin in plugins:
            if "maxServerVersion" in plugin:
                version = plugin["maxServerVersion"]
                assert self.VERSION_PATTERN.match(version), f"Invalid maxServerVersion: {version}"


class TestRequiredFields:
    """Tests for required fields on each plugin."""

    REQUIRED_FIELDS = {"name", "title", "type", "repo", "ref", "artifactSha256", "version"}

    def test_all_required_fields_present(self, plugins):
        """Every plugin must have all required fields."""
        for plugin in plugins:
            for field in self.REQUIRED_FIELDS:
                assert field in plugin, f"Plugin missing required field '{field}': {plugin.get('name', 'unknown')}"


class TestBooleanFields:
    """Tests for boolean fields on plugins."""

    def test_verified_is_boolean_if_present(self, plugins):
        """verified field, if present, must be boolean."""
        for plugin in plugins:
            if "verified" in plugin:
                assert isinstance(plugin["verified"], bool), f"verified must be boolean: {plugin['name']}"

    def test_deprecated_is_boolean_if_present(self, plugins):
        """deprecated field, if present, must be boolean."""
        for plugin in plugins:
            if "deprecated" in plugin:
                assert isinstance(plugin["deprecated"], bool), f"deprecated must be boolean: {plugin['name']}"

    def test_yanked_is_boolean_if_present(self, plugins):
        """yanked field, if present, must be boolean."""
        for plugin in plugins:
            if "yanked" in plugin:
                assert isinstance(plugin["yanked"], bool), f"yanked must be boolean: {plugin['name']}"


class TestOptionalFields:
    """Tests for optional field formats."""

    def test_tags_is_array_if_present(self, plugins):
        """tags field, if present, must be an array of strings."""
        for plugin in plugins:
            if "tags" in plugin:
                tags = plugin["tags"]
                assert isinstance(tags, list), f"tags must be array: {plugin['name']}"
                for tag in tags:
                    assert isinstance(tag, str), f"tags must be strings: {plugin['name']}"

    def test_deprecation_message_is_string_if_present(self, plugins):
        """deprecationMessage, if present, must be a string."""
        for plugin in plugins:
            if "deprecationMessage" in plugin:
                msg = plugin["deprecationMessage"]
                assert isinstance(msg, str), f"deprecationMessage must be string: {plugin['name']}"

    def test_author_is_string_if_present(self, plugins):
        """author, if present, must be a string."""
        for plugin in plugins:
            if "author" in plugin:
                author = plugin["author"]
                assert isinstance(author, str), f"author must be string: {plugin['name']}"


class TestLockstepRefSha:
    """Tests for the ref + artifactSha256 lockstep rule."""

    def test_ref_and_sha256_exist_together(self, plugins):
        """If ref exists, artifactSha256 must also exist (and vice versa)."""
        for plugin in plugins:
            has_ref = "ref" in plugin
            has_sha = "artifactSha256" in plugin
            assert has_ref == has_sha, (
                f"Plugin {plugin.get('name', 'unknown')}: ref and artifactSha256 must both be present or both absent"
            )

    def test_no_additional_properties_on_plugins(self, plugins, schema_json):
        """Plugins must not have unexpected properties beyond the schema."""
        # Get allowed properties from schema
        allowed_properties = set(schema_json["$defs"]["plugin"]["properties"].keys())

        for plugin in plugins:
            actual = set(plugin.keys())
            extra = actual - allowed_properties
            assert not extra, f"Plugin {plugin.get('name', 'unknown')} has unexpected properties: {extra}"


class TestSpecificPlugins:
    """Tests for specific plugins in the catalog."""

    def test_all_official_plugins_have_verified_true(self, plugins):
        """All plugins in the official catalog should have verified: true."""
        for plugin in plugins:
            assert plugin.get("verified") is True, f"Plugin {plugin['name']} should be verified"

    def test_all_official_plugins_are_not_deprecated(self, plugins):
        """All plugins in the official catalog should not be deprecated."""
        for plugin in plugins:
            assert plugin.get("deprecated") is not True, f"Plugin {plugin['name']} should not be deprecated"

    def test_all_official_plugins_are_not_yanked(self, plugins):
        """All plugins in the official catalog should not be yanked."""
        for plugin in plugins:
            assert plugin.get("yanked") is not True, f"Plugin {plugin['name']} should not be yanked"

    def test_plugins_have_min_server_version(self, plugins):
        """All plugins should specify minServerVersion."""
        for plugin in plugins:
            assert "minServerVersion" in plugin, f"Plugin {plugin['name']} missing minServerVersion"

    def test_plugins_have_author(self, plugins):
        """All plugins should have an author."""
        for plugin in plugins:
            assert "author" in plugin, f"Plugin {plugin['name']} missing author"

    def test_plugins_have_summary(self, plugins):
        """All plugins should have a summary."""
        for plugin in plugins:
            assert "summary" in plugin, f"Plugin {plugin['name']} missing summary"

    def test_plugins_have_description(self, plugins):
        """All plugins should have a description."""
        for plugin in plugins:
            assert "description" in plugin, f"Plugin {plugin['name']} missing description"

    def test_plugins_have_tags(self, plugins):
        """All plugins should have tags."""
        for plugin in plugins:
            assert "tags" in plugin, f"Plugin {plugin['name']} missing tags"
            assert len(plugin["tags"]) > 0, f"Plugin {plugin['name']} has empty tags"
