# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from uuid import uuid4

import pytest

from globus_registered_api.commands.manage.role._name_resolution import RoleNameResolver
from globus_registered_api.config import GRAConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.repositories.clients import GlobusClientRepository
from globus_registered_api.repositories.groups import Group
from globus_registered_api.repositories.groups import GroupRepository
from globus_registered_api.repositories.identities import Identity
from globus_registered_api.repositories.identities import IdentityRepository


@pytest.fixture(autouse=True)
def patch_identity_repository(monkeypatch):
    repository = IdentityRepository.instance()
    globus = GlobusClientRepository.instance()
    identity_cache = repository._identity_cache[globus.cache_key]

    for identity in (IDENTITIES.Alice, IDENTITIES.Bob, IDENTITIES.Carol):
        identity_cache[identity.id] = identity


@pytest.fixture(autouse=True)
def patch_group_repository(monkeypatch):
    repository = GroupRepository.instance()
    globus = GlobusClientRepository.instance()
    group_cache = repository._group_cache[globus.cache_key]
    active_cache = repository._active_cache

    for group in (GROUPS.Leos, GROUPS.Pisceses, GROUPS.Toruses):
        group_cache[group.id] = group

    active_cache[globus.cache_key] = [GROUPS.Leos, GROUPS.Pisceses]


# The suite of identities & groups to be cached in auth & group repositories.
IDENTITIES = SimpleNamespace(
    Alice=Identity(str(uuid4()), "alice@gmail.com"),
    Bob=Identity(str(uuid4()), "bob@hotmail.edu"),
    Carol=Identity(str(uuid4()), "carol@globus.org"),
)
GROUPS = SimpleNamespace(
    Leos=Group(str(uuid4()), "Leos"),
    Pisceses=Group(str(uuid4()), "Pisceses"),
    Toruses=Group(str(uuid4()), "Toruses"),
)


def test_role_management_add_group(prompt_patcher, config, gra):
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Roles")
    prompt_patcher.add_selection("<Register a New Role>")

    prompt_patcher.add_selection("Select Group")
    prompt_patcher.add_selection(GROUPS.Leos.name)

    prompt_patcher.add_selection("Set Access Level")
    prompt_patcher.add_selection("Admin")

    prompt_patcher.add_selection("<Submit>")
    prompt_patcher.add_selection("<Exit>")

    gra(["manage"], catch_exceptions=False)

    # Verify we've added the expected role to the config and committed it.
    expected = RoleConfig(type="group", id=GROUPS.Leos.id, access_level="admin")
    assert GRAConfig.load().stages["production"].roles == [expected]


def test_role_management_add_identity(prompt_patcher, config, gra):
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Roles")
    prompt_patcher.add_selection("<Register a New Role>")

    prompt_patcher.add_selection("Change Role Type")
    prompt_patcher.add_selection("Identity")
    prompt_patcher.add_selection("Select Identity")
    prompt_patcher.add_input("click_prompt", IDENTITIES.Alice.id)

    prompt_patcher.add_selection("Set Access Level")
    prompt_patcher.add_selection("Admin")

    prompt_patcher.add_selection("<Submit>")
    prompt_patcher.add_selection("<Exit>")

    gra(["manage"], catch_exceptions=False)

    # Verify we've added the expected role to the config and committed it.
    expected = RoleConfig(type="identity", id=IDENTITIES.Alice.id, access_level="admin")
    assert GRAConfig.load().stages["production"].roles == [expected]


def test_role_management_add_duplicate_identity_is_rejected(
    prompt_patcher, config, gra, capsys
):
    # TODO - this is no longer the case, maybe change src?

    # Configure a role to be duplicated.
    role = RoleConfig(type="identity", id=IDENTITIES.Alice.id, access_level="viewer")
    config.stages["production"].roles = [role]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Roles")
    prompt_patcher.add_selection("<Register a New Role>")

    prompt_patcher.add_selection("Change Role Type")
    prompt_patcher.add_selection("Identity")
    prompt_patcher.add_selection("Select Identity")
    prompt_patcher.add_input("click_prompt", IDENTITIES.Alice.id)

    prompt_patcher.add_selection("Set Access Level")
    prompt_patcher.add_selection("Admin")

    prompt_patcher.add_selection("<Submit>")
    prompt_patcher.add_selection("<Exit>")

    # Execute
    gra(["manage"], catch_exceptions=False)

    # Verify that Alice still has viewer access and that we printed a warning.
    expected = RoleConfig(
        type="identity", id=IDENTITIES.Alice.id, access_level="viewer"
    )
    assert GRAConfig.load().stages["production"].roles == [expected]

    outstream = capsys.readouterr().out
    assert "use the 'Modify Role' option instead" in outstream


def test_role_management_remove_role(prompt_patcher, config, gra):
    # Configure a role to be removed.
    initial_role = RoleConfig(
        type="group", id=GROUPS.Pisceses.id, access_level="viewer"
    )
    config.stages["production"].roles = [initial_role]
    config.commit()

    # Set up a sequence of selections to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Roles")
    prompt_patcher.add_selection(f"Manage '{GROUPS.Pisceses.name}'")
    prompt_patcher.add_selection("Remove Role")
    prompt_patcher.add_input("confirmation", True)
    prompt_patcher.add_selection("<Exit>")

    # Execute
    gra(["manage"], catch_exceptions=False)

    # Verify we've removed the role from the config and committed it.
    assert GRAConfig.load().stages["production"].roles == []


def test_role_management_modify_access_level(prompt_patcher, config, gra):
    # Configure some roles to be displayed.
    leos = RoleConfig(type="group", id=GROUPS.Leos.id, access_level="owner")
    bob = RoleConfig(type="identity", id=IDENTITIES.Bob.id, access_level="viewer")
    config.stages["production"].roles = [leos, bob]
    config.commit()

    # Set up a selection to be made by the mocked selector.
    prompt_patcher.add_selection("Manage Roles")
    prompt_patcher.add_selection(f"Manage '{IDENTITIES.Bob.username}'")
    prompt_patcher.add_selection("Modify Access Level")
    prompt_patcher.add_selection("Admin")
    prompt_patcher.add_selection("<Exit>")

    # Execute
    gra(["manage"], catch_exceptions=False)

    # Verify we've updated the role in the config and committed it.
    old_bob = RoleConfig(type="identity", id=IDENTITIES.Bob.id, access_level="viewer")
    expected_bob = RoleConfig(
        type="identity", id=IDENTITIES.Bob.id, access_level="admin"
    )
    committed_roles = GRAConfig.load().stages["production"].roles
    assert expected_bob in committed_roles
    assert old_bob not in committed_roles
    assert leos in committed_roles


_RANDOM_UUID = uuid4()


@pytest.mark.parametrize(
    "role_type,role_id,expected",
    (
        # Known Identities
        ("identity", IDENTITIES.Alice.id, IDENTITIES.Alice.username),
        ("identity", IDENTITIES.Bob.id, IDENTITIES.Bob.username),
        # Known Groups
        ("group", GROUPS.Pisceses.id, GROUPS.Pisceses.name),
        ("group", GROUPS.Leos.id, GROUPS.Leos.name),
        # Unknown Entities
        ("identity", _RANDOM_UUID, f"{_RANDOM_UUID} (Identity)"),
        ("group", _RANDOM_UUID, f"{_RANDOM_UUID} (Group)"),
    ),
)
def test_role_management_name_resolution(
    role_type, role_id, expected, prompt_patcher, config
):
    resolver = RoleNameResolver()
    assert resolver.resolve_display_name((role_type, str(role_id))) == expected
