# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from pathlib import Path
from uuid import UUID

import click
import openapi_pydantic as oa
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from globus_registered_api.domain import HTTPMethod
from globus_registered_api.domain import TargetSpecifier

_CONFIG_PATH = Path(".globus_registered_api/config.json")


_CURRENT_VERSION = "0.1"


class RegisteredAPIConfig(BaseModel):
    document_version: str = Field(default=_CURRENT_VERSION)

    # Central config, supplied at repository initialization time.
    core: CoreConfig

    # A list of target configurations.
    # A target defines maps onto a Registered API to be synchronized via publish.
    targets: list[TargetConfig]

    # A list of roles, defining access control for identities and groups.
    # Entities within this list must be unique (w.r.t their type and id).
    roles: list[RoleConfig]

    @field_validator("document_version", mode="before")
    def validate_document_version(cls, v: t.Any) -> t.Any:
        if isinstance(v, str) and v != _CURRENT_VERSION:
            click.secho(f"Error: Out-of-date config version: {v}.", fg="red", err=True)
            click.secho(
                f"       Required version: {_CURRENT_VERSION}.", fg="red", err=True
            )
            click.secho(
                "Please check the release notes for upgrade instructions.",
                fg="yellow",
                err=True,
            )
            raise click.Abort()
        return v

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
            click.echo("Run 'gra init' first to create a repository.")
            raise click.Abort()

        return cls.model_validate_json(_CONFIG_PATH.read_text())

    @classmethod
    def exists(cls) -> bool:
        """
        :return: True if a config file exists on disk, False otherwise.
        """
        return _CONFIG_PATH.is_file()


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

    class Security(BaseModel):
        globus_auth_scope: str | None = None

    # A relative API path string (e.g., /resource/{id}/action).
    # This will be appended to the core.base_url to form the full target URL.
    path: str

    # The HTTP method for this target.
    method: HTTPMethod

    # A persistent human-readable name for the target.
    # E.g., create-resource
    alias: str

    # Human-readable description of what this target does.
    description: str

    # Additional security configuration to be mixed in with an OpenAPI specification.
    security: Security = Field(default_factory=Security)

    # The UUID of the registered API in Flows service, if published.
    registered_api_id: UUID | None = None

    @property
    def sort_key(self) -> tuple[str, ...]:
        # Sort by path then method, disambiguating duplicate targets by alias.
        return self.path, self.method, self.alias

    @property
    def specifier(self) -> TargetSpecifier:
        return TargetSpecifier.create(self.method, self.path)

    def __str__(self) -> str:
        return f"{self.alias} ({self.method} {self.path})"


RoleAccessLevel = t.Literal["owner", "admin", "viewer"]


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
    access_level: RoleAccessLevel

    @property
    def sort_key(self) -> tuple[str, ...]:
        # Sort by type, then id for consistent ordering.
        return self.type, str(self.id)

    @property
    def auth_urn(self) -> str:
        """
        Convert role configuration to Flows API URN format.

        :return: URN string for the role
        """
        if self.type == "group":
            return f"urn:globus:groups:id:{self.id}"
        else:  # identity
            return f"urn:globus:auth:identity:{self.id}"
