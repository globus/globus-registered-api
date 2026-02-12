# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json

from globus_registered_api.cli import cli


def test_willdelete_print_includes_required_fields(cli_runner, spec_path):
    # Act
    result = cli_runner.invoke(
        cli,
        ["willdelete", "print-target", str(spec_path("minimal.json")), "get", "/items"],
    )

    # Assert
    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["type"] == "openapi"
    assert output["openapi_version"] == "3.1"
    assert "destination" in output
    assert "specification" in output
    assert output["transforms"] is None


def test_willdelete_print_destination_has_method_and_url(cli_runner, spec_path):
    # Act
    result = cli_runner.invoke(
        cli,
        ["willdelete", "print-target", str(spec_path("minimal.json")), "get", "/items"],
    )

    # Assert
    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["destination"]["method"] == "get"
    assert output["destination"]["url"] == "https://api.example.com/items"


def test_willdelete_print_with_refs_includes_components(cli_runner, spec_path):
    # Act
    result = cli_runner.invoke(
        cli,
        [
            "willdelete",
            "print-target",
            str(spec_path("with_refs.json")),
            "get",
            "/items",
        ],
    )

    # Assert
    assert result.exit_code == 0
    output = json.loads(result.output)
    assert "components" in output
    assert "Item" in output["components"]["schemas"]


def test_willdelete_print_with_content_type_option(cli_runner, spec_path):
    # Act
    result = cli_runner.invoke(
        cli,
        [
            "willdelete",
            "print-target",
            str(spec_path("multiple_content_types.json")),
            "post",
            "/upload",
            "--content-type",
            "application/json",
        ],
    )

    # Assert
    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["destination"]["method"] == "post"
    request_body = output["specification"]["requestBody"]
    assert "application/json" in request_body["content"]


def test_willdelete_print_with_nonexistent_file_shows_error(cli_runner):
    # Act
    result = cli_runner.invoke(
        cli, ["willdelete", "print-target", "/nonexistent.json", "get", "/items"]
    )

    # Assert
    assert result.exit_code != 0
    assert "Failed to read file:" in result.output
    assert "nonexistent.json" in result.output


def test_willdelete_print_with_invalid_route_shows_error(cli_runner, spec_path):
    # Act
    result = cli_runner.invoke(
        cli,
        [
            "willdelete",
            "print-target",
            str(spec_path("minimal.json")),
            "get",
            "/nonexistent",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Route not found: '/nonexistent'" in result.output


def test_willdelete_print_with_invalid_method_shows_error(cli_runner, spec_path):
    # Act
    result = cli_runner.invoke(
        cli,
        [
            "willdelete",
            "print-target",
            str(spec_path("minimal.json")),
            "delete",
            "/items",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Method 'DELETE' not found for route '/items'" in result.output


def test_willdelete_print_with_ambiguous_content_type_shows_error(
    cli_runner, spec_path
):
    # Act
    result = cli_runner.invoke(
        cli,
        [
            "willdelete",
            "print-target",
            str(spec_path("multiple_content_types.json")),
            "post",
            "/upload",
        ],
    )

    # Assert
    assert result.exit_code != 0
    assert "Multiple content-types match" in result.output
