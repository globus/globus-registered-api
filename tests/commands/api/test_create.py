# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import functools
import json
import typing as t

import pytest
import responses


@pytest.fixture
def patch_create(
    api_url_patterns,
) -> t.Iterable[t.Callable[..., responses.BaseResponse]]:
    yield functools.partial(
        responses.add,
        method=responses.POST,
        url=api_url_patterns.CREATE,
    )


@pytest.fixture
def target_path(tmp_path):
    target_file = tmp_path / "target.json"
    target_file.write_text(
        json.dumps(
            {
                "type": "openapi",
                "openapi_version": "3.1",
                "destination": {
                    "method": "get",
                    "url": "https://api.example.com/items",
                },
            }
        )
    )
    return target_file


@pytest.fixture
def target_option(target_path):
    return ["--target", str(target_path)]


def test_create_registered_api_text_format(gra, patch_create, target_option):
    # Arrange
    api_id = "12345678-1234-1234-1234-123456789abc"
    name, desc = "My API", "Test description"
    patch_create(
        json={
            "id": api_id,
            "name": name,
            "description": desc,
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
            "updated_timestamp": None,
        },
        status=201,
    )

    # Act
    result = gra(["api", "create", name, *target_option, "--description", desc])

    # Assert
    assert result.exit_code == 0
    assert "ID:" in result.output
    assert api_id in result.output
    assert "Name:" in result.output
    assert name in result.output
    assert "Description:" in result.output
    assert desc in result.output


def test_create_registered_api_json_format(gra, patch_create, target_option):
    # Arrange
    api_id = "12345678-1234-1234-1234-123456789abc"
    name, desc = "My API", "Test description"
    patch_create(
        json={
            "id": api_id,
            "name": name,
            "description": desc,
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
            "updated_timestamp": None,
        },
        status=201,
    )

    # Act
    basic_command = ["api", "create", name, *target_option, "--description", desc]
    result = gra(basic_command + ["--format", "json"])

    # Assert
    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["id"] == api_id
    assert output["name"] == name
    assert output["description"] == desc


def test_create_registered_api_with_nonexistent_file_shows_error(gra):
    # Act
    cmd = ["api", "create", "My API", "--target", "/nope.json", "--description", "Test"]
    result = gra(cmd)

    # Assert
    assert result.exit_code != 0
    assert "File '/nope.json' does not exist" in result.output


def test_create_registered_api_calls_post_endpoint(gra, patch_create, target_option):
    # Arrange
    api_id = "12345678-1234-1234-1234-123456789abc"
    name, desc = "My API", "Test Description"
    patched_create = patch_create(
        json={
            "id": api_id,
            "name": name,
            "description": desc,
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
            "updated_timestamp": None,
        },
        status=201,
    )

    # Act
    result = gra(["api", "create", name, *target_option, "--description", desc])

    # Assert
    assert result.exit_code == 0
    assert patched_create.call_count == 1


def test_create_registered_api_api_error(gra, patch_create, target_option):
    # Arrange
    patch_create(
        status=400,
        json={
            "error": {
                "code": "VALIDATION_ERROR",
                "detail": "Invalid target specification",
            }
        },
    )

    # Act
    result = gra(["api", "create", "My API", *target_option, "--description", "Test"])

    # Assert
    assert result.exit_code != 0
    assert "Invalid target specification" in result.stderr


@pytest.mark.parametrize(
    "args,expected_error",
    [
        pytest.param(
            ["api", "create", "--target", "$TARGET", "--description", "Test"],
            "Missing argument 'NAME'",
            id="missing-name",
        ),
        pytest.param(
            ["api", "create", "My API", "--description", "Test"],
            "Missing option '--target'",
            id="missing-target",
        ),
        pytest.param(
            ["api", "create", "My API", "--target", "$TARGET"],
            "Missing option '--description'",
            id="missing-description",
        ),
    ],
)
def test_create_registered_api_missing_required_param_shows_error(
    gra, target_path, args, expected_error
):
    # Arrange
    args = [str(target_path) if arg == "$TARGET" else arg for arg in args]

    # Act
    result = gra(args)

    # Assert
    assert result.exit_code != 0
    assert expected_error in result.output


def test_create_registered_api_with_single_owner_admin_and_viewer(
    gra, patch_create, target_option
):
    # Arrange
    api_id = "12345678-1234-1234-1234-123456789abc"
    name, desc = "My API", "Test Description"

    owner_urn = "urn:globus:auth:identity:user1"
    admin_urn = "urn:globus:auth:identity:user2"
    viewer_urn = "urn:globus:groups:id:group1"

    patch_create(
        json={
            "id": api_id,
            "name": name,
            "description": desc,
            "roles": {
                "owners": [owner_urn],
                "administrators": [admin_urn],
                "viewers": [viewer_urn],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
            "updated_timestamp": None,
        },
        status=201,
    )

    # Act
    basic_command = ["api", "create", name, *target_option, "--description", desc]
    result = gra(basic_command + ["--administrator", admin_urn, "--viewer", viewer_urn])

    assert result.exit_code == 0
    assert "Owners:" in result.output
    assert owner_urn in result.output
    assert "Administrators:" in result.output
    assert admin_urn in result.output
    assert "Viewers:" in result.output
    assert viewer_urn in result.output


def test_create_registered_api_with_multiple_owners_admins_and_viewers(
    gra, patch_create, target_option
):
    # Arrange
    api_id = "12345678-1234-1234-1234-123456789abc"
    name, desc = "My API", "Test Description"

    owner_urns = [
        "urn:globus:auth:identity:user1",
        "urn:globus:auth:identity:user2",
    ]
    admin_urns = [
        "urn:globus:auth:identity:user3",
        "urn:globus:auth:identity:user4",
    ]
    viewer_urns = [
        "urn:globus:groups:id:group1",
        "urn:globus:groups:id:group2",
    ]

    patch_create(
        json={
            "id": api_id,
            "name": name,
            "description": desc,
            "roles": {
                "owners": owner_urns,
                "administrators": admin_urns,
                "viewers": viewer_urns,
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
            "updated_timestamp": None,
        },
        status=201,
    )

    # Act
    basic_command = ["api", "create", name, *target_option, "--description", desc]
    result = gra(
        basic_command
        + ["--owner", owner_urns[0], "--owner", owner_urns[1]]
        + ["--administrator", admin_urns[0], "--administrator", admin_urns[1]]
        + ["--viewer", viewer_urns[0], "--viewer", viewer_urns[1]]
    )

    assert result.exit_code == 0
    for owner in owner_urns:
        assert owner in result.output
    for admin in admin_urns:
        assert admin in result.output
    for viewer in viewer_urns:
        assert viewer in result.output
