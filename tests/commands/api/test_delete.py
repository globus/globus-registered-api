# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
import functools
import typing as t

import pytest
import responses


@pytest.fixture
def patch_delete(api_url_patterns) -> t.Iterable[t.Callable[..., None]]:
    yield functools.partial(
        responses.add,
        method=responses.DELETE,
        url=api_url_patterns.DELETE,
    )


def test_delete_registered_api_text_format(gra, patch_delete):
    api_id = "12345678-1234-1234-1234-123456789abc"

    patch_delete(
        json={
            "id": api_id,
            "name": "Test API",
            "status": "DELETE_PENDING",
            "scheduled_deletion_timestamp": "2025-02-01T00:00:00+00:00",
        },
        status=202,
    )

    result = gra(["api", "delete", api_id])

    assert result.exit_code == 0
    assert "Registered API marked for deletion:" in result.output
    assert api_id in result.output
    assert "Test API" in result.output
    assert "DELETE_PENDING" in result.output
    assert (
        "will be permanently deleted on February 01, 2025 at 00:00 UTC" in result.output
    )


def test_delete_registered_api_json_format(gra, patch_delete):
    api_id = "12345678-1234-1234-1234-123456789abc"

    patch_delete(
        json={
            "id": api_id,
            "name": "Test API",
            "status": "DELETE_PENDING",
            "scheduled_deletion_timestamp": "2025-02-01T00:00:00+00:00",
        },
        status=202,
    )

    result = gra(["api", "delete", api_id, "--format", "json"])

    assert result.exit_code == 0
    assert f'"id": "{api_id}"' in result.output
    assert '"status": "DELETE_PENDING"' in result.output
    assert '"scheduled_deletion_timestamp"' in result.output


def test_delete_registered_api_calls_correct_endpoint(gra, patch_delete):
    api_id = "12345678-1234-1234-1234-123456789abc"

    patch_delete(
        json={
            "id": api_id,
            "name": "Test API",
            "status": "DELETE_PENDING",
            "scheduled_deletion_timestamp": "2025-02-01T00:00:00+00:00",
        },
        status=202,
    )

    gra(["api", "delete", api_id])

    delete_calls = [c for c in responses.calls if c.request.method == "DELETE"]
    assert len(delete_calls) == 1
    assert f"/registered_apis/{api_id}" in delete_calls[0].request.url


def test_delete_registered_api_not_found(gra, patch_delete):
    api_id = "12345678-1234-1234-1234-123456789abc"

    patch_delete(
        status=404,
        json={
            "error": {
                "code": "NOT_FOUND",
                "detail": f"No Registered API exists with id value {api_id}",
            }
        },
    )

    result = gra(["api", "delete", api_id])

    assert result.exit_code != 0
    assert "No Registered API exists" in result.stderr


def test_delete_registered_api_forbidden(gra, patch_delete):
    api_id = "12345678-1234-1234-1234-123456789abc"

    patch_delete(
        status=403,
        json={
            "error": {
                "code": "FORBIDDEN",
                "detail": "Caller must be an owner of this registered API to delete",
            }
        },
    )

    result = gra(["api", "delete", api_id])

    assert result.exit_code != 0
    assert "FORBIDDEN" in result.stderr


def test_delete_registered_api_invalid_uuid(gra):
    result = gra(["api", "delete", "not-a-valid-uuid"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output or "not a valid UUID" in result.output
