# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime

import pytest

import globus_registered_api.manifest as manifest_module
from globus_registered_api.config import CoreConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import TargetConfig


@pytest.fixture(autouse=True)
def manifest_path(monkeypatch, tmp_path):
    new_path = tmp_path / ".globus_registered_api" / "manifest.json"
    monkeypatch.setattr(manifest_module, "_MANIFEST_PATH", new_path)
    yield new_path


@pytest.fixture
def config_with_targets(openapi_schema):
    core = CoreConfig(
        base_url="https://api.example.com",
        specification=openapi_schema,
    )
    targets = [
        TargetConfig(
            path="/example",
            method="GET",
            alias="get-example",
            scope_strings=["example:read"],
        ),
        TargetConfig(
            path="/example",
            method="POST",
            alias="create-example",
            scope_strings=["example:write"],
        ),
    ]
    return RegisteredAPIConfig(core=core, targets=targets, roles=[])


def test_build_command_exists(gra):
    # Act
    result = gra(["build", "--help"])

    # Assert
    assert result.exit_code == 0
    assert "Build a manifest file for your registered APIs" in result.output


def test_error_missing_config(gra):
    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code != 0
    assert "Missing repository config file" in result.output


def test_build_generates_manifest_with_single_target(gra, config, manifest_path):
    # Arrange
    config.targets.append(
        TargetConfig(
            path="/example",
            method="GET",
            alias="get-example",
            scope_strings=[],
        )
    )
    config.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "registered-apis" in manifest
    assert "get-example" in manifest["registered-apis"]


def test_build_generates_manifest_with_multiple_targets(
    gra, config_with_targets, manifest_path
):
    # Arrange
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["registered-apis"]) == 2
    assert "get-example" in manifest["registered-apis"]
    assert "create-example" in manifest["registered-apis"]


def test_manifest_structure(gra, config_with_targets, manifest_path):
    # Arrange
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Assert - top-level fields
    assert "_comment" in manifest
    assert "build_timestamp" in manifest
    assert "registered-apis" in manifest
    # Assert - comment structure
    assert isinstance(manifest["_comment"], list)
    assert all(isinstance(line, str) for line in manifest["_comment"])
    # Assert - comment content
    comment_text = " ".join(manifest["_comment"])
    assert "AUTO-GENERATED FILE" in comment_text
    assert "DO NOT MODIFY DIRECTLY" in comment_text
    # Assert - timestamp format
    timestamp = datetime.fromisoformat(manifest["build_timestamp"])
    assert timestamp.tzinfo is not None


def test_manifest_keys_alphabetically_sorted(gra, config_with_targets, manifest_path):
    # Arrange
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    top_keys = list(manifest.keys())
    assert top_keys == sorted(top_keys)
    api_keys = list(manifest["registered-apis"].keys())
    assert api_keys == sorted(api_keys)


def test_target_specification_structure(gra, config_with_targets, manifest_path):
    # Arrange
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    apis = manifest["registered-apis"]
    # Assert - expected aliases present
    assert "get-example" in apis
    assert "create-example" in apis
    # Assert - target specification structure
    for _alias, entry in apis.items():
        assert "target" in entry
        target_spec = entry["target"]
        assert "type" in target_spec
        assert target_spec["type"] == "openapi"
        assert "destination" in target_spec
        assert "specification" in target_spec
    # Assert - destination values
    get_dest = apis["get-example"]["target"]["destination"]
    assert get_dest["method"] == "get"
    assert get_dest["url"] == "https://api.example.com/example"
    post_dest = apis["create-example"]["target"]["destination"]
    assert post_dest["method"] == "post"
    assert post_dest["url"] == "https://api.example.com/example"
    # Assert - specification structure
    for _alias, entry in apis.items():
        spec = entry["target"]["specification"]
        assert "summary" in spec
        assert isinstance(spec["summary"], str)


def test_manifest_overwrites_existing_file(gra, config_with_targets, manifest_path):
    # Arrange
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["registered-apis"]) == 2
    assert "get-example" in manifest["registered-apis"]
    assert "create-example" in manifest["registered-apis"]

    # Arrange
    config_with_targets.targets.pop()
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["registered-apis"]) == 1
    assert "get-example" in manifest["registered-apis"]
    assert "create-example" not in manifest["registered-apis"]

    # Arrange
    config_with_targets.targets.append(
        TargetConfig(
            path="/example",
            method="POST",
            alias="create-example",
            scope_strings=["example:write"],
        )
    )
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["registered-apis"]) == 2
    assert "get-example" in manifest["registered-apis"]
    assert "create-example" in manifest["registered-apis"]


@pytest.mark.parametrize(
    "base_url,expected_url",
    [
        pytest.param(
            "https://api.example.com",
            "https://api.example.com/example",
            id="base_url_without_trailing_slash",
        ),
        pytest.param(
            "https://api.example.com/",
            "https://api.example.com/example",
            id="base_url_with_trailing_slash",
        ),
        pytest.param(
            "https://api.example.com/v2/",
            "https://api.example.com/v2/example",
            id="base_url_with_path_and_trailing_slash",
        ),
        pytest.param(
            "https://api.example.com/v2",
            "https://api.example.com/v2/example",
            id="base_url_with_path_without_trailing_slash",
        ),
    ],
)
def test_build_destination_url_slash_handling(
    gra, openapi_schema, manifest_path, base_url, expected_url
):
    # Arrange
    core = CoreConfig(
        base_url=base_url,
        specification=openapi_schema,
    )
    targets = [
        TargetConfig(
            path="/example",
            method="GET",
            alias="get-example",
            scope_strings=["example:read"],
        ),
    ]
    config = RegisteredAPIConfig(core=core, targets=targets, roles=[])
    config.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dest_url = manifest["registered-apis"]["get-example"]["target"]["destination"][
        "url"
    ]
    assert dest_url == expected_url


def test_manifest_directory_creation(gra, config_with_targets, tmp_path, monkeypatch):
    # Arrange
    new_manifest_path = tmp_path / "new_dir" / "manifest.json"
    monkeypatch.setattr(manifest_module, "_MANIFEST_PATH", new_manifest_path)
    config_with_targets.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    assert new_manifest_path.exists()
    assert new_manifest_path.parent.exists()
