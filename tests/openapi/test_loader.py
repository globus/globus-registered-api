# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import openapi_pydantic as oa
import pytest

from globus_registered_api.openapi.loader import OpenAPILoadError
from globus_registered_api.openapi.loader import load_openapi_spec


def test_load_openapi_spec_from_json_file_returns_openapi_object(spec_path):
    # Act
    result = load_openapi_spec(spec_path("minimal.json"))

    # Assert
    assert isinstance(result, oa.OpenAPI)
    assert result.info.title == "Minimal API"
    assert result.info.version == "1.0.0"
    assert result.openapi == "3.1.0"


def test_load_openapi_spec_from_yaml_file_returns_openapi_object(spec_path):
    # Act
    result = load_openapi_spec(spec_path("minimal.yaml"))

    # Assert
    assert isinstance(result, oa.OpenAPI)
    assert result.info.title == "Minimal API"
    assert result.info.version == "1.0.0"


def test_load_openapi_spec_with_paths_returns_parsed_paths(spec_path):
    # Act
    result = load_openapi_spec(spec_path("minimal.json"))

    # Assert
    assert result.paths is not None
    assert "/items" in result.paths
    path_item = result.paths["/items"]
    assert path_item.get is not None
    assert path_item.get.summary == "List items"


def test_load_openapi_spec_with_components_returns_parsed_components(spec_path):
    # Act
    result = load_openapi_spec(spec_path("with_refs.json"))

    # Assert
    assert result.components is not None
    assert result.components.schemas is not None
    assert "Item" in result.components.schemas
    assert "Error" in result.components.schemas


def test_load_openapi_spec_with_nonexistent_file_raises_error(spec_path):
    # Act & Assert
    with pytest.raises(OpenAPILoadError, match="^Failed to read file:"):
        load_openapi_spec(spec_path("nonexistent.json"))


def test_load_openapi_spec_with_invalid_json_raises_error(temp_spec_file):
    # Arrange
    path = temp_spec_file("invalid.json", "{invalid json content")

    # Act & Assert
    msg = "^Failed to parse OpenAPI content as JSON or YAML$"
    with pytest.raises(OpenAPILoadError, match=msg):
        load_openapi_spec(path)


def test_load_openapi_spec_with_invalid_yaml_raises_error(temp_spec_file):
    # Arrange
    path = temp_spec_file("invalid.yaml", "invalid: yaml: content: [")

    # Act & Assert
    msg = "^Failed to parse OpenAPI content as JSON or YAML$"
    with pytest.raises(OpenAPILoadError, match=msg):
        load_openapi_spec(path)


def test_load_openapi_spec_with_invalid_openapi_structure_raises_error(temp_spec_file):
    # Arrange
    path = temp_spec_file("invalid_structure.json", '{"not": "a valid openapi spec"}')

    # Act & Assert
    with pytest.raises(OpenAPILoadError, match="^Malformed OpenAPI specification"):
        load_openapi_spec(path)


def test_load_openapi_spec_accepts_string_path(spec_path):
    # Act
    result = load_openapi_spec(str(spec_path("minimal.json")))

    # Assert
    assert isinstance(result, oa.OpenAPI)


def test_load_openapi_spec_with_yml_extension_works(temp_spec_file):
    # Arrange
    content = """
openapi: "3.1.0"
info:
    title: YML Test
    version: "1.0.0"
paths: {}
"""
    path = temp_spec_file("test.yml", content)

    # Act
    result = load_openapi_spec(path)

    # Assert
    assert result.info.title == "YML Test"
