# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import typing as t
from pathlib import Path
from uuid import UUID

import click
import openapi_pydantic as oa
from pydantic import BaseModel
from pydantic import Field

from globus_registered_api.domain import HTTPMethod
from globus_registered_api.domain import TargetSpecifier

_CONFIG_PATH = Path(".registered_api/config.json")


class RegisteredAPIConfig(BaseModel):
    # Central config, supplied at repository initialization time.
    core: CoreConfig

    # A list of target configurations.
    # A target defines maps onto a Registered API to be synchronized via publish.
    targets: list[TargetConfig]

    # A list of roles, defining access control for identities and groups.
    # Entities within this list must be unique (w.r.t their type and id).
    roles: list[RoleConfig]

    def commit(self) -> None:
        """
        Write the current config state to disk.
        """
        _CONFIG_PATH.parent.mkdir(exist_ok=True)
        _CONFIG_PATH.write_text(self.model_dump_json(indent=4))

    @classmethod
    def load(cls) -> RegisteredAPIConfig:
        """
        Read the config from disk, loading it into a RegisteredAPIConfig instance.

        :raises click.Abort: if no config file exists.
        :raises ValidationError: if the config data is malformed in some way.
        """
        if not cls.exists():
            click.echo("Error: Missing repository config file.")
            click.echo("Run 'globus-registered-api init' first to create a repository.")
            raise click.Abort()

        with open(_CONFIG_PATH) as f:
            return cls.model_validate_json(f.read())

    @classmethod
    def exists(cls) -> bool:
        """
        :return: True if a config file exists on disk, False otherwise.
        """
        return os.path.exists(_CONFIG_PATH)


class CoreConfig(BaseModel):
    """
    A core config entry containing top-level service information.
    """

    # The common prefix URL for all API targets.
    base_url: str

    # The OpenAPI specification for this repository.
    # This must be either an inline OpenAPI document or a file path/URL pointing to one.
    specification: str | oa.OpenAPI


class TargetConfig(BaseModel):
    """
    A configuration entry for a single target within a Registered API service.
    """

    # A relative API path string (e.g., /resource/{id}/action).
    # This will be appended to the core.base_url to form the full target URL.
    path: str

    # The HTTP method for this target.
    method: HTTPMethod

    # A persistent human-readable name for the target.
    # E.g., create-resource
    alias: str

    # The list of globus-auth scope strings which independently consent to this target.
    scope_strings: list[str] = Field(default_factory=list)

    @property
    def sort_key(self) -> str:
        # Sort by alias, then method and path for consistent ordering.
        return f"{self.path}:{self.method}:{self.alias}"

    @property
    def specifier(self) -> TargetSpecifier:
        return TargetSpecifier.create(self.method, self.path)

    def __str__(self) -> str:
        return f"{self.alias} ({self.method} {self.path})"


class RoleConfig(BaseModel):
    """
    A configuration entry for a single identity or group.
    """

    # The type of entity this role identifies.
    #   'identity' refers to an entity as recognized by Globus Auth service.
    #   'group' refers to a group managed in the Globus Groups service.
    type: t.Literal["identity", "group"]

    # The UUID of the identity or group.
    id: UUID

    # The degree of permission granted to this entity.
    access_level: t.Literal["owner", "admin", "viewer"]

    @property
    def sort_key(self) -> str:
        # Sort by type, then id for consistent ordering.
        return f"{self.type}:{self.id}"
