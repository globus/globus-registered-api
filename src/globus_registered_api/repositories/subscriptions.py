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
        self._known_cache: dict[str, dict[str, SubscriptionInfo | None]] = defaultdict(
            dict
        )

    def get_subscription(self, subscription_id: str) -> SubscriptionInfo | None:
        """
        Returns a subscription for the requested subscription id if one can be
        found, otherwise None.
        """
        known_cache = self._known_cache[self._globus.cache_key]
        if subscription_id not in known_cache:
            subscription = self._query_single_subscription(subscription_id)
            known_cache[subscription_id] = subscription

        return known_cache[subscription_id]

    def active_subscriptions(self) -> list[SubscriptionInfo]:
        """
        Returns a list of all active subscriptions for the current user.
        """
        known_cache = self._known_cache[self._globus.cache_key]
        if self._globus.cache_key not in self._active_cache:
            subscriptions = list(self._query_active_subscriptions())
            self._active_cache[self._globus.cache_key] = subscriptions

            # For other lookups, also cache active subscriptions as known.
            for subscription in subscriptions:
                known_cache.setdefault(subscription.id, subscription)
        return self._active_cache[self._globus.cache_key]

    def _query_single_subscription(
        self, subscription_id: str
    ) -> SubscriptionInfo | None:
        subjects = self._globus.search.post_search(
            _GROUPS_METADATA_SEARCH_INDEX_ID,
            {
                "filters": [
                    {
                        "type": "match_all",
                        "field_name": "subscription_id",
                        "values": [subscription_id],
                    },
                ],
                "limit": 1,
            },
        ).data["gmeta"]
        for subject in subjects:
            for entry in subject["entries"]:
                return SubscriptionInfo(
                    id=entry["content"]["subscription_id"],
                    name=entry["content"]["name"],
                )
        return None

    def _query_active_subscriptions(self) -> t.Iterator[SubscriptionInfo]:
        subjects = self._globus.search.post_search(
            _GROUPS_METADATA_SEARCH_INDEX_ID,
            {
                "filter_principal_sets": ["status_active"],
                "filters": [{"type": "exists", "field_name": "subscription_id"}],
                "limit": 20,
            },
        ).data["gmeta"]
        for subject in subjects:
            for entry in subject["entries"]:
                yield SubscriptionInfo(
                    id=entry["content"]["subscription_id"],
                    name=entry["content"]["name"],
                )
