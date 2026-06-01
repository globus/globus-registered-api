# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
from uuid import UUID

import pytest

from globus_registered_api.config import GRAConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.errors import GRACommandLineError


def test_load_config(config_path):
    config_dict = {
        "document_version": "1.0",
        "targets": {},
        "stages": {
            "production": {
                "base_url": "https://api.example.com",
                "specification": "https://api.example.com/openapi.json",
                "subscription_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
                "globus_environment": "production",
                "registered_apis": {},
                "roles": [],
            }
        },
    }
    config_path.parent.mkdir()
    with open(config_path, "w") as f:
        json.dump(config_dict, f, indent=4)

    config = GRAConfig.load()
    assert config.stages["production"].base_url == "https://api.example.com"


def test_load_config_when_no_config_exists():
    GRAConfig.verify_nonexistence()
    with pytest.raises(GRACommandLineError):
        GRAConfig.load()


def test_load_config_when_version_mismatch(config_path):
    config_dict = {
        "document_version": "0.0",
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

    with pytest.raises(GRACommandLineError) as excinfo:
        GRAConfig.load()

    err = excinfo.value
    assert "Out-of-date config version: 0.0" in err.error
    assert "Check GRA's release notes" in err.resolution


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


def test_target_config_data_templates_defaults_to_none():
    target = TargetConfig(path="/test", method="GET", description="Test")
    assert target.data_templates is None


def test_target_config_serialization_includes_data_templates_if_set():
    data_templates = {"requests": {}, "responses": {"2XX": {}}}
    target = TargetConfig(
        path="/test",
        method="GET",
        description="Test",
        data_templates=data_templates,
    )
    serialized = target.model_dump()
    assert serialized["data_templates"] == data_templates


def test_target_config_serialization_excludes_data_templates_if_unset():
    target = TargetConfig(
        path="/test",
        method="GET",
        description="Test",
    )
    serialized = target.model_dump()
    assert "data_templates" not in serialized


def test_role_config_auth_urn_for_identity():
    identity_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    role = RoleConfig(type="identity", id=identity_id, access_level="owner")
    assert role.auth_urn == f"urn:globus:auth:identity:{identity_id}"


def test_role_config_auth_urn_for_group():
    group_id = UUID("660e8400-e29b-41d4-a716-446655440001")
    role = RoleConfig(type="group", id=group_id, access_level="admin")
    assert role.auth_urn == f"urn:globus:groups:id:{group_id}"


def test_target_config_requires_description():
    target = TargetConfig(path="/test", method="GET", description="My Endpoint")
    assert target.description == "My Endpoint"
