# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from uuid import UUID

import click
from globus_sdk import GlobusApp
from rich.console import Console
from rich.table import Table

from globus_registered_api.clients import create_auth_client
from globus_registered_api.clients import create_groups_client
from globus_registered_api.clients import create_search_client
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleAccessLevel
from globus_registered_api.config import RoleConfig
from globus_registered_api.rendering import prompt_selection

from .domain import ConfiguratorMenu
from .domain import ManageContext

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

        for role in sorted(roles, key=lambda r: r.sort_key):
            self.add_row(
                str(self.row_count + 1),
                role.type,
                self.resolver.resolve(role) or str(role.id),
                role.access_level,
            )

    def print(self) -> None:
        self._console.print(self)


class RoleConfigurator:
    """
    Central management pane of role configuration.

    Each method corresponds to a subcommand of `gra manage` related to role management.
    """

    def __init__(self, context: ManageContext) -> None:
        self.config = context.config
        self._name_resolver = _RoleNameResolver(context.globus_app)
        self._role_prompter = _RolePrompter(
            context.config, context.globus_app, self._name_resolver
        )

    @property
    def menu_options(self) -> ConfiguratorMenu:
        """The available role management subcommands."""
        return [
            (self.list_roles, "List Roles"),
            (self.modify_role, "Modify Role"),
            (self.add_role, "Add Role"),
            (self.remove_role, "Remove Role"),
        ]

    def list_roles(self) -> None:
        """Display a summary table of all configured roles."""
        table = RoleSummaryTable(self.config.roles, resolver=self._name_resolver)
        table.print()

    def modify_role(self) -> None:
        """Modify a configured role's access level."""
        role = self._role_prompter.prompt_for_config()

        access_level_options: list[tuple[RoleAccessLevel, str]] = [
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("viewer", "Viewer"),
        ]
        access_level = prompt_selection(
            "Access Level", access_level_options, default=role.access_level
        )

        role.access_level = access_level
        self.config.roles.sort(key=lambda r: r.sort_key)
        self.config.commit()

    def add_role(self) -> None:
        """Add a new role to the configuration."""
        role_type, entity_id = self._role_prompter.prompt_for_entity()
        existing_roles = {(r.type, r.id) for r in self.config.roles}
        if (role_type, entity_id) in existing_roles:
            click.echo("This entity already has a role configured.")
            click.echo("Please use the 'Modify Role' option instead.")
            return

        access_level_options: list[tuple[RoleAccessLevel, str]] = [
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("viewer", "Viewer"),
        ]
        access_level = prompt_selection("Access Level", options=access_level_options)

        new_role = RoleConfig(type=role_type, id=entity_id, access_level=access_level)
        self.config.roles.append(new_role)
        self.config.roles.sort(key=lambda r: r.sort_key)
        self.config.commit()

    def remove_role(self) -> None:
        """Remove a role from the configuration."""
        role = self._role_prompter.prompt_for_config()
        role_name = self._name_resolver.resolve(role) or str(role.id)

        if click.confirm(f"You'd like to remove access from '{role_name}'?"):
            self.config.roles.remove(role)
            self.config.commit()


class _RolePrompter:
    """
    Common and/or complex user prompting logic for role management subcommands.
    """

    def __init__(
        self,
        config: RegisteredAPIConfig,
        globus_app: GlobusApp,
        resolver: _RoleNameResolver,
    ) -> None:
        self._config = config
        self._resolver = resolver
        self._groups_client = create_groups_client(globus_app)

    def prompt_for_config(self) -> RoleConfig:
        """
        Prompt the user to select an already-configured RoleConfig object.
        """

        self._resolver.populate_cache(self._config.roles)

        role_options = [
            (role, f"{self._resolver.resolve(role) or role.id} ({role.type})")
            for role in sorted(self._config.roles, key=lambda role: role.sort_key)
        ]
        return prompt_selection("Role", role_options)

    def prompt_for_entity(self) -> tuple[t.Literal["group", "identity"], UUID]:
        """
        Prompt the user to select an unconfigured entity.
        """

        role_type_options = [("identity", "User"), ("group", "Group")]
        role_type = prompt_selection("Role Type", options=role_type_options)

        if role_type == "group":
            return "group", self._prompt_for_group_id()
        elif role_type == "identity":
            return "identity", self._prompt_for_entity_id("identity")
        raise RuntimeError(f"Unrecognized role type: {role_type}")

    def _prompt_for_group_id(self) -> UUID:
        """
        Prompt the user to select a group from a list of groups which they are both
          1. currently a member of
          2. have not already configured a role for.

        Additionally, they may choose to enter a UUID manually.
        :return: A group UUID.
        """

        config_ids = {role.id for role in self._config.roles if role.type == "group"}
        groups_resp = self._groups_client.get_my_groups()

        # Process the groups response into a list of known_group options.
        known_group_options: list[tuple[UUID, str]] = [
            (UUID(group["id"]), group["name"])
            for group in groups_resp
            if UUID(group["id"]) not in config_ids
        ]
        known_group_options.sort(key=lambda g: g[1].lower())

        # Prepend an option to manually enter a Group ID.
        group_options = [(None, "<Enter a group UUID manually>")] + known_group_options

        selection = prompt_selection("Group", group_options)
        if selection is not None:
            return selection

        return self._prompt_for_entity_id("group")

    def _prompt_for_entity_id(self, role_type: t.Literal["group", "identity"]) -> UUID:
        """
        Prompt the user to enter a UUID for the specified role type.

        :return: A UUID of the specified role type.
        """
        resolver = self._resolver.get_specific_resolver(role_type)

        while True:
            prompt_msg = f"{role_type.capitalize()} UUID"
            entity_id: UUID = click.prompt(prompt_msg, type=click.UUID)
            resolved_name = resolver.resolve(entity_id)

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
    An ID -> display name resolver.

    Usage:
        resolver = _RoleNameResolver(globus_app)
        display_name = resolver.resolve(role_config)

    A `populate_cache` method if provided to facilitate batch resolution.
    Unresolvable IDs fail silently (returning None).

    Groups display names are sourced from the groups-maintained search index.
    Identity usernames are sourced from the auth service.
    """

    def __init__(self, globus_app: GlobusApp) -> None:
        self._group_name_resolver = _GroupNameResolver(globus_app)
        self._identity_name_resolver = _IdentityNameResolver(globus_app)

    def resolve(self, role_config: RoleConfig) -> str | None:
        resolver = self.get_specific_resolver(role_config.type)
        return resolver.resolve(role_config.id)

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
        self._search_client = create_search_client(globus_app)
        self._name_cache: dict[UUID, str | None] = {}

    def resolve(self, group_id: UUID) -> str | None:
        """
        Resolve a group ID to its display name, if possible.

        :returns: The group's display name or None if the name could not be resolved.
        """
        if group_id not in self._name_cache:
            self.populate_cache([group_id])

        return self._name_cache[group_id]

    def populate_cache(self, group_ids: list[UUID]) -> None:
        """
        Populate the name cache for a list of group IDs.
        This batch operation optimizes the number of API calls needed for a list of
        group IDs.

        Groups will only ever have resolution attempted once. Subsequent attempts will
        silently fail.
        """
        group_ids = [gid for gid in group_ids if gid not in self._name_cache]
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
    An identity ID -> username resolver.
    Failures are silently ignored and will return None on resolution attempts.
    """

    def __init__(self, globus_app: GlobusApp) -> None:
        self._auth_client = create_auth_client(globus_app)
        self._name_cache: dict[UUID, str | None] = {}

    def resolve(self, identity_id: UUID) -> str | None:
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
        identity_ids = [iid for iid in identity_ids if iid not in self._name_cache]
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
