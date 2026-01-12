# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import pytest

from globus_registered_api.openapi import TargetSpecifier


def test_target_specifier_create_normalizes_method_to_uppercase():
    # Arrange / Act
    target = TargetSpecifier.create("get", "/items")

    # Assert
    assert target.method == "GET"


def test_target_specifier_create_preserves_path():
    # Arrange / Act
    target = TargetSpecifier.create("get", "/items/{id}")

    # Assert
    assert target.path == "/items/{id}"


def test_target_specifier_create_with_content_type():
    # Arrange / Act
    target = TargetSpecifier.create("post", "/items", "application/json")

    # Assert
    assert target.content_type == "application/json"


def test_target_specifier_create_rejects_invalid_method():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="Invalid HTTP method"):
        TargetSpecifier.create("INVALID", "/items")


def test_target_specifier_create_rejects_path_without_leading_slash():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="Path must start with"):
        TargetSpecifier.create("get", "items")


def test_target_specifier_load_parses_method_and_path():
    # Arrange / Act
    target = TargetSpecifier.load("GET /items")

    # Assert
    assert target.method == "GET"
    assert target.path == "/items"
    assert target.content_type == "*" # Default content-type


def test_target_specifier_load_parses_with_content_type():
    # Arrange / Act
    target = TargetSpecifier.load("POST /items application/json")

    # Assert
    assert target.method == "POST"
    assert target.path == "/items"
    assert target.content_type == "application/json"


def test_target_specifier_load_handles_path_with_parameters():
    # Arrange / Act
    target = TargetSpecifier.load("PUT /items/{id} application/json")

    # Assert
    assert target.path == "/items/{id}"


def test_target_specifier_load_normalizes_lowercase_method():
    # Arrange / Act
    target = TargetSpecifier.load("get /items")

    # Assert
    assert target.method == "GET"


def test_target_specifier_load_rejects_invalid_format():
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="Invalid TargetSpecifier string"):
        TargetSpecifier.load("invalid format")


def test_target_specifier_is_immutable():
    # Arrange
    target = TargetSpecifier.create("get", "/items")

    # Act / Assert
    with pytest.raises(AttributeError):
        target.method = "POST"


def test_target_specifier_equality():
    # Arrange
    target1 = TargetSpecifier.create("get", "/items")
    target2 = TargetSpecifier.create("GET", "/items")

    # Assert
    assert target1 == target2


def test_target_specifier_can_be_used_as_dict_key():
    # Arrange
    target = TargetSpecifier.create("get", "/items")
    mapping = {target: "value"}

    # Act / Assert
    assert mapping[TargetSpecifier.create("get", "/items")] == "value"


def test_target_specifier_supports_all_http_methods():
    # Arrange
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]

    # Act / Assert
    for method in methods:
        target = TargetSpecifier.create(method, "/test")
        assert target.method == method
