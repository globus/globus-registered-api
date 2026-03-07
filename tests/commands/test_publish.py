# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

import openapi_pydantic as oa
import pytest
import responses

import globus_registered_api.manifest as manifest_module
from globus_registered_api.config import CoreConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.manifest import ComputedRegisteredAPI
from globus_registered_api.manifest import RegisteredAPIManifest
from globus_registered_api.openapi.reducer import OpenAPITarget


@pytest.fixture(autouse=True)
def manifest_path(monkeypatch, tmp_path):
    new_path = tmp_path / ".globus_registered_api" / "manifest.json"
    monkeypatch.setattr(manifest_module, "_MANIFEST_PATH", new_path)
    yield new_path


@pytest.fixture
def config_with_targets_and_roles(openapi_schema):
    core = CoreConfig(
        base_url="https://api.example.com",
        specification=openapi_schema,
    )
    targets = [
        TargetConfig(
            path="/example",
            method="GET",
            alias="get-example",
            description="Get example resource",
        ),
        TargetConfig(
            path="/example",
            method="POST",
            alias="create-example",
            description="Create example resource",
        ),
    ]
    roles = [
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
    return RegisteredAPIConfig(core=core, targets=targets, roles=roles)


@pytest.fixture
def manifest_for_config(config_with_targets_and_roles, manifest_path):
    # Create a manifest that matches the config targets
    registered_apis = {}
    for target in config_with_targets_and_roles.targets:
        operation = oa.Operation(
            summary=f"Example {target.method} endpoint",
            responses={"200": oa.Response(description="Success")},
        )
        api_target = OpenAPITarget(
            operation=operation,
            destination={
                "url": target.path,
                "method": target.method.lower(),
            },
        )
        registered_apis[target.alias] = ComputedRegisteredAPI(
            target=api_target, description=target.description
        )

    manifest = RegisteredAPIManifest(
        build_timestamp=datetime.now(timezone.utc),
        registered_apis=registered_apis,
    )
    manifest.commit()
    return manifest


def test_publish_command_exists(gra):
    # Act
    result = gra(["publish", "--help"])

    # Assert
    assert result.exit_code == 0
    assert "Publish registered APIs to Flows service" in result.output


def test_publish_raises_error_when_config_missing(gra):
    # Act
    result = gra(["publish"])

    # Assert
    assert result.exit_code != 0
    assert "Error: Missing repository config file." in result.output


def test_publish_raises_error_when_manifest_missing(gra, config):
    # Arrange
    config.commit()

    # Act
    result = gra(["publish"])

    # Assert
    assert result.exit_code != 0
    assert "Error: Missing repository manifest file." in result.output
    assert "Run 'gra build' first to generate a manifest." in result.output


def test_publish_creates_new_registered_api_when_no_id_exists(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Assert -  No ID exists before publishing
    assert config_with_targets_and_roles.targets[0].registered_api_id is None

    # Add mock API response for create
    created_id = uuid4()
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id)},
        status=200,
    )

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(["publish"])

    # Assert
    assert result.exit_code == 0

    # Assert - ID was written back to config
    updated_config = RegisteredAPIConfig.load()
    assert updated_config.targets[0].registered_api_id == created_id


def test_publish_updates_existing_registered_api_when_id_exists(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    existing_id = uuid4()
    config_with_targets_and_roles.targets[0].registered_api_id = existing_id
    config_with_targets_and_roles.commit()

    # Add mock API response for update
    responses.add(
        responses.PATCH,
        api_url_patterns.UPDATE,
        json={"id": str(existing_id)},
        status=200,
    )

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act - only update the first target by specifying alias
    result = gra(["publish", "--target-alias", "get-example"])

    # Assert
    assert result.exit_code == 0

    # Assert - ID is unchanged (update doesn't change the ID)
    updated_config = RegisteredAPIConfig.load()
    assert updated_config.targets[0].registered_api_id == existing_id


def test_publish_with_target_alias_filters_targets(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Add mock API response for create (only one target should be published)
    created_id = uuid4()
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": str(created_id)},
        status=200,
    )

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(["publish", "--target-alias", "get-example"])

    # Assert
    assert result.exit_code == 0

    # Verify only one target was published
    assert len(responses.calls) == 1

    # Verify only the selected target got an ID
    updated_config = RegisteredAPIConfig.load()
    assert updated_config.targets[0].registered_api_id == created_id
    assert updated_config.targets[1].registered_api_id is None


def test_publish_with_multiple_target_aliases(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Add mock API responses for create
    created_id_1 = uuid4()
    created_id_2 = uuid4()
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

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(
        ["publish", "--target-alias", "get-example", "--target-alias", "create-example"]
    )

    # Assert
    assert result.exit_code == 0

    # Assert - both targets were published
    assert len(responses.calls) == 2

    # Assert - both targets got IDs
    updated_config = RegisteredAPIConfig.load()
    assert updated_config.targets[0].registered_api_id == created_id_1
    assert updated_config.targets[1].registered_api_id == created_id_2


def test_publish_raises_error_when_target_alias_not_found(
    gra, config_with_targets_and_roles, manifest_for_config
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Act
    result = gra(["publish", "--target-alias", "nonexistent-target"])

    # Assert
    assert result.exit_code != 0
    assert "Error: The following target aliases are not configured:" in result.output
    assert "  - nonexistent-target" in result.output


def test_publish_skips_confirmation_with_yes_flag(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Add mock API response
    created_id = str(uuid4())
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": created_id},
        status=200,
    )

    # Act
    result = gra(["publish", "--yes"])

    # Assert - no api calls made
    assert result.exit_code == 0
    assert len(responses.calls) > 0


def test_publish_aborts_when_user_declines_confirmation(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

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
    updated_config = RegisteredAPIConfig.load()
    assert updated_config.targets[0].registered_api_id is None
    assert updated_config.targets[1].registered_api_id is None


def test_publish_passes_correct_roles_to_api(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Add mock API response
    created_id = str(uuid4())
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": created_id},
        status=200,
    )

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(["publish", "--target-alias", "get-example", "--yes"])

    # Assert
    assert result.exit_code == 0
    assert len(responses.calls) == 1

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
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Add mock API responses for both targets
    created_id_1 = uuid4()
    created_id_2 = uuid4()
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

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(["publish"])

    # Assert
    assert result.exit_code == 0

    # Assert - both targets were published
    assert len(responses.calls) == 2

    # Assert - IDs were written back to config
    updated_config = RegisteredAPIConfig.load()
    assert updated_config.targets[0].registered_api_id == created_id_1
    assert updated_config.targets[1].registered_api_id == created_id_2


def test_publish_processes_target_from_openapi_spec(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Add mock API response
    created_id = str(uuid4())
    responses.add(
        responses.POST,
        api_url_patterns.CREATE,
        json={"id": created_id},
        status=200,
    )

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(["publish", "--target-alias", "get-example", "--yes"])

    # Assert
    assert result.exit_code == 0

    # Assert - request contains target definition from manifest
    request_body = json.loads(responses.calls[0].request.body)
    assert "target" in request_body
    assert "destination" in request_body["target"]
    assert "specification" in request_body["target"]


def test_publish_mixed_create_and_update(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    # Give first target an ID (will update), leave second without ID (will create)
    existing_id = uuid4()
    config_with_targets_and_roles.targets[0].registered_api_id = existing_id
    config_with_targets_and_roles.commit()

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

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(["publish", "--yes"])

    # Assert
    assert result.exit_code == 0

    # Assert - one update and one create
    assert len(responses.calls) == 2
    assert responses.calls[0].request.method == "PATCH"
    assert responses.calls[1].request.method == "POST"

    # Assert - output mentions both operations
    assert "Updating registered API for get-example" in result.output
    assert "Creating registered API for create-example" in result.output


def test_publish_validates_all_aliases_upfront(
    gra, config_with_targets_and_roles, manifest_for_config
):
    # Arrange
    config_with_targets_and_roles.commit()

    # Act - provide mix of valid and invalid aliases
    result = gra(
        [
            "publish",
            "--target-alias",
            "get-example",
            "--target-alias",
            "invalid-1",
            "--target-alias",
            "create-example",
            "--target-alias",
            "invalid-2",
        ]
    )

    # Assert
    assert result.exit_code != 0
    assert "Error: The following target aliases are not configured:" in result.output
    # Both invalid aliases should be mentioned
    assert "  - invalid-1" in result.output
    assert "  - invalid-2" in result.output


def test_publish_partial_failure_saves_successful_ids(
    gra,
    config_with_targets_and_roles,
    manifest_for_config,
    api_url_patterns,
    prompt_patcher,
):
    # Arrange
    config_with_targets_and_roles.commit()

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

    # Skip confirmation prompt
    prompt_patcher.add_input("confirmation", True)

    # Act
    result = gra(["publish", "--yes"])

    # Assert - should fail overall due to second target error
    assert result.exit_code != 0

    # Assert - first target ID should be saved despite overall failure
    # This validates that config is committed after each successful publish
    updated_config = RegisteredAPIConfig.load()
    assert updated_config.targets[0].registered_api_id == created_id
    assert updated_config.targets[1].registered_api_id is None
