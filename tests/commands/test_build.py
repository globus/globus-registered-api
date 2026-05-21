# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime

import pytest

import globus_registered_api.manifest as manifest_module
from globus_registered_api.config import CoreConfig
from globus_registered_api.config import GRAConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.openapi.loader import load_openapi_spec


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
        subscription_id="a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    )
    targets = [
        TargetConfig(
            path="/example",
            method="GET",
            alias="get-example",
            description="Get example resource",
        ),
        TargetConfig(
            path="/example",
            method="POST",
            alias="create-example",
            description="Create example resource",
        ),
    ]
    return GRAConfig(core=core, targets=targets, roles=[])


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
            description="Get example resource",
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


def test_manifest_route_parameters_are_inherited(gra, config, manifest_path, spec_path):
    """Verify that shared route parameters are inherited.

    The `with_refs.json` file contains content similar to this:

        components:
            parameters:
                Id: <definition of 'id' parameter, with a ref to 'schemas/Id', below>
            schemas:
                Id: <definition of 'id' schema>

        /items/{id}:
            parameters:
                - <ref to 'parameters/Id', above>

            put:
                # no parameters defined

    This test confirms that the shared 'id' parameter is inherited by the 'put' method,
    and that the 'Id' schema is included.
    """

    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("put", "/items/{id}")
    target_config = TargetConfig(
        path=target.path,
        method=target.method,
        alias="update-item",
        description="description",
        security=TargetConfig.Security(globus_auth_scope="scope"),
    )
    config.core.specification = spec
    config.targets = [target_config]
    config.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    target = manifest["registered-apis"]["update-item"]["target"]
    # "parameters" shouldn't exist because no refs into it should be needed;
    # they should have been expanded in-place.
    assert "parameters" not in target["components"]

    # Only one inherited parameter is expected.
    parameters = target["specification"]["parameters"]
    assert len(parameters) == 1
    assert parameters[0]["description"] == "Defined in components"

    # Expect a reference to `#/components/schemas/Id` to be valid.
    assert parameters[0]["schema"]["$ref"] == "#/components/schemas/Id"
    assert "Id" in target["components"]["schemas"]


def test_manifest_method_parameters_override_route_parameters(
    gra, config, manifest_path, spec_path
):
    """Verify that method-specific parameters override route parameters.

    The `with_refs.json` file contains content similar to this:

        components:
            parameters:
                Id: <definition of 'id' parameter, with a ref to 'schemas/Id', below>
            schemas:
                Id: <definition of 'id' schema>


        /items/{id}:
            parameters:
                - <ref to 'parameters/Id', above>

            get:
                parameters:
                    - <redefinition of 'id' parameter, with explicit schema>

    This test confirms that the redefined 'id' parameter takes precedence,
    and that the 'Id' schema is dropped because it's not needed.
    """

    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("get", "/items/{id}")
    target_config = TargetConfig(
        path=target.path,
        method=target.method,
        alias="get-item",
        description="description",
        security=TargetConfig.Security(globus_auth_scope="scope"),
    )
    config.core.specification = spec
    config.targets = [target_config]
    config.commit()

    # Act
    result = gra(["build"])

    # Assert
    assert result.exit_code == 0
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    target = manifest["registered-apis"]["get-item"]["target"]
    # "parameters" shouldn't exist because no refs into it should be needed;
    # they should have been deduplicated and removed.
    assert "parameters" not in target["components"]

    # Only one parameter is expected due to deduplication.
    parameters = target["specification"]["parameters"]
    assert len(parameters) == 1
    assert parameters[0]["description"] == "Defined in the method"

    # The method-specific `id` parameter should have no `$ref`.
    assert "$ref" not in parameters[0]["schema"]
    assert "Id" not in target["components"]["schemas"]


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
            description="Create example resource",
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
        subscription_id="a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    )
    targets = [
        TargetConfig(
            path="/example",
            method="GET",
            alias="get-example",
            description="Get example resource",
        ),
    ]
    config = GRAConfig(core=core, targets=targets, roles=[])
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
