# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import pytest

from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.openapi.selector import AmbiguousContentTypeError
from globus_registered_api.openapi.selector import TargetInfo
from globus_registered_api.openapi.selector import TargetNotFoundError
from globus_registered_api.openapi.selector import find_target

# --- Exact route matching ---


def test_find_target_with_exact_route_returns_target_info(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")

    # Act
    result = find_target(spec, target)

    # Assert
    assert isinstance(result, TargetInfo)
    assert result.matched_target.path == "/items"
    assert result.matched_target.method == "GET"
    assert result.operation.summary == "List items"


def test_find_target_with_post_method_returns_correct_operation(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("post", "/items")

    # Act
    result = find_target(spec, target)

    # Assert
    assert result.matched_target.method == "POST"
    assert result.operation.summary == "Create item"


def test_find_target_with_path_parameter_returns_target(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("with_refs.json"))
    target = TargetSpecifier.create("get", "/items/{id}")

    # Act
    result = find_target(spec, target)

    # Assert
    assert result.matched_target.path == "/items/{id}"
    assert result.operation.summary == "Get item by ID"


# --- Error cases ---


def test_find_target_with_nonexistent_route_raises_error(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/nonexistent")

    # Act & Assert
    with pytest.raises(TargetNotFoundError, match="^Route not found: '/nonexistent'"):
        find_target(spec, target)


def test_find_target_with_nonexistent_method_raises_error(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("delete", "/items")

    # Act & Assert
    with pytest.raises(
        TargetNotFoundError, match="^Method 'DELETE' not found for route '/items'"
    ):
        find_target(spec, target)


# --- Content-type selection ---


def test_find_target_with_single_content_type_auto_selects(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("multiple_content_types.json"))
    target = TargetSpecifier.create("post", "/single-content")

    # Act
    result = find_target(spec, target)

    # Assert
    assert result.matched_target.content_type == "application/json"


def test_find_target_with_explicit_content_type_selects_it(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("multiple_content_types.json"))
    target = TargetSpecifier.create("post", "/upload", "application/xml")

    # Act
    result = find_target(spec, target)

    # Assert
    assert result.matched_target.content_type == "application/xml"


def test_find_target_with_wildcard_content_type_matching_multiple_raises_error(
    spec_path,
):
    # Arrange
    spec = load_openapi_spec(spec_path("multiple_content_types.json"))
    target = TargetSpecifier.create("post", "/upload", "application/*")

    # Act & Assert - "application/*" matches multiple, raises ambiguity error
    with pytest.raises(
        AmbiguousContentTypeError,
        match="^Multiple content-types match",
    ):
        find_target(spec, target)


def test_find_target_with_multiple_content_types_and_wildcard_raises_error(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("multiple_content_types.json"))
    target = TargetSpecifier.create("post", "/upload")  # default content_type is "*"

    # Act & Assert - "*" matches multiple, raises ambiguity error
    with pytest.raises(
        AmbiguousContentTypeError,
        match="^Multiple content-types match",
    ):
        find_target(spec, target)


def test_find_target_with_invalid_content_type_raises_error(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("multiple_content_types.json"))
    target = TargetSpecifier.create("post", "/upload", "text/plain")

    # Act & Assert
    with pytest.raises(
        TargetNotFoundError, match="^Content-type 'text/plain' not found\\."
    ):
        find_target(spec, target)


# --- No request body cases ---


def test_find_target_without_request_body_preserves_default_content_type(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items")  # default content_type is "*"

    # Act
    result = find_target(spec, target)

    # Assert - no request body, content_type unchanged
    assert result.matched_target.content_type == "*"


def test_find_target_without_request_body_preserves_explicit_content_type(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("get", "/items", "application/json")

    # Act
    result = find_target(spec, target)

    # Assert - no request body, content_type unchanged
    assert result.matched_target.content_type == "application/json"


# --- Case insensitivity ---


def test_find_target_method_is_case_insensitive(spec_path):
    # Arrange
    spec = load_openapi_spec(spec_path("minimal.json"))
    target = TargetSpecifier.create("GET", "/items")

    # Act
    result = find_target(spec, target)

    # Assert
    assert result.matched_target.method == "GET"
