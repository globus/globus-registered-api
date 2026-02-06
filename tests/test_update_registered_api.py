# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from unittest.mock import patch

import responses
from conftest import UPDATE_REGISTERED_API_URL

import globus_registered_api.cli
from globus_registered_api.extended_flows_client import ExtendedFlowsClient


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_text_format(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
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

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        ["update", "12345678-1234-1234-1234-123456789abc", "--name", "Updated API"],
    )

    assert result.exit_code == 0
    assert "ID:" in result.output
    assert "12345678-1234-1234-1234-123456789abc" in result.output
    assert "Name:" in result.output
    assert "Updated API" in result.output


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_json_format(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": "12345678-1234-1234-1234-123456789abc",
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

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        [
            "update",
            "12345678-1234-1234-1234-123456789abc",
            "--name",
            "Updated API",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert '"id": "12345678-1234-1234-1234-123456789abc"' in result.output
    assert '"name": "Updated API"' in result.output


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_calls_correct_endpoint(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    api_id = "12345678-1234-1234-1234-123456789abc"
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
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

    cli_runner.invoke(
        globus_registered_api.cli.cli, ["update", api_id, "--name", "Test"]
    )

    assert f"/registered_apis/{api_id}" in responses.calls[0].request.url
    assert responses.calls[0].request.method == "PATCH"


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_not_found(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    api_id = "12345678-1234-1234-1234-123456789abc"
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        status=404,
        json={
            "error": {
                "code": "NOT_FOUND",
                "detail": f"No Registered API exists with id value {api_id}",
            }
        },
    )

    result = cli_runner.invoke(
        globus_registered_api.cli.cli, ["update", api_id, "--name", "Test"]
    )

    assert result.exit_code != 0
    assert "No Registered API exists" in str(result.exception)


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_with_description(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": "abcdef12-1234-1234-1234-123456789abc",
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

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        [
            "update",
            "abcdef12-1234-1234-1234-123456789abc",
            "--description",
            "New description",
        ],
    )

    assert result.exit_code == 0
    assert "New description" in result.output


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_with_owner(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": "abcdef12-1234-1234-1234-123456789abc",
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:new-owner"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        [
            "update",
            "abcdef12-1234-1234-1234-123456789abc",
            "--owner",
            "urn:globus:auth:identity:new-owner",
        ],
    )

    assert result.exit_code == 0
    assert "Owners:" in result.output
    assert "urn:globus:auth:identity:new-owner" in result.output


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_with_multiple_owners(mock_create_client, cli_runner):

    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": "abcdef12-1234-1234-1234-123456789abc",
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": [
                    "urn:globus:auth:identity:user1",
                    "urn:globus:auth:identity:user2",
                ],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        [
            "update",
            "abcdef12-1234-1234-1234-123456789abc",
            "--owner",
            "urn:globus:auth:identity:user2",
            "--owner",
            "urn:globus:auth:identity:user1",
            "--owner",
            "urn:globus:auth:identity:user2",  # duplicate
        ],
    )

    assert result.exit_code == 0
    request_body = json.loads(responses.calls[0].request.body)
    # Duplicate should be removed
    assert set(request_body["roles"]["owners"]) == {
        "urn:globus:auth:identity:user1",
        "urn:globus:auth:identity:user2",
    }


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_no_viewers_clears_viewers(
    mock_create_client, cli_runner
):

    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": "abcdef12-1234-1234-1234-123456789abc",
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

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        ["update", "abcdef12-1234-1234-1234-123456789abc", "--no-viewers"],
    )

    assert result.exit_code == 0
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["roles"]["viewers"] == []


@patch("globus_registered_api.cli._create_flows_client")
def test_update_registered_api_no_administrators_clears_administrators(
    mock_create_client, cli_runner
):

    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": "abcdef12-1234-1234-1234-123456789abc",
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

    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        ["update", "abcdef12-1234-1234-1234-123456789abc", "--no-administrators"],
    )

    assert result.exit_code == 0
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["roles"]["administrators"] == []


def test_update_registered_api_viewer_and_no_viewers_mutually_exclusive(cli_runner):
    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        [
            "update",
            "abcdef12-1234-1234-1234-123456789abc",
            "--viewer",
            "urn:globus:auth:identity:user1",
            "--no-viewers",
        ],
    )

    assert result.exit_code != 0
    assert "cannot be used together" in result.output


def test_update_registered_api_administrator_and_no_administrators_mutually_exclusive(
    cli_runner,
):
    result = cli_runner.invoke(
        globus_registered_api.cli.cli,
        [
            "update",
            "abcdef12-1234-1234-1234-123456789abc",
            "--administrator",
            "urn:globus:auth:identity:user1",
            "--no-administrators",
        ],
    )

    assert result.exit_code != 0
    assert "cannot be used together" in result.output
