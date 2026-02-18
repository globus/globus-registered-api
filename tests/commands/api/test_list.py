# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import responses


def test_list_registered_apis_text_format(gra, crud_patcher):
    crud_patcher.patch_list(
        json={
            "registered_apis": [
                {"id": "abc-123", "name": "Test API 1"},
                {"id": "def-456", "name": "Test API 2"},
            ],
            "has_next_page": False,
            "marker": None,
        },
    )

    result = gra(["api", "list"])

    assert result.exit_code == 0
    assert "ID" in result.output
    assert "Name" in result.output
    assert "abc-123" in result.output
    assert "Test API 1" in result.output
    assert "def-456" in result.output
    assert "Test API 2" in result.output


def test_list_registered_apis_json_format(gra, crud_patcher):
    crud_patcher.patch_list(
        json={
            "registered_apis": [
                {"id": "abc-123", "name": "Test API 1"},
            ],
            "has_next_page": False,
            "marker": None,
        },
    )

    result = gra(["api", "list", "--format", "json"])

    assert result.exit_code == 0
    assert '"id": "abc-123"' in result.output
    assert '"name": "Test API 1"' in result.output


def test_list_registered_apis_empty_result(gra, crud_patcher):
    crud_patcher.patch_list(
        json={
            "registered_apis": [],
            "has_next_page": False,
            "marker": None,
        },
    )

    result = gra(["api", "list"])

    assert result.exit_code == 0
    assert "ID" not in result.output


def test_list_registered_apis_with_filter_roles(gra, crud_patcher):
    crud_patcher.patch_list(
        json={
            "registered_apis": [],
            "has_next_page": False,
            "marker": None,
        },
    )

    gra(["api", "list", "--filter-roles", "owner", "--filter-roles", "administrator"])

    assert "filter_roles=owner%2Cadministrator" in responses.calls[0].request.url


def test_list_registered_apis_with_per_page(gra, crud_patcher):
    crud_patcher.patch_list(
        json={
            "registered_apis": [],
            "has_next_page": False,
            "marker": None,
        },
    )

    gra(["api", "list", "--per-page", "50"])

    assert "per_page=50" in responses.calls[0].request.url
