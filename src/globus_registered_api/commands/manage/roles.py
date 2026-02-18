# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from uuid import UUID

import click
from globus_sdk import AuthClient
from globus_sdk import GlobusApp
from globus_sdk import GroupsClient
from globus_sdk import SearchClient
from rich.console import Console
from rich.table import Table

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.rendering import prompt_selection

from .domain import ManageContext
from .domain import ManageMenuOptions

_GROUPS_SEARCH_INDEX_ID = "fcd4d0ab-f48d-4b13-af61-a5d40832192f"


class RoleSummaryTable(Table):
    _console: t.ClassVar[Console] = Console()

    def __init__(self, roles: list[RoleConfig], *, resolver: _RoleNameResolver) -> None:
        super().__init__()
        self.add_column()
        self.add_column("Entity Type", style="red")
        self.add_column("Identifier", style="magenta")
        self.add_column("Access Level", style="cyan")

        self.resolver = resolver
        self.resolver.populate_cache(roles)

        for idx, role in enumerate(sorted(roles, key=lambda r: r.sort_key)):
            self._populate_role(idx + 1, role)

    def _populate_role(self, idx: int, role: RoleConfig) -> None:
        self.add_row(
            str(idx),
            role.type,
            self.resolver[role] or str(role.id),
            role.access_level,
        )

    def print(self) -> None:
        self._console.print(self)


class RoleConfigurator:

    def __init__(self, context: ManageContext) -> None:
        self.config = context.config
        self._name_resolver = _RoleNameResolver(context.globus_app)
        self._role_selector = _RoleSelector(
            context.config, context.globus_app, self._name_resolver
        )

    @property
    def menu_options(self) -> ManageMenuOptions:
        """The available role management subcommands."""
        return [
            ("List Roles", self.list_roles),
            ("Modify Role", self.modify_role),
            ("Add Role", self.add_role),
            ("Remove Role", self.remove_role),
        ]

    def list_roles(self) -> None:
        table = RoleSummaryTable(self.config.roles, resolver=self._name_resolver)
        table.print()

    def modify_role(self) -> None:
        role = self._role_selector.prompt()

        access_level_options = [
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("viewer", "Viewer"),
        ]
        access_level = prompt_selection(
            "Access Level", access_level_options, default=role.access_level
        )

        role.access_level = access_level
        self.config.commit()

    def add_role(self) -> None:
        role_type, entity_id = self._role_selector.prompt_for_entity()
        if any(
            r for r in self.config.roles if r.type == role_type and r.id == entity_id
        ):
            click.echo("This entity already has a role configured.")
            click.echo("Please use the 'Modify Role' option instead.")
            return

        access_level_options = [
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("viewer", "Viewer"),
        ]
        access_level = prompt_selection("Access Level", options=access_level_options)

        self.config.roles.append(
            RoleConfig(
                type=role_type,
                id=entity_id,
                access_level=access_level,
            )
        )
        self.config.commit()

    def remove_role(self) -> None:
        role = self._role_selector.prompt()
        role_name = self._name_resolver[role] or str(role.id)

        if click.confirm(f"You'd like to remove access from '{role_name}'?"):
            self.config.roles.remove(role)
            self.config.commit()


class _RoleSelector:
    def __init__(
        self,
        config: RegisteredAPIConfig,
        globus_app: GlobusApp,
        resolver: _RoleNameResolver,
    ) -> None:
        self._config = config
        self._resolver = resolver
        self._groups_client = GroupsClient(app=globus_app)

    def prompt(self) -> RoleConfig:
        self._resolver.populate_cache(self._config.roles)

        role_options = [
            (role, f"{self._resolver[role] or role.id} ({role.type})")
            for role in sorted(self._config.roles, key=lambda role: role.sort_key)
        ]
        return prompt_selection("Role", role_options)

    def prompt_for_entity(self) -> tuple[t.Literal["group", "identity"], UUID]:
        role_type_options = [("identity", "User"), ("group", "Group")]
        role_type = prompt_selection("Role Type", options=role_type_options)

        if role_type == "group":
            return "group", self._prompt_for_group_id()
        else:
            return "identity", self._prompt_for_entity_id(role_type)

    def _prompt_for_group_id(self) -> UUID:
        user_groups = sorted(
            self._groups_client.get_my_groups(), key=lambda group: group["name"].lower()
        )
        config_groups = {role.id for role in self._config.roles if role.type == "group"}
        user_groups = filter(lambda g: UUID(g["id"]) not in config_groups, user_groups)

        group_options: list[tuple[UUID | None, str]] = [
            (None, "<Enter a group UUID manually>")
        ] + [(UUID(group["id"]), group["name"]) for group in user_groups]

        selection = prompt_selection("Group", group_options)
        if selection is not None:
            return selection

        return self._prompt_for_entity_id("group")

    def _prompt_for_entity_id(self, role_type: t.Literal["group", "identity"]) -> UUID:
        resolver = self._resolver.get_specific_resolver(role_type)

        while True:
            entity_id = click.prompt(f"{role_type.capitalize()} UUID", type=click.UUID)
            resolved_name = resolver[entity_id]

            if resolved_name is None:
                click.echo("The UUID you provided could not be resolved to a name.")
                if click.confirm("Would you like to proceed anyways?"):
                    return entity_id
            else:
                click.echo(f"The UUID you provided resolved to: '{resolved_name}'")
                if click.confirm("Would you like to proceed?"):
                    return entity_id


class _RoleNameResolver:
    """
    A resolver for role display names.
    """

    def __init__(self, globus_app: GlobusApp) -> None:
        self._group_name_resolver = _GroupNameResolver(globus_app)
        self._identity_name_resolver = _IdentityNameResolver(globus_app)

    def __getitem__(self, role_config: RoleConfig) -> str | None:
        resolver = self.get_specific_resolver(role_config.type)
        return resolver[role_config.id]

    def populate_cache(self, role_configs: list[RoleConfig]) -> None:
        group_ids = [r.id for r in role_configs if r.type == "group"]
        identity_ids = [r.id for r in role_configs if r.type == "identity"]

        self._group_name_resolver.populate_cache(group_ids)
        self._identity_name_resolver.populate_cache(identity_ids)

    def get_specific_resolver(
        self, role_type: t.Literal["identity", "group"]
    ) -> _GroupNameResolver | _IdentityNameResolver:
        if role_type == "group":
            return self._group_name_resolver
        else:
            return self._identity_name_resolver


class _GroupNameResolver:
    """
    A group ID -> name resolver.
    Failures are silently ignored and will return None on resolution attempts.
    """

    def __init__(self, globus_app: GlobusApp) -> None:
        self._search_client = SearchClient(app=globus_app)
        self._name_cache: dict[UUID, str | None] = {}

    def __getitem__(self, group_id: UUID) -> str | None:
        """
        Resolve a group ID to its display name, if possible.

        :returns: The group's display name or None if the name could not be resolved.
        """
        if group_id not in self._name_cache:
            self.populate_cache([group_id])

        return self._name_cache.get(group_id, None)

    def populate_cache(self, group_ids: list[UUID]) -> None:
        """
        Populate the name cache for a list of group IDs.
        This batch operation optimizes the number of API calls needed for a list of
        group IDs.

        Groups will only ever have resolution attempted once. Subsequent attempts will
        silently fail.
        """
        if len(group_ids) == 0:
            return

        search_resp = self._search_client.paginated.post_search(
            _GROUPS_SEARCH_INDEX_ID,
            {
                "filters": [
                    {
                        "type": "match_any",
                        "field_name": "id",
                        "values": [str(gid) for gid in group_ids],
                    }
                ],
            },
        )

        for page in search_resp.pages():
            for result in page["gmeta"]:
                try:
                    group_id = UUID(result["entries"][0]["content"]["id"])
                    group_name = result["entries"][0]["content"]["name"]
                    self._name_cache[group_id] = group_name
                except (KeyError, IndexError):
                    # Malformed Group Index Data
                    continue

        # Mark any IDs we attempted to resolve but didn't.
        for gid in group_ids:
            if gid not in self._name_cache:
                self._name_cache[gid] = None


class _IdentityNameResolver:
    """
    An identity ID -> name resolver.
    Failures are silently ignored and will return None on resolution attempts.
    """

    def __init__(self, globus_app: GlobusApp) -> None:
        self._auth_client = AuthClient(app=globus_app)
        self._name_cache: dict[UUID, str | None] = {}

    def __getitem__(self, identity_id: UUID) -> str | None:
        """
        Resolve an identity ID to its display name, if possible.

        :returns: The identity's display name or None if the name could not be resolved.
        """
        if identity_id not in self._name_cache:
            self.populate_cache([identity_id])

        return self._name_cache[identity_id]

    def populate_cache(self, identity_ids: list[UUID]) -> None:
        """
        Populate the name cache for a list of identity IDs.
        This batch operation optimizes the number of API calls needed for a list of
        identity IDs.

        Identities will only ever have resolution attempted once. Subsequent attempts
        will silently fail.
        """
        if len(identity_ids) == 0:
            return

        resp = self._auth_client.get_identities(ids=identity_ids)

        for identity_info in resp["identities"]:
            try:
                identity_id = UUID(identity_info["id"])
                display_name = identity_info["username"]
                self._name_cache[identity_id] = display_name
            except (KeyError, ValueError):
                # Malformed identity response from auth.
                continue

        for identity_id in identity_ids:
            if identity_id not in self._name_cache:
                self._name_cache[identity_id] = None
