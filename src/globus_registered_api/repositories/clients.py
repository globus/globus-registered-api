# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from collections import defaultdict
from contextvars import ContextVar

from globus_sdk import AuthClient
from globus_sdk import BaseClient
from globus_sdk import GlobusApp
from globus_sdk import GlobusAppConfig
from globus_sdk import GroupsClient
from globus_sdk import SearchClient

from globus_registered_api import ExtendedFlowsClient
from globus_registered_api.config import GLOBUS_ENVIRONMENTS
from globus_registered_api.config import GlobusEnvironment
from globus_registered_api.context import create_globus_app
from globus_registered_api.errors import GRAArgumentError

_INSTANCE: ContextVar[GlobusClientRepository] = ContextVar(
    "globus_client_repository_instance"
)


class GlobusClientRepository:
    """
    Global Repository of Globus Clients.

    GlobusApps & Clients are cached per environment per thread.

    Normal client access looks like:
    >>> flows_client = GlobusClientRepository.instance().flows

    Orchestration components may set a globally configured environment via:
    >>> GlobusClientRepository.instance().environment = ...

    In addition to clients, the construct offers a `cache_key` property for
    call sites to use in their own internal caching of results from clients.
    """

    def __init__(self) -> None:
        default_env = GlobusAppConfig().environment
        if default_env not in GLOBUS_ENVIRONMENTS:
            raise GRAArgumentError(
                f"Unrecognized GLOBUS_SDK_ENVIRONMENT value: {default_env}",
                GLOBUS_ENVIRONMENTS,
                autosort=False,
            )

        self.environment: GlobusEnvironment = GlobusAppConfig().environment  # type: ignore[assignment]
        self._client_cache: dict[GlobusEnvironment, dict[str, BaseClient]] = (
            defaultdict(dict)
        )
        self._globus_app_cache: dict[GlobusEnvironment, GlobusApp] = {}

    @classmethod
    def instance(cls) -> GlobusClientRepository:
        if _INSTANCE.get(None) is None:
            _INSTANCE.set(GlobusClientRepository())

        return _INSTANCE.get()

    @property
    def cache_key(self) -> GlobusEnvironment:
        return self.environment

    @property
    def auth(self) -> AuthClient:
        cache = self._client_cache[self.cache_key]
        if "auth" not in cache:
            cache["auth"] = AuthClient(app=self.globus_app)
        return t.cast(AuthClient, cache["auth"])

    @property
    def flows(self) -> ExtendedFlowsClient:
        cache = self._client_cache[self.cache_key]
        if "flows" not in cache:
            cache["flows"] = ExtendedFlowsClient(app=self.globus_app)
        return t.cast(ExtendedFlowsClient, cache["flows"])

    @property
    def groups(self) -> GroupsClient:
        cache = self._client_cache[self.cache_key]
        if "groups" not in cache:
            cache["groups"] = GroupsClient(app=self.globus_app)
        return t.cast(GroupsClient, cache["groups"])

    @property
    def search(self) -> SearchClient:
        cache = self._client_cache[self.cache_key]
        if "search" not in cache:
            cache["search"] = SearchClient(app=self.globus_app)
        return t.cast(SearchClient, cache["search"])

    @property
    def globus_app(self) -> GlobusApp:
        if self.cache_key not in self._globus_app_cache:
            globus_app = create_globus_app(self.environment)
            self._globus_app_cache[self.cache_key] = globus_app

        return self._globus_app_cache[self.cache_key]
