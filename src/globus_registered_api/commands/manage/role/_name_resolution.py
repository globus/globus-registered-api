# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from globus_registered_api.config import RoleConfig
from globus_registered_api.repositories.groups import GroupRepository
from globus_registered_api.repositories.identities import IdentityRepository


class RoleNameResolver:
    """
    An ID -> display name resolver.

    Usage:
        resolver = RoleNameResolver()
        display_name = resolver.resolve_display_name(role_config)

    Unresolvable IDs fail silently (returning None).

    Group display names are sourced from the groups-maintained search index.
    Identity usernames are sourced from the auth service.
    """

    def __init__(self) -> None:
        self._group_repository = GroupRepository.instance()
        self._identity_repository = IdentityRepository.instance()

    def resolve_display_name(self, role: RoleConfig | tuple[str, str]) -> str:
        """
        Resolve the display name for a given RoleConfig.

        :param role: A role, either in the form of a RoleConfig or a tuple of
            (role_type, role_id).
        """
        if isinstance(role, RoleConfig):
            role_type, role_id = role.type, str(role.id)
        else:
            role_type, role_id = role

        if role_type == "group":
            return self._group_names([role_id])[role_id]
        else:
            return self._identity_names([role_id])[role_id]

    def batch_resolve_display_names(
        self, role_configs: list[RoleConfig]
    ) -> dict[str, str]:
        identity_ids = [str(i.id) for i in role_configs if i.type == "identity"]
        group_ids = [str(g.id) for g in role_configs if g.type == "group"]

        return {
            **self._identity_names(identity_ids),
            **self._group_names(group_ids),
        }

    def _identity_names(self, identity_ids: list[str]) -> dict[str, str]:
        identity_names = {}
        identities = self._identity_repository.batch_get_identities(identity_ids)
        for identity_id, identity in identities.items():
            if identity:
                identity_names[identity_id] = identity.username
            else:
                identity_names[identity_id] = f"{identity_id} (Identity)"
        return identity_names

    def _group_names(self, group_ids: list[str]) -> dict[str, str]:
        group_names = {}
        groups = self._group_repository.batch_get_groups(group_ids)
        for group_id, group in groups.items():
            if group:
                group_names[group_id] = group.name
            else:
                group_names[group_id] = f"{group_id} (Group)"
        return group_names
