# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import responses
from conftest import LIST_REGISTERED_APIS_URL

import globus_registered_api.cli
from globus_registered_api.extended_flows_client import ExtendedFlowsClient


@patch("globus_registered_api.cli._create_flows_client")
def test_list_registered_apis_text_format(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": "abc-123", "name": "Test API 1"},
                {"id": "def-456", "name": "Test API 2"},
            ],
            "has_next_page": False,
            "marker": None,
        },
    )

    result = cli_runner.invoke(globus_registered_api.cli.cli, ["list"])

    assert result.exit_code == 0
    assert "ID" in result.output
    assert "Name" in result.output
    assert "abc-123" in result.output
    assert "Test API 1" in result.output
    assert "def-456" in result.output
    assert "Test API 2" in result.output


@patch("globus_registered_api.cli._create_flows_client")
def test_list_registered_apis_json_format(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": "abc-123", "name": "Test API 1"},
            ],
            "has_next_page": False,
            "marker": None,
        },
    )

    result = cli_runner.invoke(
        globus_registered_api.cli.cli, ["list", "--format", "json"]
    )

    assert result.exit_code == 0
    assert '"id": "abc-123"' in result.output
    assert '"name": "Test API 1"' in result.output


@patch("globus_registered_api.cli._create_flows_client")
def test_list_registered_apis_empty_result(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [],
            "has_next_page": False,
            "marker": None,
        },
    )

    result = cli_runner.invoke(globus_registered_api.cli.cli, ["list"])

    assert result.exit_code == 0
    assert "ID" not in result.output


@patch("globus_registered_api.cli._create_flows_client")
def test_list_registered_apis_with_filter_roles(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [],
            "has_next_page": False,
            "marker": None,
        },
    )

    cli_runner.invoke(
        globus_registered_api.cli.cli,
        ["list", "--filter-roles", "owner", "--filter-roles", "administrator"],
    )

    assert "filter_roles=owner%2Cadministrator" in responses.calls[0].request.url


@patch("globus_registered_api.cli._create_flows_client")
def test_list_registered_apis_with_per_page(mock_create_client, cli_runner):
    mock_create_client.return_value = ExtendedFlowsClient()
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [],
            "has_next_page": False,
            "marker": None,
        },
    )

    cli_runner.invoke(globus_registered_api.cli.cli, ["list", "--per-page", "50"])

    assert "per_page=50" in responses.calls[0].request.url
