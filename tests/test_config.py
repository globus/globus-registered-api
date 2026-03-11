# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import UUID

import click
import pytest

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig


def test_load_config(config_path):
    config_dict = {
        "core": {
            "base_url": "https://api.example.com",
            "specification": "https://api.example.com/openapi.json",
        },
        "targets": [],
        "roles": [],
    }
    config_path.parent.mkdir()
    with open(config_path, "w") as f:
        json.dump(config_dict, f, indent=4)

    assert RegisteredAPIConfig.exists()
    config = RegisteredAPIConfig.load()

    assert config.core.base_url == "https://api.example.com"


def test_load_config_when_no_config_exists():
    assert not RegisteredAPIConfig.exists()
    with pytest.raises(click.Abort):
        RegisteredAPIConfig.load()


@pytest.mark.parametrize(
    "first_config,second_config",
    [
        (
            # Path is the highest sort precedence
            TargetConfig(alias="b", path="a", method="POST", description="Test"),
            TargetConfig(alias="a", path="b", method="GET", description="Test"),
        ),
        (
            # Then method
            TargetConfig(alias="b", path="a", method="GET", description="Test"),
            TargetConfig(alias="a", path="a", method="POST", description="Test"),
        ),
        (
            # Then alias
            TargetConfig(alias="a", path="a", method="GET", description="Test"),
            TargetConfig(alias="b", path="a", method="GET", description="Test"),
        ),
    ],
)
def test_target_config_sort_precedence(first_config, second_config):
    configs = [second_config, first_config]
    configs = sorted(configs, key=lambda config: config.sort_key)
    assert configs[0] == first_config
    assert configs[1] == second_config


uuid0 = UUID("00000000-0000-0000-0000-000000000000")
uuid1 = UUID("11111111-1111-1111-1111-111111111111")


@pytest.mark.parametrize(
    "first_config,second_config",
    [
        (
            # Type is the highest sort precedence
            RoleConfig(type="group", id=uuid1, access_level="owner"),
            RoleConfig(type="identity", id=uuid0, access_level="owner"),
        ),
        (
            # Then ID
            RoleConfig(type="group", id=uuid0, access_level="owner"),
            RoleConfig(type="group", id=uuid1, access_level="owner"),
        ),
    ],
)
def test_role_config_sort_precedence(first_config, second_config):
    configs = [second_config, first_config]
    configs = sorted(configs, key=lambda config: config.sort_key)
    assert configs[0] == first_config
    assert configs[1] == second_config


def test_target_config_registered_api_id_defaults_to_none():
    target = TargetConfig(alias="test", path="/test", method="GET", description="Test")
    assert target.registered_api_id is None


def test_target_config_registered_api_id_accepts_uuid():
    test_uuid = UUID("12345678-1234-1234-1234-123456789abc")
    target = TargetConfig(
        alias="test",
        path="/test",
        method="GET",
        description="Test",
        registered_api_id=test_uuid,
    )
    assert target.registered_api_id == test_uuid


def test_target_config_serialization_includes_registered_api_id():
    test_uuid = UUID("12345678-1234-1234-1234-123456789abc")
    target = TargetConfig(
        alias="test",
        path="/test",
        method="GET",
        description="Test",
        registered_api_id=test_uuid,
    )
    serialized = target.model_dump()
    assert serialized["registered_api_id"] == test_uuid


def test_role_config_auth_urn_for_identity():
    identity_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    role = RoleConfig(type="identity", id=identity_id, access_level="owner")
    assert role.auth_urn == f"urn:globus:auth:identity:{identity_id}"


def test_role_config_auth_urn_for_group():
    group_id = UUID("660e8400-e29b-41d4-a716-446655440001")
    role = RoleConfig(type="group", id=group_id, access_level="admin")
    assert role.auth_urn == f"urn:globus:groups:id:{group_id}"


def test_target_config_requires_description():
    target = TargetConfig(
        alias="test", path="/test", method="GET", description="Test endpoint"
    )
    assert target.description == "Test endpoint"
