# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from collections import defaultdict
from contextvars import ContextVar
from dataclasses import dataclass

from globus_registered_api.repositories.clients import GlobusClientRepository

_INSTANCE: ContextVar[SubscriptionRepository] = ContextVar(
    "subscription_repository_instance"
)


_GROUPS_METADATA_SEARCH_INDEX_ID = "fcd4d0ab-f48d-4b13-af61-a5d40832192f"


@dataclass(frozen=True)
class SubscriptionInfo:
    id: str
    name: str


class SubscriptionRepository:
    @classmethod
    def instance(cls) -> SubscriptionRepository:
        if _INSTANCE.get(None) is None:
            _INSTANCE.set(SubscriptionRepository())

        return _INSTANCE.get()

    def __init__(self) -> None:
        self._globus = GlobusClientRepository.instance()

        self._active_cache: dict[str, list[SubscriptionInfo]] = defaultdict(list)

    def active_subscriptions(self) -> list[SubscriptionInfo]:
        """
        Returns a list of all active subscriptions for the current user.
        """
        if self._globus.cache_key not in self._active_cache:
            subscriptions = []
            for subject in self._query_active_subscription_subjects():
                for entry in subject["entries"]:
                    info = SubscriptionInfo(
                        id=entry["content"]["subscription_id"],
                        name=entry["content"]["name"],
                    )
                    subscriptions.append(info)
            self._active_cache[self._globus.cache_key] = subscriptions

        return self._active_cache[self._globus.cache_key]

    def _query_active_subscription_subjects(self) -> list[dict[str, t.Any]]:
        return self._globus.search.post_search(
            _GROUPS_METADATA_SEARCH_INDEX_ID,
            {
                "filter_principal_sets": ["status_active"],
                "filters": [{"type": "exists", "field_name": "subscription_id"}],
                "limit": 20,
            },
        ).data["gmeta"]
