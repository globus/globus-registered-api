# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json

import pytest
import responses


def test_create_registered_api_text_format(gra, crud_patcher, spec_path):
    # Arrange
    crud_patcher.patch_create(
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "My API",
            "description": "Test description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
        status=201,
    )

    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "get",
            "/items",
            "My API",
            "--description",
            "Test description",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "ID:" in result.output
    assert "12345678-1234-1234-1234-123456789abc" in result.output
    assert "Name:" in result.output
    assert "My API" in result.output


def test_create_registered_api_json_format(gra, crud_patcher, spec_path):
    # Arrange
    crud_patcher.patch_create(
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "My API",
            "description": "Test description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
        status=201,
    )

    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "get",
            "/items",
            "My API",
            "--description",
            "Test description",
            "--format",
            "json",
        ],
    )

    # Assert
    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["id"] == "12345678-1234-1234-1234-123456789abc"
    assert output["name"] == "My API"


def test_create_registered_api_with_description(gra, crud_patcher, spec_path):
    # Arrange
    crud_patcher.patch_create(
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "My API",
            "description": "A detailed description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
        status=201,
    )

    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "get",
            "/items",
            "My API",
            "--description",
            "A detailed description",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "A detailed description" in result.output
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["description"] == "A detailed description"


def test_create_registered_api_sends_correct_target(gra, crud_patcher, spec_path):
    # Arrange
    crud_patcher.patch_create(
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "My API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
        status=201,
    )

    # Act
    gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "get",
            "/items",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["name"] == "My API"
    assert "target" in request_body
    target = request_body["target"]
    assert target["type"] == "openapi"
    assert target["openapi_version"] == "3.1"
    assert target["destination"]["method"] == "get"
    assert target["destination"]["url"] == "https://api.example.com/items"


def test_create_registered_api_with_content_type(gra, crud_patcher, spec_path):
    # Arrange
    crud_patcher.patch_create(
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "Upload API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
        status=201,
    )

    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("multiple_content_types.json")),
            "post",
            "/upload",
            "Upload API",
            "--description",
            "Test",
            "--content-type",
            "application/json",
        ],
    )

    # Assert
    assert result.exit_code == 0
    request_body = json.loads(responses.calls[0].request.body)
    target = request_body["target"]
    assert target["destination"]["method"] == "post"


def test_create_registered_api_with_nonexistent_file_shows_error(gra):
    # Act
    result = gra(
        [
            "api",
            "create",
            "/nonexistent.json",
            "get",
            "/items",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Failed to read file:" in result.output


def test_create_registered_api_with_invalid_route_shows_error(gra, spec_path):
    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "get",
            "/nonexistent",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Route not found: '/nonexistent'" in result.output


def test_create_registered_api_with_invalid_method_shows_error(gra, spec_path):
    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "delete",
            "/items",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Method 'DELETE' not found for route '/items'" in result.output


def test_create_registered_api_with_ambiguous_content_type_shows_error(gra, spec_path):
    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("multiple_content_types.json")),
            "post",
            "/upload",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Multiple content-types match" in result.output


def test_create_registered_api_calls_post_endpoint(gra, crud_patcher, spec_path):
    # Arrange
    crud_patcher.patch_create(
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "My API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
        status=201,
    )

    # Act
    gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "get",
            "/items",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    assert "/registered_apis" in responses.calls[0].request.url
    assert responses.calls[0].request.method == "POST"


def test_create_registered_api_api_error(gra, crud_patcher, spec_path):
    # Arrange
    crud_patcher.patch_create(
        status=400,
        json={
            "error": {
                "code": "VALIDATION_ERROR",
                "detail": "Invalid target specification",
            }
        },
    )

    # Act
    result = gra(
        [
            "api",
            "create",
            str(spec_path("minimal.json")),
            "get",
            "/items",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Invalid target specification" in str(result.exception)


@pytest.mark.parametrize(
    "args,expected_error",
    [
        pytest.param(
            ["api", "create", "SPEC", "get", "/items", "My API"],
            "Missing option '--description'",
            id="missing-description",
        ),
        pytest.param(
            ["api", "create", "SPEC", "get", "/items", "--description", "Test"],
            "Missing argument 'NAME'",
            id="missing-name",
        ),
    ],
)
def test_create_registered_api_missing_required_param_shows_error(
    gra, spec_path, args, expected_error
):
    # Arrange
    args = [str(spec_path("minimal.json")) if arg == "SPEC" else arg for arg in args]

    # Act
    result = gra(args)

    # Assert
    assert result.exit_code != 0
    assert expected_error in result.output


def test_create_registered_api_with_url_containing_query_params(
    gra, crud_patcher, spec_path
):
    # Arrange
    spec_url = "https://domain.example/spec?format=json&download=true"
    spec_content = spec_path("minimal.json").read_text()

    responses.add(responses.GET, spec_url, body=spec_content, status=200)
    crud_patcher.patch_create(
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "My API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
        status=201,
    )

    # Act
    result = gra(
        [
            "api",
            "create",
            spec_url,
            "get",
            "/items",
            "My API",
            "--description",
            "Test",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "12345678-1234-1234-1234-123456789abc" in result.output
    assert responses.calls[0].request.url == spec_url
