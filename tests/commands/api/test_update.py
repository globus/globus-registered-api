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
def patch_update(api_url_patterns) -> t.Iterable[t.Callable[..., None]]:
    yield functools.partial(
        responses.add,
        method=responses.PATCH,
        url=api_url_patterns.UPDATE,
    )


def test_update_registered_api_text_format(gra, patch_update):
    api_id = "12345678-1234-1234-1234-123456789abc"
    patch_update(
        json={
            "id": api_id,
            "name": "Updated API",
            "description": "Updated description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = gra(["api", "update", api_id, "--name", "Updated API"])

    assert result.exit_code == 0
    assert "ID:" in result.output
    assert "12345678-1234-1234-1234-123456789abc" in result.output
    assert "Name:" in result.output
    assert "Updated API" in result.output


def test_update_registered_api_json_format(gra, patch_update):
    api_id = "12345678-1234-1234-1234-123456789abc"
    patch_update(
        json={
            "id": api_id,
            "name": "Updated API",
            "description": "Updated description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = gra(["api", "update", api_id, "--name", "Updated API", "--format", "json"])

    assert result.exit_code == 0
    assert '"id": "12345678-1234-1234-1234-123456789abc"' in result.output
    assert '"name": "Updated API"' in result.output


def test_update_registered_api_calls_correct_endpoint(gra, patch_update):
    api_id = "12345678-1234-1234-1234-123456789abc"
    patch_update(
        json={
            "id": api_id,
            "name": "Test",
            "description": "",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    gra(["api", "update", api_id, "--name", "Test"])

    assert f"/registered_apis/{api_id}" in responses.calls[0].request.url
    assert responses.calls[0].request.method == "PATCH"


def test_update_registered_api_not_found(gra, patch_update):
    api_id = "12345678-1234-1234-1234-123456789abc"
    patch_update(
        status=404,
        json={
            "error": {
                "code": "NOT_FOUND",
                "detail": f"No Registered API exists with id value {api_id}",
            }
        },
    )

    result = gra(["api", "update", api_id, "--name", "Test"])

    assert result.exit_code != 0
    assert "No Registered API exists" in str(result.exception)


def test_update_registered_api_with_description(gra, patch_update):
    api_id = "abcdef12-1234-1234-1234-123456789abc"
    patch_update(
        json={
            "id": api_id,
            "name": "Test API",
            "description": "New description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = gra(["api", "update", api_id, "--description", "New description"])

    assert result.exit_code == 0
    assert "New description" in result.output


def test_update_registered_api_with_owner(gra, patch_update):
    api_id = "abcdef12-1234-1234-1234-123456789abc"
    owner_urn = "urn:globus:auth:identity:new-owner"
    patch_update(
        json={
            "id": "abcdef12-1234-1234-1234-123456789abc",
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": [owner_urn],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = gra(["api", "update", api_id, "--owner", owner_urn])

    assert result.exit_code == 0
    assert "Owners:" in result.output
    assert owner_urn in result.output


def test_update_registered_api_with_multiple_owners(gra, patch_update):
    api_id = "abcdef12-1234-1234-1234-123456789abc"
    user1_urn = "urn:globus:auth:identity:user1"
    user2_urn = "urn:globus:auth:identity:user2"
    patch_update(
        json={
            "id": api_id,
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": [user1_urn, user2_urn],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = gra(
        [
            "api",
            "update",
            api_id,
            "--owner",
            user2_urn,
            "--owner",
            user1_urn,
            "--owner",
            user2_urn,  # duplicate
        ],
    )

    assert result.exit_code == 0
    request_body = json.loads(responses.calls[0].request.body)
    # Duplicate should be removed
    assert set(request_body["roles"]["owners"]) == {user1_urn, user2_urn}


def test_update_registered_api_no_viewers_clears_viewers(gra, patch_update):
    api_id = "abcdef12-1234-1234-1234-123456789abc"
    patch_update(
        json={
            "id": api_id,
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = gra(["api", "update", api_id, "--no-viewers"])

    assert result.exit_code == 0
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["roles"]["viewers"] == []


def test_update_registered_api_no_administrators_clears_administrators(
    gra, patch_update
):
    api_id = "abcdef12-1234-1234-1234-123456789abc"
    patch_update(
        json={
            "id": api_id,
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = gra(["api", "update", api_id, "--no-administrators"])

    assert result.exit_code == 0
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["roles"]["administrators"] == []


def test_update_registered_api_viewer_and_no_viewers_mutually_exclusive(gra):
    api_id = "abcdef12-1234-1234-1234-123456789abc"
    user1_urn = "urn:globus:auth:identity:user1"

    result = gra(["api", "update", api_id, "--viewer", user1_urn, "--no-viewers"])

    assert result.exit_code != 0
    assert "cannot be used together" in result.output


def test_update_registered_api_administrator_and_no_administrators_mutually_exclusive(
    gra,
):
    api_id = "abcdef12-1234-1234-1234-123456789abc"
    user1_urn = "urn:globus:auth:identity:user1"

    result = gra(
        [
            "api",
            "update",
            api_id,
            "--administrator",
            user1_urn,
            "--no-administrators",
        ],
    )

    assert result.exit_code != 0
    assert "cannot be used together" in result.output
