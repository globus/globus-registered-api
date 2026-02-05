# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import pytest

from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.openapi import OpenAPILoadError
from globus_registered_api.openapi import TargetNotFoundError
from globus_registered_api.openapi import process_target
from globus_registered_api.openapi.loader import load_openapi_spec


def test_process_target_with_spec_object_returns_processing_result(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")

    # Act
    result = process_target(spec, target)

    # Assert
    assert result.target.operation.summary == "List items"


def test_process_target_result_contains_target(spec_path):
    # Arrange
    target = TargetSpecifier.create("get", "/items")

    # Act
    result = process_target(spec_path("minimal.json"), target)

    # Assert
    assert result.target is not None
    assert result.target.operation.summary == "List items"


def test_process_target_to_dict_returns_correct_structure(spec_path):
    # Arrange
    target = TargetSpecifier.create("get", "/items")

    # Act
    result = process_target(spec_path("minimal.json"), target)
    output = result.to_dict()

    # Assert
    assert output["type"] == "openapi"
    assert output["openapi_version"] == "3.1"
    assert "destination" in output
    assert "specification" in output


def test_process_target_with_refs_collects_components(spec_path):
    # Arrange
    target = TargetSpecifier.create("get", "/items")

    # Act
    result = process_target(spec_path("with_refs.json"), target)
    output = result.to_dict()

    # Assert
    assert "components" in output
    assert "Item" in output["components"]["schemas"]


def test_process_target_with_invalid_path_raises_load_error():
    # Arrange
    target = TargetSpecifier.create("get", "/items")

    # Act & Assert
    with pytest.raises(OpenAPILoadError, match="^Failed to read file:"):
        process_target("/nonexistent/path.json", target)


def test_process_target_with_invalid_route_raises_target_not_found(spec_path):
    # Arrange
    target = TargetSpecifier.create("get", "/nonexistent")

    # Act & Assert
    with pytest.raises(TargetNotFoundError, match="^Route not found: '/nonexistent'"):
        process_target(spec_path("minimal.json"), target)
