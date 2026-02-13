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
            TargetConfig(alias="b", path="a", method="POST"),
            TargetConfig(alias="a", path="b", method="GET"),
        ),
        (
            # Then method
            TargetConfig(alias="b", path="a", method="GET"),
            TargetConfig(alias="a", path="a", method="POST"),
        ),
        (
            # Then alias
            TargetConfig(alias="a", path="a", method="GET"),
            TargetConfig(alias="b", path="a", method="GET"),
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
