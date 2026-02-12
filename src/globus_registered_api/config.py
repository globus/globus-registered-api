# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t

from globus_sdk import Scope


class RegisteredAPIConfig(t.TypedDict, total=False):
    openapi_uri: str
    globus_auth: GlobusAuthConfig


class GlobusAuthConfig(t.TypedDict, total=False):
    # Every scope used by the service mapped onto a brief human-readable description.
    scopes: dict[Scope, ScopeConfig]


class ScopeConfig(t.TypedDict, total=False):
    # A brief human-readable description of the scope.
    description: str | None

    # The targets which a caller consents to when consenting to this scope.
    # Either in the form of:
    #   * A list of TargetSpecifiers in the form `["POST /v2/obj", "GET /v2/obj/{id}"]`
    #   * The wildcard character "*", indicating that this scope applies to all targets.
    targets: t.Sequence[str] | t.Literal["*"]
