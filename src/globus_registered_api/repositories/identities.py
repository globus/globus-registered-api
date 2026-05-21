# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import defaultdict
from contextvars import ContextVar
from dataclasses import dataclass

from globus_registered_api.repositories.clients import GlobusClientRepository

_INSTANCE: ContextVar[IdentityRepository] = ContextVar("identity_repository_instance")


@dataclass(frozen=True)
class Identity:
    id: str
    username: str


class IdentityRepository:

    @classmethod
    def instance(cls) -> IdentityRepository:
        if _INSTANCE.get(None) is None:
            _INSTANCE.set(IdentityRepository())

        return _INSTANCE.get()

    def __init__(self) -> None:
        self._globus = GlobusClientRepository.instance()

        # client cache key -> identity id -> Identity
        self._identity_cache: dict[str, dict[str, Identity | None]] = defaultdict(dict)

    def get_identity(self, identity_id: str) -> Identity | None:
        """
        Get a single identity from Globus Auth.

        :return: An Identity object or None if the identity doesn't exist.
        """
        return self._ensure_cache([identity_id])[identity_id]

    def batch_get_identities(
        self, identity_ids: list[str]
    ) -> dict[str, Identity | None]:
        """
        Get a batch of identities, caching the result.

        :return: dict of identity id -> Identity or None if the identity
            couldn't be accessed.
        """
        cache = self._ensure_cache(identity_ids)

        return {identity_id: cache[identity_id] for identity_id in identity_ids}

    def _ensure_cache(self, identity_ids: list[str]) -> dict[str, Identity | None]:
        cache = self._identity_cache[self._globus.cache_key]

        to_query = {_id for _id in identity_ids if _id not in cache}
        if not to_query:
            return cache

        for resp in self._globus.auth.get_identities(ids=to_query)["identities"]:
            identity = Identity(id=resp["id"], username=resp["username"])
            cache[identity.id] = identity
            to_query.remove(identity.id)

        for omitted_id in to_query:
            cache[omitted_id] = None

        return cache
