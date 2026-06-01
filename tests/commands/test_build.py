# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json

import pytest

import globus_registered_api.manifest as manifest_module
from globus_registered_api.config import TargetConfig
from globus_registered_api.manifest import GRAManifest


@pytest.fixture
def config_with_targets(config, openapi_schema):
    config.targets = {
        "get-example": TargetConfig(
            path="/example",
            method="GET",
            description="Get example resource",
        ),
        "create-example": TargetConfig(
            path="/example",
            method="POST",
            description="Create example resource",
        ),
    }
    return config


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
    assert "Error: Missing config file" in result.output


def test_build_generates_manifest_with_single_target(config, gra):
    # Arrange
    config.targets["get-example"] = TargetConfig(
        path="/example",
        method="GET",
        description="Get example resource",
    )
    config.commit()

    # Act
    gra(["build"], catch_exceptions=False)

    # Assert
    assert "get-example" in GRAManifest.load().registered_apis["production"]


def test_build_generates_manifest_with_multiple_targets(
    config_with_targets,
    gra,
):
    # Arrange
    config_with_targets.commit()

    # Act
    gra(["build"], catch_exceptions=False)

    # Assert
    manifest = GRAManifest.load()
    assert "get-example" in manifest.registered_apis["production"]
    assert "create-example" in manifest.registered_apis["production"]


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
    api_keys = list(manifest["registered_apis"]["production"].keys())
    assert api_keys == sorted(api_keys)


def test_manifest_route_parameters_are_inherited(gra, config, spec_path):
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
    config.stages["production"].specification = str(spec_path("with_refs.json"))
    config.targets = {
        "update-item": TargetConfig(
            path="/items/{id}",
            method="PUT",
            description="description",
            security=TargetConfig.Security(globus_auth_scope="scope"),
        )
    }
    config.commit()

    # Act
    result = gra(["build"], catch_exceptions=False)

    # Assert
    assert result.exit_code == 0
    registered_apis = GRAManifest.load().registered_apis["production"]
    target = registered_apis["update-item"].target.to_dict()

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


def test_manifest_method_parameters_override_route_parameters(gra, config, spec_path):
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
    config.stages["production"].specification = str(spec_path("with_refs.json"))
    config.targets = {
        "get-item": TargetConfig(
            path="/items/{id}",
            method="GET",
            description="description",
            security=TargetConfig.Security(globus_auth_scope="scope"),
        )
    }
    config.commit()

    # Act
    result = gra(["build"], catch_exceptions=False)

    # Assert
    assert result.exit_code == 0

    registered_apis = GRAManifest.load().registered_apis["production"]
    target = registered_apis["get-item"].target.to_dict()
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
    apis = manifest["registered_apis"]["production"]
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


def test_manifest_overwrites_existing_file(gra, config_with_targets):
    # Arrange
    config_with_targets.commit()

    # Act
    gra(["build"], catch_exceptions=False)

    # Assert
    registered_apis = GRAManifest.load().registered_apis["production"]
    assert registered_apis.keys() == {"get-example", "create-example"}

    # Arrange
    del config_with_targets.targets["create-example"]
    config_with_targets.commit()

    # Act
    gra(["build"], catch_exceptions=False)

    # Assert
    registered_apis = GRAManifest.load().registered_apis["production"]
    assert registered_apis.keys() == {"get-example"}

    # Arrange
    config_with_targets.targets["create-example"] = TargetConfig(
        path="/example",
        method="POST",
        description="Create example resource",
    )
    config_with_targets.commit()

    # Act
    gra(["build"], catch_exceptions=False)

    # Assert
    registered_apis = GRAManifest.load().registered_apis["production"]
    assert registered_apis.keys() == {"get-example", "create-example"}


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
    gra, config_with_targets, base_url, expected_url
):
    # Arrange
    config_with_targets.stages["production"].base_url = base_url
    config_with_targets.commit()

    # Act
    gra(["build"], catch_exceptions=False)

    # Assert
    registered_apis = GRAManifest.load().registered_apis["production"]
    dest_url = registered_apis["get-example"].target.destination["url"]
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
