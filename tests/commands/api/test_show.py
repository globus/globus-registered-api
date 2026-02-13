# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import responses
from conftest import GET_REGISTERED_API_URL

import globus_registered_api.cli


def test_show_registered_api_text_format(mock_flows_client, cli_runner):
    responses.add(
        responses.GET,
        GET_REGISTERED_API_URL,
        json={
            "id": "abc-123-def-456",
            "name": "Test API",
            "description": "A test description",
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "updated_timestamp": "2025-01-02T00:00:00+00:00",
        },
    )

    result = cli_runner.invoke(
        globus_registered_api.cli.cli, ["api", "show", "abc-123-def-456"]
    )

    assert result.exit_code == 0
    assert "ID:" in result.output
    assert "abc-123-def-456" in result.output
    assert "Name:" in result.output
    assert "Test API" in result.output
    assert "Description:" in result.output
    assert "A test description" in result.output
    assert "Created:" in result.output
    assert "Updated:" in result.output


def test_show_registered_api_json_format(mock_flows_client, cli_runner):
    responses.add(
        responses.GET,
        GET_REGISTERED_API_URL,
        json={
            "id": "abc-123-def-456",
            "name": "Test API",
            "description": "A test description",
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "updated_timestamp": "2025-01-02T00:00:00+00:00",
        },
    )

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        ["api", "show", "abc-123-def-456", "--format", "json"],
    )

    assert result.exit_code == 0
    assert '"id": "abc-123-def-456"' in result.output
    assert '"name": "Test API"' in result.output
    assert '"description": "A test description"' in result.output


def test_show_registered_api_empty_description(mock_flows_client, cli_runner):
    responses.add(
        responses.GET,
        GET_REGISTERED_API_URL,
        json={
            "id": "abc-123-def-456",
            "name": "Minimal API",
            "description": "",
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "updated_timestamp": "2025-01-01T00:00:00+00:00",
        },
    )

    result = cli_runner.invoke(
        globus_registered_api.cli.cli, ["api", "show", "abc-123-def-456"]
    )

    assert result.exit_code == 0
    assert "Minimal API" in result.output
    assert "Description:" in result.output


def test_show_registered_api_calls_correct_endpoint(mock_flows_client, cli_runner):
    api_id = "12345678-1234-1234-1234-123456789abc"
    responses.add(
        responses.GET,
        GET_REGISTERED_API_URL,
        json={
            "id": api_id,
            "name": "Test",
            "description": "",
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "updated_timestamp": "2025-01-01T00:00:00+00:00",
        },
    )

    cli_runner.invoke(globus_registered_api.cli.cli, ["api", "show", api_id])

    assert f"/registered_apis/{api_id}" in responses.calls[0].request.url


def test_get_registered_api_not_found(mock_flows_client, cli_runner):
    api_id = "12345678-1234-1234-1234-123456789abc"
    responses.add(
        responses.GET,
        GET_REGISTERED_API_URL,
        status=404,
        json={
            "error": {
                "code": "NOT_FOUND",
                "detail": f"No Registered API exists with id value {api_id}",
            }
        },
    )

    result = cli_runner.invoke(globus_registered_api.cli.cli, ["api", "show", api_id])

    assert result.exit_code != 0
    assert "No Registered API exists" in str(result.exception)
