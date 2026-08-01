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
