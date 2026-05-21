# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from pathlib import Path
from uuid import UUID

import pydantic
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from globus_registered_api.domain import HTTPMethod
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.errors import GRACommandLineError

_CONFIG_PATH = Path(".globus_registered_api/config.json")


_CURRENT_VERSION = "1.0"

GlobusEnvironment: t.TypeAlias = t.Literal[
    "sandbox", "integration", "test", "preview", "staging", "production"
]
GLOBUS_ENVIRONMENTS: list[GlobusEnvironment] = [
    "sandbox",
    "integration",
    "test",
    "preview",
    "staging",
    "production",
]

RoleType: t.TypeAlias = t.Literal["identity", "group"]
ROLE_TYPES: list[RoleType] = ["identity", "group"]

RoleAccessLevel = t.Literal["owner", "admin", "viewer"]
ROLE_ACCESS_LEVELS: list[RoleAccessLevel] = ["owner", "admin", "viewer"]


class GRAConfig(BaseModel):
    document_version: str = Field(default=_CURRENT_VERSION)

    # Target Configurations, indexed by a customer-defined "target alias" key.
    # Each element configures a single api route (method + path).
    targets: dict[str, TargetConfig] = Field(default_factory=dict)

    # Stage Configurations, indexed by a customer-defined "stage" key.
    stages: dict[str, StageConfig] = Field(default_factory=dict)

    @field_validator("document_version", mode="before")
    def validate_document_version(cls, v: t.Any) -> t.Any:
        if isinstance(v, str) and v != _CURRENT_VERSION:
            version_data = f"Version: {v}; Expected: {_CURRENT_VERSION}."
            raise GRACommandLineError(
                f"Out-of-date config document. {version_data}",
                "Check GRA's release notes for upgrade instructions.",
            )
        return v

    def commit(self) -> None:
        """
        Write the current config state to disk.
        """
        _CONFIG_PATH.parent.mkdir(exist_ok=True)
        _CONFIG_PATH.write_text(self.model_dump_json(indent=4) + "\n")

    @classmethod
    def load(cls) -> GRAConfig:
        """
        Read the config from disk, loading it into a RegisteredAPIConfig instance.

        :raises click.Abort: if no config file exists.
        :raises ValidationError: if the config data is malformed in some way.
        """
        if not _CONFIG_PATH.is_file():
            raise GRACommandLineError(
                f"Missing config file at {_CONFIG_PATH.absolute()}",
                "Run 'gra init' first to create a repository.",
            )

        return cls.model_validate_json(_CONFIG_PATH.read_text())

    @classmethod
    def verify_nonexistence(cls) -> None:
        if _CONFIG_PATH.is_file():
            raise GRACommandLineError(
                f"Config already exists at {_CONFIG_PATH.absolute()}",
                "Use 'gra manage' instead to configure your repository.",
            )

    @classmethod
    def path(cls) -> Path:
        return _CONFIG_PATH


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

    # Human-readable description of what this target does.
    description: str

    # Additional security configuration to be mixed in with an OpenAPI specification.
    security: Security = Field(default_factory=Security)

    # The stage(s) this target should be published to.
    # Either a list of stages or, the default "*" to indicate all stages.
    stages: t.Literal["*"] | list[str] = "*"

    data_templates: dict[str, t.Any] | None = pydantic.Field(
        default=None,
        repr=False,  # Exclude from on-screen display rendering.
        exclude_if=lambda v: v is None,  # Exclude from serializing if None.
    )

    state_input_schema: dict[str, t.Any] | None = pydantic.Field(
        default=None,
        repr=False,  # Exclude from on-screen display rendering.
        exclude_if=lambda v: v is None,  # Exclude from serializing if None.
    )

    @property
    def specifier(self) -> TargetSpecifier:
        return TargetSpecifier.create(self.method, self.path)


class StageConfig(BaseModel):
    """
    A configuration entry for a single stage within a Registered API service.
    """

    # The common prefix URL for all API targets.
    # Example: https://api.example.com
    base_url: str

    # Filepath or URL pointing to an OpenAPI JSON document.
    # Ex: ./path/to/local
    # Ex: https://api.example.com/openapi.json
    specification: str

    # Subscription ID that grants access to registered APIs.
    subscription_id: str

    # Flows environment to deploy APIs to.
    # Only relevant for internal globus use.
    globus_environment: GlobusEnvironment = "production"

    # Mapping of alias -> registered api resource tracker.
    registered_apis: dict[str, RegisteredAPIConfig] = Field(default_factory=dict)

    # A list of roles, defining access control for identities and groups.
    # Entities within this list must be unique (w.r.t their type and id).
    roles: list[RoleConfig]


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


class RegisteredAPIConfig(BaseModel):
    registered_api_id: UUID
