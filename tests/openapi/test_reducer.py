# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import pytest

from globus_registered_api.openapi import TargetSpecifier
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.openapi.selector import find_target
from globus_registered_api.openapi.reducer import reduce_to_target
from globus_registered_api.openapi.reducer import OpenAPITarget


# --- Basic reduction ---


def test_reduce_to_target_returns_openapi_target(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert isinstance(result, OpenAPITarget)


def test_reduce_to_target_includes_operation(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert result.operation is not None
    assert result.operation.summary == "List items"


def test_reduce_to_target_includes_destination(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert result.destination is not None
    assert result.destination["method"] == "get"
    assert result.destination["url"] == "https://api.example.com/items"


def test_reduce_to_target_transforms_is_none(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert result.transforms is None


# --- Component collection ---


def test_reduce_to_target_collects_referenced_schemas(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert result.components is not None
    assert "schemas" in result.components
    assert "Item" in result.components["schemas"]


def test_reduce_to_target_collects_transitive_references(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert "Metadata" in result.components["schemas"]


def test_reduce_to_target_collects_request_body_schemas(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("post", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert "CreateItemRequest" in result.components["schemas"]


def test_reduce_to_target_collects_error_response_schemas(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("post", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert "Error" in result.components["schemas"]


def test_reduce_to_target_without_refs_has_empty_components(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert result.components is None or result.components == {}


# --- Output format ---


def test_reduce_to_target_to_dict_returns_correct_structure(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)
    output = result.to_dict()

    # Assert
    assert output["type"] == "openapi"
    assert output["openapi_version"] == "3.1"
    assert "destination" in output
    assert "specification" in output
    assert output["transforms"] is None


def test_reduce_to_target_to_dict_includes_components_when_present(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)
    output = result.to_dict()

    # Assert
    assert "components" in output
    assert output["components"] is not None


# --- URL construction ---


def test_reduce_to_target_builds_url_from_server_and_path(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("get", "/items/{id}")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert result.destination["url"] == "https://api.example.com/items/{id}"


def test_reduce_to_target_handles_server_url_with_trailing_slash(temp_spec_file):
    # Arrange
    content = """
{
  "openapi": "3.1.0",
  "info": {"title": "Test", "version": "1.0.0"},
  "servers": [{"url": "https://api.example.com/"}],
  "paths": {
    "/items": {
      "get": {
        "summary": "List",
        "responses": {"200": {"description": "OK"}}
      }
    }
  }
}
"""
    path = temp_spec_file("trailing_slash.json", content)
    spec = load_openapi_spec(path)
    target = TargetSpecifier.create("get", "/items")
    target_info = find_target(spec, target)

    # Act
    result = reduce_to_target(spec, target_info)

    # Assert
    assert result.destination["url"] == "https://api.example.com/items"


# --- Edge cases ---


def test_reduce_to_target_handles_circular_references(temp_spec_file):
    # Arrange
    content = """
{
  "openapi": "3.1.0",
  "info": {"title": "Circular", "version": "1.0.0"},
  "servers": [{"url": "https://api.example.com"}],
  "paths": {
    "/nodes": {
      "get": {
        "summary": "Get nodes",
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {"$ref": "#/components/schemas/Node"}
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Node": {
        "type": "object",
        "properties": {
          "children": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/Node"}
          }
        }
      }
    }
  }
}
"""
    path = temp_spec_file("circular.json", content)
    spec = load_openapi_spec(path)
    target = TargetSpecifier.create("get", "/nodes")
    target_info = find_target(spec, target)

    # Act - should not infinite loop
    result = reduce_to_target(spec, target_info)

    # Assert
    assert "Node" in result.components["schemas"]
