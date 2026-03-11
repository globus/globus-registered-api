# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import enum
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

import pytest

from globus_registered_api.commands.manage.domain import ManageContext
from globus_registered_api.commands.manage.roles import RoleConfigurator
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig


class Identity(enum.Enum):
    """
    The suite of identities to be "registered" in auth.

    These are patched out in `setup_globus_responses` to be returned by
    mocked `auth.get_identities` calls.
    """

    Alice = "alice@gmail.com"
    Bob = "bob@hotmail.edu"
    Carol = "carol@globus.org"

    def __init__(self, username: str) -> None:
        self.id = uuid4()
        self.username = username
        self.data = {"id": str(self.id), "username": username}

    @classmethod
    def get_identities(cls, ids: list[UUID]) -> dict[str, list[dict[str, str]]]:
        return {"identities": [identity.data for identity in cls if identity.id in ids]}


class Group(enum.Enum):
    """
    The suite of groups to be "registered" in groups.

    These are patched out in `setup_globus_responses` to be returned by mocked
    `groups.get_my_groups` and `search.post_search` calls.
    (Only two are returned by `get_my_groups`)
    """

    Leos = "leos"
    Pisceses = "pisceses"
    Toruses = "toruses"

    def __init__(self, name: str) -> None:
        self.id = uuid4()
        # Note: `name` is a protected attribute of Enum.
        self.gname = name

        self.data = {"id": str(self.id), "name": name}

    @classmethod
    def get_my_groups(cls) -> list[dict[str, str]]:
        return [cls.Leos.data, cls.Pisceses.data]

    @classmethod
    def search_paginated_groups(cls, _: str, query: dict):
        filter_ids = [UUID(gid) for gid in query["filters"][0]["values"]]
        gmeta = [{"entries": [{"content": g.data}]} for g in cls if g.id in filter_ids]
        resp = MagicMock()
        resp.pages.return_value = [{"gmeta": gmeta}]
        return resp


@pytest.fixture(autouse=True)
def setup_globus_responses(mock_auth_client, mock_groups_client, mock_search_client):
    """
    Configure:
      * auth-service -> response from `get_identities`
      * groups-service -> response from `get_my_groups`
      * search-service -> response from `post_search` against the groups index.
    """
    mock_auth_client.get_identities.side_effect = Identity.get_identities
    mock_groups_client.get_my_groups.side_effect = Group.get_my_groups

    mock_search_client.paginated.post_search = Group.search_paginated_groups


@pytest.fixture
def role_configurator(config):
    ctx = ManageContext(config=config, analysis=MagicMock(), globus_app=MagicMock())
    return RoleConfigurator(ctx)


def test_role_management_add_group(prompt_patcher, role_configurator):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", "Group")
    prompt_patcher.add_input("selection", Group.Leos.id)
    prompt_patcher.add_input("selection", "owner")

    # Execute
    role_configurator.add_role()

    # Verify we've added the expected role to the config and committed it.
    expected = RoleConfig(type="group", id=Group.Leos.id, access_level="owner")
    assert RegisteredAPIConfig.load().roles == [expected]


def test_role_management_add_identity(prompt_patcher, role_configurator):
    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", "User")
    prompt_patcher.add_input("click_prompt", Identity.Alice.id)
    prompt_patcher.add_input("confirmation", True)
    prompt_patcher.add_input("selection", "viewer")

    # Execute
    role_configurator.add_role()

    # Verify we've added the expected role to the config and committed it.
    expected = RoleConfig(type="identity", id=Identity.Alice.id, access_level="viewer")
    assert RegisteredAPIConfig.load().roles == [expected]


def test_role_management_add_duplicate_identity_is_rejected(
    prompt_patcher, role_configurator, config, capsys
):
    # Configure a role to be duplicated.
    role = RoleConfig(type="identity", id=Identity.Alice.id, access_level="viewer")
    config.roles = [role]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", "User")
    prompt_patcher.add_input("click_prompt", Identity.Alice.id)
    prompt_patcher.add_input("confirmation", True)

    # Execute
    role_configurator.add_role()

    # Verify that Alice still has viewer access and that we printed a warning.
    expected = RoleConfig(type="identity", id=Identity.Alice.id, access_level="viewer")
    assert RegisteredAPIConfig.load().roles == [expected]

    outstream = capsys.readouterr().out
    assert "use the 'Modify Role' option instead" in outstream


def test_role_management_remove_role(prompt_patcher, role_configurator, config):
    # Configure a role to be removed.
    initial_role = RoleConfig(type="group", id=Group.Pisceses.id, access_level="viewer")
    config.roles = [initial_role]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_input("selection", initial_role)
    prompt_patcher.add_input("confirmation", True)

    # Execute
    role_configurator.remove_role()

    # Verify we've removed the role from the config and committed it.
    assert RegisteredAPIConfig.load().roles == []


def test_role_management_modify_role(prompt_patcher, role_configurator, config):
    # Configure some roles to be displayed.
    leos = RoleConfig(type="group", id=Group.Leos.id, access_level="owner")
    bob = RoleConfig(type="identity", id=Identity.Bob.id, access_level="viewer")
    config.roles = [leos, bob]
    config.commit()

    # Set up a selection to be made by the mocked selector.
    prompt_patcher.add_input("selection", bob)
    prompt_patcher.add_input("selection", "admin")

    # Execute
    role_configurator.modify_role()

    # Verify we've updated the role in the config and committed it.
    old_bob = RoleConfig(type="identity", id=Identity.Bob.id, access_level="viewer")
    expected_bob = RoleConfig(type="identity", id=Identity.Bob.id, access_level="admin")
    committed_roles = RegisteredAPIConfig.load().roles
    assert expected_bob in committed_roles
    assert old_bob not in committed_roles
    assert leos in committed_roles


def test_role_management_list_roles_group_resolution(role_configurator, config, capsys):
    # Configure some roles to be displayed.
    leos = RoleConfig(type="group", id=Group.Leos.id, access_level="owner")
    toruses = RoleConfig(type="group", id=Group.Toruses.id, access_level="viewer")
    other = RoleConfig(type="group", id=uuid4(), access_level="admin")
    config.roles = [leos, toruses, other]
    config.commit()

    # Execute
    role_configurator.list_roles()

    # Verify that known groups were rendered with names and unknown ones with IDs.
    outstream = capsys.readouterr().out
    assert str(other.id) in outstream
    for group in (Group.Leos, Group.Toruses):
        assert group.gname in outstream
        assert str(group.id) not in outstream


def test_role_management_list_roles_identity_resolution(
    role_configurator, config, capsys
):
    # Configure some roles to be displayed.
    alice = RoleConfig(type="identity", id=Identity.Alice.id, access_level="owner")
    other = RoleConfig(type="identity", id=uuid4(), access_level="viewer")
    config.roles = [alice, other]
    config.commit()

    # Execute
    role_configurator.list_roles()

    # Verify that known users were rendered with usernames and unknown ones with IDs.
    outstream = capsys.readouterr().out
    assert str(other.id) in outstream
    assert Identity.Alice.username in outstream
    assert str(Identity.Alice.id) not in outstream
