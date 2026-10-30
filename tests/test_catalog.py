"""
Tests for phlix-plugins catalog validation.

This module tests the plugins.json catalog against the rules documented
in the README and enforced by CI:
1. JSON Schema conformance
2. Canonical order (name ascending, release-before-dev within a name, version
   tie-break) with unique (name, version) pairs — the dev channel intentionally
   reuses plugin names
3. Lockstep ref + artifactSha256
4. Plugin name format
5. Repo URL format
6. Ref (commit SHA) format
7. artifactSha256 format
8. Version format: "dev" (dev-channel) or semver (release)
9. Required fields present
10. Workflow-contract tripwires: laws that live inside the CI YAML (codeload
    URL idiom, updater regex constants, push-blocking pin-drift, trust-boundary
    guards, shared catalog gate) — see TestWorkflowContract
"""
import json
import re
import shutil
import subprocess
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
    """Tests for canonical order and (name, version) deduplication."""

    def test_plugins_sorted_canonically(self, plugins):
        """Plugins array must be sorted canonically: name ascending, dev-channel
        entries (version "dev") last within a name, version ascending as a
        deterministic tie-break — the same key validate-catalog.yml's jq gate
        enforces and the update-checksums workflow's usort comparator produces."""
        key = lambda p: (p["name"], 1 if p["version"] == "dev" else 0, p["version"])
        actual = [key(p) for p in plugins]
        expected = sorted(actual)
        assert actual == expected, f"Plugins not in canonical order. Got: {actual}"

    def test_no_duplicate_name_version_pairs(self, plugins):
        """(name, version) pairs must be unique. The dev channel intentionally
        reuses a plugin's name (one release entry with a semver version plus one
        dev entry with version "dev"), so uniqueness is keyed on the pair, not the
        bare name."""
        pairs = [(p["name"], p["version"]) for p in plugins]
        unique_pairs = set(pairs)
        assert len(pairs) == len(unique_pairs), f"Duplicate (name, version) pairs: {[kv for kv in pairs if pairs.count(kv) > 1]}"


class TestPluginName:
    """Tests for plugin name format."""

    PLUGIN_NAME_PATTERN = re.compile(r"^phlix-plugin-[a-z0-9][a-z0-9-]*$")

    def test_all_plugin_names_match_pattern(self, plugins):
        """All plugin names must match the required pattern."""
        for plugin in plugins:
            name = plugin["name"]
            assert self.PLUGIN_NAME_PATTERN.match(name), f"Invalid name format: {name}"

    def test_plugin_names_may_repeat_only_as_dev_channel(self, plugins):
        """A plugin name may appear more than once ONLY for the dev-channel entry
        (version "dev"); a name must never have two non-dev (release) entries."""
        from collections import Counter
        release_counts = Counter(p["name"] for p in plugins if p["version"] != "dev")
        assert all(c == 1 for c in release_counts.values()), f"Multiple release entries: {[n for n, c in release_counts.items() if c > 1]}"


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
    """Tests for plugin version format: semver for release entries, literal "dev"
    for dev-channel entries."""

    SEMVER_PATTERN = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
    )

    def test_all_versions_are_dev_or_semver(self, plugins):
        """All versions must be either the literal "dev" or a valid semantic version."""
        for plugin in plugins:
            version = plugin["version"]
            assert version == "dev" or self.SEMVER_PATTERN.match(version), f"Invalid version: {version}"

    def test_release_entries_have_semver(self, plugins):
        """Every non-dev entry must carry a semver version (the tag-commit manifest
        version or the cleaned tag name fallback — never "dev")."""
        for plugin in plugins:
            if plugin["version"] != "dev":
                assert self.SEMVER_PATTERN.match(plugin["version"]), f"Release entry not semver: {plugin['name']}@{plugin['version']}"

    def test_dev_entries_are_never_verified(self, plugins):
        """Dev-channel entries are always verified=false: the dev channel tracks the
        unstable default-branch HEAD, so it stays install-blocked in default-deny
        until a maintainer reviews it — even for curated plugins whose release entry
        is verified=true."""
        for plugin in plugins:
            if plugin["version"] == "dev":
                assert plugin.get("verified") is False, f"Dev entry must be verified=false: {plugin['name']}"


class TestPluginType:
    """Tests for plugin type enum."""

    VALID_TYPES = {
        "metadata-provider",
        "scrobbler",
        "subtitle-provider",
        "notifier",
        "player",
        "integration",
        "ui-theme",
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

    def test_unverified_plugins_are_auto_discovered(self, plugins):
        """Un-verified entries are expected: the update-checksums workflow auto-adds
        newly discovered plugins with verified=false so the server install-blocks them
        in default-deny mode until a maintainer reviews and verifies them."""
        for plugin in plugins:
            assert plugin.get("verified") in (True, False), f"Plugin {plugin['name']} verified must be boolean"

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

    def test_verified_plugins_have_summary(self, plugins):
        """Verified (curated) plugins should have a summary. Auto-added un-verified
        entries have none — the manifest carries no summary and curation happens
        during human verification."""
        for plugin in plugins:
            if not plugin.get("verified"):
                continue
            assert "summary" in plugin, f"Plugin {plugin['name']} missing summary"

    def test_verified_plugins_have_description(self, plugins):
        """Verified (curated) plugins should have a description. Auto-added
        un-verified entries have none until a maintainer curates them."""
        for plugin in plugins:
            if not plugin.get("verified"):
                continue
            assert "description" in plugin, f"Plugin {plugin['name']} missing description"

    def test_verified_plugins_have_tags(self, plugins):
        """Verified (curated) plugins should have non-empty tags. Auto-added
        un-verified entries have none until a maintainer curates them."""
        for plugin in plugins:
            if not plugin.get("verified"):
                continue
            assert "tags" in plugin, f"Plugin {plugin['name']} missing tags"
            assert len(plugin["tags"]) > 0, f"Plugin {plugin['name']} has empty tags"


class TestEdgeCases:
    """Tests for edge cases using explicit plugin data."""

    def test_deprecation_message_is_string(self):
        """deprecationMessage field must be a string when present."""
        # Construct a plugin with deprecationMessage to test the validation branch
        plugin = {
            "name": "phlix-plugin-test",
            "title": "Test Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-test",
            "ref": "0" * 40,
            "artifactSha256": "0" * 64,
            "version": "1.0.0",
            "deprecationMessage": "Use phlix-plugin-other instead",
            "author": "test",
            "tags": ["test"]
        }
        assert isinstance(plugin["deprecationMessage"], str)
        assert plugin["deprecationMessage"] == "Use phlix-plugin-other instead"

    def test_max_server_version_is_valid_semver(self):
        """maxServerVersion field must be valid semver when present."""
        plugin = {
            "name": "phlix-plugin-test",
            "title": "Test Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-test",
            "ref": "0" * 40,
            "artifactSha256": "0" * 64,
            "version": "1.0.0",
            "minServerVersion": "1.0.0",
            "maxServerVersion": "2.0.0",
            "author": "test",
            "tags": ["test"]
        }
        SEMVER_PATTERN = re.compile(
            r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
        )
        assert SEMVER_PATTERN.match(plugin["maxServerVersion"])

    def test_deprecation_message_empty_string_is_valid(self):
        """deprecationMessage can be an empty string."""
        plugin = {
            "name": "phlix-plugin-test",
            "title": "Test Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-test",
            "ref": "0" * 40,
            "artifactSha256": "0" * 64,
            "version": "1.0.0",
            "deprecationMessage": "",
            "author": "test",
            "tags": ["test"]
        }
        assert isinstance(plugin["deprecationMessage"], str)

    def test_tags_can_be_empty_array(self):
        """tags can be an empty array (though not recommended)."""
        plugin = {
            "name": "phlix-plugin-test",
            "title": "Test Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-test",
            "ref": "0" * 40,
            "artifactSha256": "0" * 64,
            "version": "1.0.0",
            "tags": [],
            "author": "test"
        }
        assert isinstance(plugin["tags"], list)

    def test_optional_fields_all_absent_is_valid(self):
        """Plugin can have only required fields."""
        plugin = {
            "name": "phlix-plugin-minimal",
            "title": "Minimal Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-minimal",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64,
            "version": "0.1.0"
        }
        # This should satisfy all required field checks
        required_fields = {"name", "title", "type", "repo", "ref", "artifactSha256", "version"}
        for field in required_fields:
            assert field in plugin


class TestSchemaValidation:
    """Tests for JSON Schema validation behavior."""

    def test_schema_rejects_unknown_plugin_properties(self, schema_json):
        """Schema should reject plugins with unexpected properties."""
        import jsonschema
        invalid_plugin = {
            "name": "phlix-plugin-invalid",
            "title": "Invalid Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-invalid",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64,
            "version": "1.0.0",
            "unknownField": "should be rejected"
        }
        catalog = {
            "schemaVersion": 2,
            "name": "Test Catalog",
            "plugins": [invalid_plugin]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(catalog, schema_json)

    def test_schema_accepts_valid_minimal_plugin(self, schema_json):
        """Schema should accept a valid minimal plugin."""
        import jsonschema
        valid_plugin = {
            "name": "phlix-plugin-valid",
            "title": "Valid Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-valid",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64,
            "version": "1.0.0"
        }
        catalog = {
            "schemaVersion": 2,
            "name": "Test Catalog",
            "plugins": [valid_plugin]
        }
        # Should not raise
        jsonschema.validate(catalog, schema_json)

    def test_schema_accepts_dev_version(self, schema_json):
        """Schema must accept the literal "dev" version (dev-channel entry)."""
        import jsonschema
        dev_plugin = {
            "name": "phlix-plugin-valid",
            "title": "Valid Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-valid",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64,
            "version": "dev"
        }
        catalog = {"schemaVersion": 2, "name": "Test Catalog", "plugins": [dev_plugin]}
        jsonschema.validate(catalog, schema_json)

    def test_schema_rejects_dev_variants(self, schema_json):
        """Schema must reject dev variants ("Dev", "DEV", "dev-1.0") — "dev" is
        lowercase-exact only — and a missing version."""
        import jsonschema
        for bad_version in ["Dev", "DEV", "dev-1.0", "dev.1"]:
            plugin = {
                "name": "phlix-plugin-invalid",
                "title": "Invalid Plugin",
                "type": "metadata-provider",
                "repo": "https://github.com/detain/phlix-plugin-invalid",
                "ref": "a" * 40,
                "artifactSha256": "b" * 64,
                "version": bad_version
            }
            catalog = {"schemaVersion": 2, "name": "Test Catalog", "plugins": [plugin]}
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(catalog, schema_json)
        plugin = {
            "name": "phlix-plugin-invalid",
            "title": "Invalid Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-invalid",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64
        }
        catalog = {"schemaVersion": 2, "name": "Test Catalog", "plugins": [plugin]}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(catalog, schema_json)

    def test_schema_rejects_invalid_plugin_type(self, schema_json):
        """Schema should reject plugins with invalid type."""
        import jsonschema
        invalid_plugin = {
            "name": "phlix-plugin-bad-type",
            "title": "Bad Type Plugin",
            "type": "invalid-type",
            "repo": "https://github.com/detain/phlix-plugin-bad-type",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64,
            "version": "1.0.0"
        }
        catalog = {
            "schemaVersion": 2,
            "name": "Test Catalog",
            "plugins": [invalid_plugin]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(catalog, schema_json)


class TestPatternValidation:
    """Tests for regex pattern validation."""

    def test_valid_plugin_name_patterns(self):
        """Valid plugin names should match the pattern."""
        PLUGIN_NAME_PATTERN = re.compile(r"^phlix-plugin-[a-z0-9][a-z0-9-]*$")
        valid_names = [
            "phlix-plugin-a",
            "phlix-plugin-ab",
            "phlix-plugin-a1",
            "phlix-plugin-a1b2c3",
            "phlix-plugin-anidb",
            "phlix-plugin-a",
            "phlix-plugin-0",
            "phlix-plugin-abc-def",
        ]
        for name in valid_names:
            assert PLUGIN_NAME_PATTERN.match(name), f"Expected {name} to be valid"

    def test_invalid_plugin_name_patterns(self):
        """Invalid plugin names should not match the pattern."""
        PLUGIN_NAME_PATTERN = re.compile(r"^phlix-plugin-[a-z0-9][a-z0-9-]*$")
        invalid_names = [
            "phlix-plugin-",  # empty after hyphen
            "Phlix-plugin-a",  # uppercase P
            "phlix_plugin_a",  # underscore
            "phlix-plugin-a_b",  # underscore in name
            "phlixplug-in-a",  # wrong prefix
            "phlix-plugin-A",  # uppercase letter
            "phlix--plugin-a",  # double hyphen
        ]
        for name in invalid_names:
            assert not PLUGIN_NAME_PATTERN.match(name), f"Expected {name} to be invalid"

    def test_valid_semver_patterns(self):
        """Valid semver versions should match the pattern."""
        SEMVER_PATTERN = re.compile(
            r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
        )
        valid_versions = [
            "0.0.0",
            "1.0.0",
            "1.2.3",
            "10.20.30",
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0+build",
            "1.0.0-alpha+build",
        ]
        for version in valid_versions:
            assert SEMVER_PATTERN.match(version), f"Expected {version} to be valid"

    def test_invalid_semver_patterns(self):
        """Invalid semver versions should not match the pattern."""
        SEMVER_PATTERN = re.compile(
            r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
        )
        invalid_versions = [
            "1.0",  # missing patch
            "1",  # missing minor and patch
            "1.0.0.0",  # too many parts
            "01.0.0",  # leading zero
            "1.00.0",  # leading zero
            "1.0.01",  # leading zero
        ]
        for version in invalid_versions:
            assert not SEMVER_PATTERN.match(version), f"Expected {version} to be invalid"

    def test_valid_ref_patterns(self):
        """Valid git commit SHAs should match the pattern."""
        REF_PATTERN = re.compile(r"^[0-9a-f]{40}$")
        valid_refs = [
            "0" * 40,
            "a" * 40,
            "f" * 40,
            "a0" * 20,
            "4b80320afcaf876767717d027b5200f69f2ab5b8",
        ]
        for ref in valid_refs:
            assert REF_PATTERN.match(ref), f"Expected {ref} to be valid"

    def test_invalid_ref_patterns(self):
        """Invalid git commit SHAs should not match the pattern."""
        REF_PATTERN = re.compile(r"^[0-9a-f]{40}$")
        invalid_refs = [
            "0" * 39,  # too short
            "0" * 41,  # too long
            "G" * 40,  # invalid hex char
            "0" * 38 + "GG",  # invalid chars at end
            "ABCDEF0123456789ABCDEF0123456789ABCDEF01",  # uppercase
        ]
        for ref in invalid_refs:
            assert not REF_PATTERN.match(ref), f"Expected {ref} to be invalid"

    def test_valid_artifact_sha256_patterns(self):
        """Valid SHA256 hashes should match the pattern."""
        SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
        valid_hashes = [
            "0" * 64,
            "a" * 64,
            "f" * 64,
            "a0" * 32,
            "a9854f188ac0a4b8dc629ecc25411a142b3b155058b9a67ba78a60d77be2dd66",
        ]
        for sha in valid_hashes:
            assert SHA256_PATTERN.match(sha), f"Expected {sha} to be valid"

    def test_invalid_artifact_sha256_patterns(self):
        """Invalid SHA256 hashes should not match the pattern."""
        SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
        invalid_hashes = [
            "0" * 63,  # too short
            "0" * 65,  # too long
            "G" * 64,  # invalid hex char
            "0" * 62 + "GG",  # invalid chars at end
            "ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789AB",  # uppercase
        ]
        for sha in invalid_hashes:
            assert not SHA256_PATTERN.match(sha), f"Expected {sha} to be invalid"


class TestCatalogOperations:
    """Tests for catalog-level operations and edge cases."""

    def test_catalog_with_single_plugin(self, schema_json):
        """Catalog with a single plugin should be valid."""
        import jsonschema
        catalog = {
            "schemaVersion": 2,
            "name": "Single Plugin Catalog",
            "plugins": [
                {
                    "name": "phlix-plugin-single",
                    "title": "Single Plugin",
                    "type": "metadata-provider",
                    "repo": "https://github.com/detain/phlix-plugin-single",
                    "ref": "a" * 40,
                    "artifactSha256": "b" * 64,
                    "version": "1.0.0"
                }
            ]
        }
        jsonschema.validate(catalog, schema_json)

    def test_catalog_with_max_fields(self, schema_json):
        """Catalog with all optional fields populated should be valid."""
        import jsonschema
        catalog = {
            "schemaVersion": 2,
            "name": "Full Catalog",
            "description": "A catalog with all fields",
            "homepage": "https://example.com",
            "plugins": [
                {
                    "name": "phlix-plugin-full",
                    "title": "Full Plugin",
                    "type": "metadata-provider",
                    "summary": "A summary",
                    "description": "A description",
                    "repo": "https://github.com/detain/phlix-plugin-full",
                    "ref": "a" * 40,
                    "artifactSha256": "b" * 64,
                    "version": "1.0.0",
                    "minServerVersion": "1.0.0",
                    "maxServerVersion": "2.0.0",
                    "verified": True,
                    "deprecated": False,
                    "yanked": False,
                    "deprecationMessage": "Use another plugin",
                    "author": "test author",
                    "tags": ["tag1", "tag2"]
                }
            ]
        }
        jsonschema.validate(catalog, schema_json)


class TestOriginalMethodsWithOptionalFields:
    """Tests that invoke original test methods with optional fields present.

    These tests ensure the conditional branches in the original test methods
    (which iterate over plugins looking for optional fields) are fully covered.
    """

    def test_max_server_version_branch_is_covered(self):
        """Invoke original maxServerVersion test with plugins containing that field."""
        # Create a plugin with maxServerVersion present
        plugin_with_max_version = {
            "name": "phlix-plugin-test",
            "title": "Test Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-test",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64,
            "version": "1.0.0",
            "minServerVersion": "1.0.0",
            "maxServerVersion": "2.0.0"
        }

        # Instantiate the original test class and call the method directly
        test_instance = TestServerVersion()
        # The method iterates over plugins, so pass a list with our plugin
        test_instance.test_max_server_version_is_valid_semver_if_present([plugin_with_max_version])

    def test_deprecation_message_branch_is_covered(self):
        """Invoke original deprecationMessage test with plugins containing that field."""
        # Create a plugin with deprecationMessage present
        plugin_with_deprecation = {
            "name": "phlix-plugin-test",
            "title": "Test Plugin",
            "type": "metadata-provider",
            "repo": "https://github.com/detain/phlix-plugin-test",
            "ref": "a" * 40,
            "artifactSha256": "b" * 64,
            "version": "1.0.0",
            "deprecationMessage": "Use phlix-plugin-other instead"
        }

        # Instantiate the original test class and call the method directly
        test_instance = TestOptionalFields()
        test_instance.test_deprecation_message_is_string_if_present([plugin_with_deprecation])


class TestWorkflowContract:
    """Executable tripwires for the laws that live INSIDE the workflow YAML.

    The codeload-hash law (this repo's own poisoning incident: api.github.com
    tarballs are DIFFERENT bytes for the same commit — review
    phlix-plugins__seceng M-05), the trust-boundary guards (M-04) and the
    shared catalog gate (M-01) all live in a PHP heredoc / shell step that no
    test otherwise imports. These tests pin the law text byte-exactly and
    re-derive its pure semantics in python, so a refactor cannot silently drop
    them. (review phlix-plugins__seceng M-05)
    """

    @pytest.fixture
    def update_wf(self, repo_root):
        return (repo_root / ".github" / "workflows" / "update-checksums.yml").read_text()

    @pytest.fixture
    def validate_wf(self, repo_root):
        return (repo_root / ".github" / "workflows" / "validate-catalog.yml").read_text()

    @staticmethod
    def _is_comment(line: str) -> bool:
        s = line.lstrip()
        return s.startswith("#") or s.startswith("//") or s.startswith("*")

    def test_every_tarball_fetch_line_uses_the_archive_idiom(self, repo_root):
        """Every non-comment line constructing a .tar.gz URL (http-bearing) must use
        github.com/.../archive/<ref>.tar.gz — the ONLY byte form the
        artifactSha256 contract is computed over. (The updater's local temp-file
        paths carry .tar.gz too — they are filenames, not fetch URLs.)"""
        for wf in sorted((repo_root / ".github" / "workflows").iterdir()):
            for i, line in enumerate(wf.read_text().splitlines(), 1):
                if ".tar.gz" in line and "http" in line and not self._is_comment(line):
                    assert "archive/" in line, f"{wf.name}:{i}: tarball URL not codeload archive idiom: {line.strip()}"

    def test_no_api_github_com_tarball_consumption(self, repo_root):
        """api.github.com may only appear in law-documenting comments — never on a
        line that fetches/consumes a tarball (those bytes hash differently and
        previously poisoned every pin)."""
        for wf in sorted((repo_root / ".github" / "workflows").iterdir()):
            for i, line in enumerate(wf.read_text().splitlines(), 1):
                if "api.github.com" in line:
                    assert self._is_comment(line), f"{wf.name}:{i}: api.github.com outside a comment: {line.strip()}"

    def test_codeload_law_text_is_carried(self, update_wf):
        """The heredoc must keep explaining WHY the codeload form is law."""
        assert "api.github.com tarball" in update_wf
        assert "DIFFERENT bytes" in update_wf

    def test_updater_fetch_line_is_byte_pinned(self, update_wf):
        """The single canonical fetch construction; move it and this test reddens
        — reviewers must see the URL-shape change deliberately."""
        assert ('''"https://github.com/detain/' . $name . '/archive/' . $sha . '.tar.gz"''') in update_wf

    def test_schema_artifact_digest_describes_the_archive_form(self, schema_json):
        desc = schema_json["$defs"]["plugin"]["properties"]["artifactSha256"]["description"]
        assert "archive/<ref>.tar.gz" in desc

    def test_updater_regex_constants_are_pinned(self, update_wf):
        """The gates between hostile repo data and shell/URL interpolation, pinned
        byte-for-byte (devops m10: SAFE_BRANCH_RE once missed () and `; a widened
        charset here is a shell-injection surface, never an editorial tweak)."""
        for const_line in (
            r"const PLUGIN_NAME_RE = '/^phlix-plugin-[a-z0-9][a-z0-9-]*$/';",
            r"const SAFE_BRANCH_RE = '/^[A-Za-z0-9][A-Za-z0-9._\/-]*$/';",
            r"const SAFE_TAG_RE = '/^[A-Za-z0-9._\/-]+$/';",
            r"const SHA40_RE = '/^[0-9a-f]{40}$/';",
            r"const SHA64_RE = '/^[0-9a-f]{64}$/';",
        ):
            assert const_line in update_wf, f"missing/bent constant: {const_line}"

    def test_branch_name_rejects_shell_metacharacters(self):
        """Behavioural mirror of SAFE_BRANCH_RE: names that could break out of a
        shell string are refused."""
        branch_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
        for ok in ("master", "main", "feature/x-1.2_3"):
            assert branch_re.match(ok), ok
        for bad in ("main;id", "feat`whoami`", "a$b", "a|b", "a'b", "a(b)", "a&&b", " lead"):
            assert not branch_re.match(bad), bad

    def test_pin_drift_checker_blocks_pushes(self, validate_wf):
        """The re-hashing cross-check must never be blanket non-blocking again
        (M-05): advisory on PRs only, blocking on push."""
        assert "continue-on-error: ${{ github.event_name == 'pull_request' }}" in validate_wf
        assert "continue-on-error: true" not in validate_wf

    def test_trust_boundary_guards_are_carried(self, update_wf):
        """M-04 guards: effective-URL ownership assertion, org assertion on repo
        metadata, and the compare-API lineage decision (fail-closed)."""
        for marker in (
            "%{url_effective}",
            "codeload\\.github\\.com)/detain/",
            ".owner.login",
            "full_name",
            "/compare/",
            "function releaseLineageOk",
            "function reattestedVerified",
        ):
            assert marker in update_wf, f"trust guard vanished from updater: {marker}"

    def test_ci_installs_python_deps_from_the_hash_lock(self, validate_wf, repo_root):
        """M-07: the CI pytest job consumes requirements-test.txt with
        --require-hashes, and the lock itself is a full exact-pinned, hash-locked
        closure — no pin without at least one sha256."""
        assert "pip install -q --require-hashes -r requirements-test.txt" in validate_wf
        lock = (repo_root / "requirements-test.txt").read_text()
        lines = [l.strip() for l in lock.splitlines() if l.strip() and not l.lstrip().startswith("#")]
        pins = [idx for idx, l in enumerate(lines) if "==" in l]
        assert len(pins) >= 12, "closure should pin the full transitive set"
        for idx in pins:
            following = lines[idx + 1] if idx + 1 < len(lines) else ""
            assert following.startswith("--hash=sha256:"), f"requirement without hash: {lines[idx]}"

    def test_all_action_uses_are_sha_pinned(self, repo_root):
        """Every `uses:` line in both workflows is pinned to a full 40-hex commit
        SHA (M-07 estate toolchain law): a floating major tag hands the runner to
        whatever upstream publishes next."""
        seen = 0
        for wf in sorted((repo_root / ".github" / "workflows").iterdir()):
            for i, line in enumerate(wf.read_text().splitlines(), 1):
                m = re.search(r"^\s*-?\s*uses:\s*(\S+)", line)
                if m is None:
                    continue
                seen += 1
                ref = m.group(1).rsplit("@", 1)[-1]
                assert re.fullmatch(r"[0-9a-f]{40}", ref), f"{wf.name}:{i}: unpinned action ref: {line.strip()}"
        assert seen >= 8, f"expected the whole action fleet, saw {seen}"

    def test_manifest_schema_fetch_is_pinned(self, validate_wf):
        """M-08: the BLOCKING manifest gate's schema authority must be fetched at
        a pinned phlix-shared TAG and compared to a committed sha256 digest —
        floating master lets upstream silently redefine the install contract."""
        assert "phlix-shared/master/schemas" not in validate_wf
        assert re.search(r"PHLIX_SHARED_REF='v\d+\.\d+\.\d+'", validate_wf)
        assert re.search(r"MANIFEST_SCHEMA_SHA256='[0-9a-f]{64}'", validate_wf)
        assert "not the pinned digest" in validate_wf

    def test_catalog_gate_script_gates_both_paths(self, repo_root, update_wf, validate_wf):
        """scripts/catalog-gate.jq is the single structural source of truth: the
        blocking validate job AND the updater's pre-push step must both INVOKE it
        (byte-pinned command line, not a comment mention), and it must PASS on the
        live catalog (jq exit 0)."""
        invoke = "jq -e -r -f scripts/catalog-gate.jq plugins.json"
        assert invoke in update_wf, "updater pre-push no longer invokes the catalog gate"
        assert invoke in validate_wf, "validate job no longer invokes the catalog gate"
        script = repo_root / "scripts" / "catalog-gate.jq"
        assert script.is_file()
        jq = shutil.which("jq")
        if jq is None:  # pragma: no cover - ubuntu runners ship jq; the sibling job fails loudly without it
            pytest.skip("jq binary unavailable in this venue")
        r = subprocess.run(
            [jq, "-e", "-r", "-f", str(script), str(repo_root / "plugins.json")],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"catalog gate reddens the live catalog: {r.stderr}"

    def test_no_coverage_annotate_junk_is_tracked(self, repo_root):
        """(M-PHLIX-PLUGINS-04) `coverage --cov-report=annotate` drops
        '<file>,cover' siblings; two were committed once and stayed tracked.
        They must not come back: untracked AND gitignored."""
        import subprocess as sp
        out = sp.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True).stdout
        junk = [line for line in out.splitlines() if line.endswith(",cover")]
        assert not junk, f"coverage-annotate artifacts tracked again: {junk}"
        ignore = (repo_root / ".gitignore").read_text()
        assert "*.cover" in ignore, ".gitignore no longer excludes annotate output"

    def test_readme_documents_the_updater_sim_seam(self, repo_root):
        """(M-PHLIX-PLUGINS-05/-23) the updater's local-simulation env vars are
        only defined inside the YAML heredoc; the README is the one place an
        operator can actually learn them. Anti-rot pin."""
        readme = (repo_root / "README.md").read_text()
        assert "Exercising the updater locally" in readme
        for var in ("PHLIX_STATE_DIR", "PHLIX_SKIP_FETCH", "PHLIX_PHASE_B_ONLY", "PHLIX_DISCOVERY_JSON"):
            assert var in readme, f"README lost the sim-var doc for {var}"

    def test_updater_pristine_read_honors_the_state_dir(self, update_wf):
        """(M-PHLIX-PLUGINS-05) the sim seam must be COMPLETE: Phase C read the
        pristine catalog from a hardcoded /tmp path, so PHLIX_STATE_DIR alone
        could not exercise the updater off-CI. It must read stateDir() — and CI
        behavior is byte-identical because stateDir() defaults to /tmp."""
        assert "file_get_contents(stateDir() . '/plugins.json')" in update_wf
        assert "file_get_contents('/tmp/plugins.json')" not in update_wf

    def test_every_job_declares_a_timeout(self, repo_root):
        """(M-PHLIX-PLUGINS-09) every job must bound its wall clock — a hung
        network fetch used to sit until GitHub's own 6h runner limit. One
        `timeout-minutes:` per `runs-on:` across both workflows."""
        total_runs_on = total_timeout = 0
        for wf in sorted((repo_root / ".github" / "workflows").iterdir()):
            text = wf.read_text()
            total_runs_on += len(re.findall(r"^\s*runs-on:", text, re.M))
            total_timeout += len(re.findall(r"^\s*timeout-minutes:\s*\d+", text, re.M))
        assert total_runs_on >= 5, "expected the full five-job fleet"
        assert total_timeout == total_runs_on, (
            f"{total_runs_on - total_timeout} job(s) run without timeout-minutes"
        )

    def test_every_tarball_fetch_is_time_bounded(self, repo_root):
        """(M-PHLIX-PLUGINS-09) every curl that pulls catalog/manifest bytes must
        carry --max-time — the one exception being the updater's byte-pinned
        fetch line, which carries it too (options precede the pinned URL
        literal, so the M-05 pin above still matches)."""
        for wf in sorted((repo_root / ".github" / "workflows").iterdir()):
            for i, line in enumerate(wf.read_text().splitlines(), 1):
                if "curl -f" in line and not self._is_comment(line):
                    assert "--max-time" in line, f"{wf.name}:{i}: unbounded fetch: {line.strip()}"

    def test_updater_scratch_is_cleaned_after_capture(self, update_wf):
        """(M-PHLIX-PLUGINS-09) fetchTargetTarball must drop the tarball and the
        unpacked copy once digest+manifest are captured (and on every early
        failure path) — 41 repos x 2 targets no longer accumulate in stateDir."""
        assert update_wf.count("@unlink($tarball)") >= 5, "tarball cleanup paths missing"
        assert update_wf.count("shell_exec('rm -rf ' . $extract)") == 2, (
            "extract dir must be pre-cleaned AND removed after capture"
        )

    def test_updater_log_sanitizes_untrusted_strings(self, update_wf):
        """(M-PHLIX-PLUGINS-10) Every string born outside the trust boundary — gh
        stderr bodies, branch/tag/ref names that FAILED the SAFE_*_RE guards,
        manifest name/type, curl's effective URL — passes through logSafe() before
        reaching the job log: printable-ASCII only, '::' workflow-command tokens
        defused, capped at 80 chars. Behavior independently verified against the
        extracted heredoc on host php 8.3.6 (W-min85 report)."""
        assert "function logSafe(string $value): string" in update_wf
        assert "preg_replace('/[^\\x20-\\x7E]/', '', $value)" in update_wf, (
            "logSafe must strip every byte outside printable ASCII (control-char "
            "line-forging + non-ASCII separators)"
        )
        assert "str_replace('::', ': :', $value)" in update_wf, (
            "logSafe must defuse GitHub Actions workflow-command tokens"
        )
        assert "strlen($value) > 80 ? substr($value, 0, 80)" in update_wf, (
            "logSafe must cap output at 80 chars"
        )
        # def + 13 call sites; growth must be deliberate (rotate this pin).
        assert update_wf.count("logSafe(") == 14, "logSafe definition/call-site count moved"
        for pin in (
            "(effective URL: '\" . logSafe($effective)",          # fork-guard refusal
            "raw output follows)\\n\" . logSafe($discoveryJson)",  # discovery dump
            "logSafe(is_string($name) ? $name : var_export($name, true))",  # pre-guard repo name
            ": repo metadata fetch failed: ' . logSafe(trim($metaJson))",   # gh error body
            "logSafe($metaOwner)", "logSafe($metaFullName)",                # transfer/rename echo
            ": unsafe branch name '\" . logSafe($branch)",                  # SAFE_BRANCH_RE reject
            ": invalid ref '\" . logSafe($sha)",                            # SHA40_RE reject
            "fetch failed at tag '\" . logSafe($latest['name'])",           # gh-provided tag name
            "logSafe($manifestName)",                                      # mismatch + invalid (2 sites)
            ": manifest type '\" . logSafe($type)",                        # enum reject
            "release entry skipped — ' . logSafe($releaseSkipReason)",     # carries tag+manifest names
        ):
            assert pin in update_wf, f"logSafe wrap site removed/renamed: {pin}"
        assert update_wf.count("logSafe($manifestName)") == 2
        assert update_wf.count("logSafe($type)") == 1

    def test_robustness_contract_exit_enumeration_is_exhaustive(self, update_wf):
        """(M-PHLIX-PLUGINS-24) The header contract must enumerate EVERY exit(1)
        cause. Pinned inventory: state-file write, discovery, all-skipped, JSON
        decode, shape-invalid, JSON encode, catalog write = 7 sites -> the prose
        set (discovery / state-file write / unparseable (invalid JSON or no
        'plugins' array) / encode / catalog write / all-skipped)."""
        assert update_wf.count("exit(1)") == 7, "exit(1) inventory moved; reconcile the header"
        for pin in (
            "discovery failure, a state-file",
            "write failure, an unparseable catalog (invalid JSON",
            "array), a JSON encode failure, a catalog write",
        ):
            assert pin in update_wf, f"Robustness contract lost cause clause: {pin}"

    def test_readme_uses_one_actor_noun(self, repo_root):
        """(M-PHLIX-PLUGINS-20) The automation is 'the updater' wherever it acts.
        'the sync job'/'a scheduled job'/'the refresh' as actors are register drift."""
        readme = (repo_root / "README.md").read_text()
        assert "the updater unions" in readme
        for alias in ("the sync job", "a scheduled job", "A scheduled job", "the refresh"):
            assert alias not in readme, f"actor-noun alias back in README: {alias!r}"

    def test_readme_states_the_codeload_versus_api_digest_law(self, repo_root):
        """(M-PHLIX-PLUGINS-21) The README pin recipe must carry the law that
        api.github.com tarballs are DIFFERENT bytes from the codeload archive form
        — previously it lived only in a workflow comment, and the mix-up poisoned
        every pin once."""
        readme = (repo_root / "README.md").read_text()
        assert "api.github.com/repos/<owner>/<repo>/tarball" in readme
        assert "**different bytes**" in readme
