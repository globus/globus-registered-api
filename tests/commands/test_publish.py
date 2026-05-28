# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import UUID
from uuid import uuid4

import pytest
import responses

from globus_registered_api.config import GRAConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig


@pytest.fixture
def populated_config(config):
    config.targets = {
        "get-example": TargetConfig(
            path="/example",
            method="GET",
            description="Get example resource",
        ),
        "create-example": TargetConfig(
            path="/example",
            method="POST",
            description="Create example resource",
        ),
    }
    config.stages["production"].roles = [
        RoleConfig(
            type="identity",
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            access_level="owner",
        ),
        RoleConfig(
            type="group",
            id=UUID("660e8400-e29b-41d4-a716-446655440001"),
            access_level="admin",
        ),
        RoleConfig(
            type="identity",
            id=UUID("770e8400-e29b-41d4-a716-446655440002"),
            access_level="viewer",
        ),
    ]
    return config


def test_publish_command_exists(gra):
    # Act
    result = gra(["publish", "--help"], catch_exceptions=False)

    # Assert
    assert result.exit_code == 0
    assert "Publish registered APIs to Flows service" in result.output


def test_publish_raises_error_when_config_missing(gra):
    # Act
    result = gra(["publish"], catch_exceptions=False)

    # Assert
    assert result.exit_code != 0
    assert "Error: Missing config file" in result.output


def test_publish_raises_error_when_manifest_missing(gra, config):
    # Arrange
    config.commit()

    # Act
    result = gra(["publish"], catch_exceptions=False)

    # Assert
    assert result.exit_code != 0
    assert "Error: Missing repository manifest file." in result.output
    assert "Run 'gra build' first to generate a manifest." in result.output


def test_publish_creates_new_registered_api_when_no_id_exists(
    gra, api_url_patterns, populated_config
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Assert -  No ID exists before publishing
    assert populated_config.stages["production"].registered_apis == {}

    # Add mock API response for create
    created_id = uuid4()
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id)},
        status=200,
    )

    # Act
    gra(["publish", "--yes"], catch_exceptions=False)

    # Assert - ID was written back to config
    registered_apis = GRAConfig.load().stages["production"].registered_apis
    assert registered_apis["get-example"].registered_api_id == created_id


def test_publish_updates_existing_registered_api_when_id_exists(
    gra,
    populated_config,
    api_url_patterns,
):
    # Arrange
    existing_id = uuid4()
    registered_apis = populated_config.stages["production"].registered_apis
    registered_apis["get-example"] = RegisteredAPIConfig(registered_api_id=existing_id)
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response for update
    responses.add(
        responses.PATCH,
        api_url_patterns.UPDATE,
        json={"id": str(existing_id)},
        status=200,
    )

    # Act - only update the first target by specifying alias
    gra(
        ["publish", "--target-alias", "get-example", "--yes"],
        catch_exceptions=False,
    )

    # Assert - ID is unchanged (update doesn't change the ID)
    registered_apis = GRAConfig.load().stages["production"].registered_apis
    assert registered_apis["get-example"].registered_api_id == existing_id


def test_publish_with_target_alias_filters_targets(
    gra,
    populated_config,
    api_url_patterns,
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response for create (only one target should be published)
    created_id = uuid4()
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id)},
        status=200,
    )

    # Act
    gra(
        ["publish", "--target-alias", "get-example", "--yes"],
        catch_exceptions=False,
    )

    # Assert - Verify only the selected target was created & stored
    assert len(responses.calls) == 1
    registered_apis = GRAConfig.load().stages["production"].registered_apis
    assert registered_apis.keys() == {"get-example"}


def test_publish_with_multiple_target_aliases(
    gra,
    populated_config,
    api_url_patterns,
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API responses for create
    created_id_1, created_id_2 = uuid4(), uuid4()
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id_1)},
        status=200,
    )
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id_2)},
        status=200,
    )

    # Act
    ta = "--target-alias"
    gra(
        ["publish", ta, "get-example", ta, "create-example", "--yes"],
        catch_exceptions=False,
    )

    # Assert - Verify both targets were created and stored
    assert len(responses.calls) == 2
    registered_apis = GRAConfig.load().stages["production"].registered_apis
    assert registered_apis.keys() == {"get-example", "create-example"}


def test_publish_raises_error_when_target_alias_not_found(gra, populated_config):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Act
    result = gra(["publish", "--target-alias", "nonexistent-target"])

    # Assert
    assert result.exit_code != 0
    assert "Error: Invalid target alias: nonexistent-target" in result.output
    assert "Allowed Values: create-example, get-example" in result.output


def test_publish_aborts_when_user_declines_confirmation(
    gra,
    populated_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # User declines confirmation
    prompt_patcher.add_input("confirmation", False)

    # Act
    result = gra(["publish"])

    # Assert
    assert result.exit_code != 0
    assert "Aborting publish." in result.output

    # Assert - no API calls were made
    assert len(responses.calls) == 0

    # Assert - config unchanged
    assert GRAConfig.load().stages["production"].registered_apis == {}


def test_publish_passes_correct_roles_to_api(
    gra,
    populated_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response
    created_id = str(uuid4())
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": created_id},
        status=200,
    )

    # Act
    gra(["publish", "--yes"], catch_exceptions=False)

    # Assert
    assert len(responses.calls) == 2

    # Verify request body contains correct role URNs
    request_body = json.loads(responses.calls[0].request.body)
    assert "roles" in request_body
    roles = request_body["roles"]
    assert "owners" in roles
    assert "administrators" in roles
    assert "viewers" in roles

    # Check URN format
    assert roles["owners"] == [
        "urn:globus:auth:identity:550e8400-e29b-41d4-a716-446655440000"
    ]
    assert roles["administrators"] == [
        "urn:globus:groups:id:660e8400-e29b-41d4-a716-446655440001"
    ]
    assert roles["viewers"] == [
        "urn:globus:auth:identity:770e8400-e29b-41d4-a716-446655440002"
    ]


def test_publish_without_target_alias_publishes_all_targets(
    gra,
    populated_config,
    api_url_patterns,
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API responses for both targets
    created_id_1, created_id_2 = uuid4(), uuid4()
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id_1)},
        status=200,
    )
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id_2)},
        status=200,
    )

    # Act
    gra(["publish", "--yes"], catch_exceptions=False)

    # Assert - both targets were published and written to config
    assert len(responses.calls) == 2
    registered_apis = GRAConfig.load().stages["production"].registered_apis
    assert registered_apis.keys() == {"get-example", "create-example"}


def test_publish_processes_target_from_openapi_spec(
    gra,
    populated_config,
    api_url_patterns,
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response
    created_id = str(uuid4())
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": created_id},
        status=200,
    )

    # Act
    gra(
        ["publish", "--target-alias", "get-example", "--yes"],
        catch_exceptions=False,
    )

    # Assert - request contains target definition from manifest
    request_body = json.loads(responses.calls[0].request.body)
    assert "target" in request_body
    assert "destination" in request_body["target"]
    assert "specification" in request_body["target"]


def test_publish_mixed_create_and_update(
    gra,
    populated_config,
    api_url_patterns,
):
    # Arrange
    # Give first target an ID (will update), leave second without ID (will create)
    existing_id = uuid4()
    registered_apis = populated_config.stages["production"].registered_apis
    registered_apis["get-example"] = RegisteredAPIConfig(registered_api_id=existing_id)
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API responses
    responses.add(
        responses.PATCH,
        api_url_patterns.UPDATE,
        json={"id": str(existing_id)},
        status=200,
    )
    new_id = str(uuid4())
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": new_id},
        status=200,
    )

    # Act
    result = gra(["publish", "--yes"], catch_exceptions=False)

    # Assert - one update and one create
    assert len(responses.calls) == 2
    assert responses.calls[0].request.method == "POST"
    assert responses.calls[1].request.method == "PATCH"

    # Assert - output mentions both operations
    assert "Creating 'create-example'" in result.output
    assert "Updating 'get-example'" in result.output


def test_publish_validates_all_aliases_upfront(gra, populated_config):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Act - provide mix of valid and invalid aliases
    alias_filters = []
    for alias in ("get-example", "invalid-1", "create-example", "invalid-2"):
        alias_filters.extend(["--target-alias", alias])
    result = gra(["publish"] + alias_filters)

    # Assert
    assert result.exit_code != 0
    assert "Invalid target aliases: invalid-1, invalid-2" in result.output
    assert "Allowed Values: create-example, get-example" in result.output


def test_publish_partial_failure_saves_successful_ids(
    gra, populated_config, api_url_patterns
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # First target succeeds, second fails
    created_id = uuid4()
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id)},
        status=200,
    )
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"error": "Server error"},
        status=500,
    )

    # Act
    result = gra(["publish", "--yes"])

    # Assert - should fail overall due to second target error
    assert result.exit_code != 0

    # Assert - first target ID should be saved despite overall failure
    # This validates that config is committed after each successful publish
    assert len(responses.calls) == 2
    registered_apis = GRAConfig.load().stages["production"].registered_apis
    assert registered_apis.keys() == {"create-example"}
    assert registered_apis["create-example"].registered_api_id == created_id


def test_publish_update_excludes_data_templates_when_unspecified(
    gra, populated_config, api_url_patterns
):
    # Arrange
    existing_id = uuid4()
    registered_apis = populated_config.stages["production"].registered_apis
    registered_apis["get-example"] = RegisteredAPIConfig(registered_api_id=existing_id)
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response for update
    responses.add(
        responses.PATCH,
        api_url_patterns.UPDATE,
        json={"id": str(existing_id)},
        status=200,
    )

    # Act - only update the first target by specifying alias
    gra(["publish", "--target-alias", "get-example", "--yes"], catch_exceptions=False)

    # Assert - no data template was imputed in config or request.
    assert populated_config.targets["get-example"].data_templates is None
    assert b'"data_templates":' not in responses.calls[0].request.body


def test_publish_update_includes_data_templates_when_specified(
    gra,
    populated_config,
    api_url_patterns,
):
    # Arrange
    existing_id = uuid4()
    populated_config.targets["get-example"].data_templates = {
        "request": {},
        "response": {"2XX": {}},
    }
    registered_apis = populated_config.stages["production"].registered_apis
    registered_apis["get-example"] = RegisteredAPIConfig(registered_api_id=existing_id)
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response for update
    responses.add(
        responses.PATCH,
        api_url_patterns.UPDATE,
        json={"id": str(existing_id)},
        status=200,
    )

    # Act - only update the first target by specifying alias
    gra(
        ["publish", "--target-alias", "get-example", "--yes"],
        catch_exceptions=False,
    )

    # Assert - the request includes a `data_templates` key.
    assert b'"data_templates": {' in responses.calls[0].request.body
    assert b'"response": {"2XX": {}}' in responses.calls[0].request.body


def test_publish_create_excludes_data_templates_when_unspecified(
    gra, populated_config, api_url_patterns
):
    # Arrange
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response for update
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(uuid4())},
        status=200,
    )

    # Act - only update the first target by specifying alias
    gra(
        ["publish", "--target-alias", "get-example", "--yes"],
        catch_exceptions=False,
    )

    # Assert - no data template was imputed in config or request.
    assert populated_config.targets["get-example"].data_templates is None
    assert b'"data_templates":' not in responses.calls[0].request.body


def test_publish_create_includes_data_templates_when_specified(
    gra, populated_config, api_url_patterns
):
    # Arrange
    populated_config.targets["get-example"].data_templates = {
        "request": {},
        "response": {"2XX": {}},
    }
    populated_config.commit()
    gra(["build"], catch_exceptions=False)

    # Add mock API response for update
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(uuid4())},
        status=200,
    )

    # Act - only update the first target by specifying alias
    gra(
        ["publish", "--target-alias", "get-example", "--yes"],
        catch_exceptions=False,
    )

    # Assert - the request includes a `data_templates` key.
    assert b'"data_templates": {' in responses.calls[0].request.body
    assert b'"response": {"2XX": {}}' in responses.calls[0].request.body
