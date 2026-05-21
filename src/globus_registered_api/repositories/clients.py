# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
from contextvars import ContextVar

from globus_sdk import AuthClient
from globus_sdk import BaseClient
from globus_sdk import GlobusApp
from globus_sdk import GroupsClient
from globus_sdk import SearchClient

from globus_registered_api import ExtendedFlowsClient
from globus_registered_api.config import GlobusEnvironment
from globus_registered_api.context import create_globus_app

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

    environment: GlobusEnvironment | None = None

    @classmethod
    def instance(cls) -> GlobusClientRepository:
        if _INSTANCE.get(None) is None:
            _INSTANCE.set(GlobusClientRepository())

        return _INSTANCE.get()

    @property
    def cache_key(self) -> str:
        return self.environment or "default-environment"

    @property
    def auth(self) -> AuthClient:
        return self._get_auth_client(self.environment)

    @property
    def flows(self) -> ExtendedFlowsClient:
        return self._get_flows_client(self.environment)

    @property
    def groups(self) -> GroupsClient:
        return self._get_groups_client(self.environment)

    @property
    def search(self) -> SearchClient:
        return self._get_search_client(self.environment)

    @property
    def globus_app(self) -> GlobusApp:
        return self._get_globus_app(self.environment)

    @functools.lru_cache(maxsize=7)
    def _get_auth_client(
        self,
        environment: GlobusEnvironment | None,
    ) -> AuthClient:
        globus_app = self._get_globus_app(environment)
        return AuthClient(app=globus_app)

    @functools.lru_cache(maxsize=7)
    def _get_flows_client(
        self, environment: GlobusEnvironment | None
    ) -> ExtendedFlowsClient:
        app = self._get_globus_app(environment)
        return ExtendedFlowsClient(app=app)

    @functools.lru_cache(maxsize=7)
    def _get_groups_client(self, environment: GlobusEnvironment | None) -> GroupsClient:
        app = self._get_globus_app(environment)
        return GroupsClient(app=app)

    @functools.lru_cache(maxsize=7)
    def _get_search_client(self, environment: GlobusEnvironment | None) -> SearchClient:
        app = self._get_globus_app(environment)
        return SearchClient(app=app)

    @functools.lru_cache(maxsize=7)
    def _get_globus_app(
        self,
        environment: GlobusEnvironment | None,
    ) -> GlobusApp:
        return create_globus_app(environment)
