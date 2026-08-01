"""
Pytest configuration and fixtures for phlix-plugins tests.
"""
import json
import pytest
from pathlib import Path


@pytest.fixture
def repo_root():
    """Return the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def plugins_json(repo_root):
    """Load and return the plugins.json catalog."""
    with open(repo_root / "plugins.json") as f:
        return json.load(f)


@pytest.fixture
def schema_json(repo_root):
    """Load and return the plugins.schema.json."""
    with open(repo_root / "plugins.schema.json") as f:
        return json.load(f)


@pytest.fixture
def catalog(plugins_json):
    """Return just the catalog object."""
    return plugins_json


@pytest.fixture
def plugins(plugins_json):
    """Return the plugins array from the catalog."""
    return plugins_json["plugins"]
