"""Prevent publishing tags whose backend, bundle metadata or notes disagree."""

import json
import shutil
from pathlib import Path

import pytest

from scripts.release_metadata import validate_release


@pytest.fixture
def release_tree(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for name in (
        "custom_components/hano/manifest.json",
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "package-lock.json",
        "releases/0.1.1.md",
    ):
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, destination)
    return tmp_path


def test_stable_metadata_is_consistent(release_tree):
    assert validate_release(release_tree, "v0.1.1") == {
        "version": "0.1.1",
        "prerelease": "false",
    }


@pytest.mark.parametrize("tag", ["main", "0.1.0b2", "v0.1.0-beta.2", "v0.1.0b02"])
def test_noncanonical_tags_are_rejected(release_tree, tag):
    with pytest.raises(ValueError):
        validate_release(release_tree, tag)


def test_stale_frontend_cannot_be_published(release_tree):
    package = release_tree / "package.json"
    data = json.loads(package.read_text())
    data["version"] = "0.1.0-beta.2"
    package.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Frontend"):
        validate_release(release_tree, "v0.1.1")


def test_empty_release_notes_are_rejected(release_tree):
    (release_tree / "releases/0.1.1.md").write_text("")
    with pytest.raises(ValueError, match="notes"):
        validate_release(release_tree, "v0.1.1")
