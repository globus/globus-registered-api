# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import defaultdict
from contextvars import ContextVar
from dataclasses import dataclass

from globus_registered_api.repositories.clients import GlobusClientRepository

_INSTANCE: ContextVar[GroupRepository] = ContextVar("group_repository_instance")


_GROUPS_METADATA_SEARCH_INDEX_ID = "fcd4d0ab-f48d-4b13-af61-a5d40832192f"


@dataclass(frozen=True)
class Group:
    id: str
    name: str


class GroupRepository:

    @classmethod
    def instance(cls) -> GroupRepository:
        if _INSTANCE.get(None) is None:
            _INSTANCE.set(GroupRepository())

        return _INSTANCE.get()

    def __init__(self) -> None:
        self._globus = GlobusClientRepository.instance()

        # client cache key -> identity id -> Identity
        self._group_cache: dict[str, dict[str, Group | None]] = defaultdict(dict)
        self._active_cache: dict[str, list[Group]] = {}

    def active_groups(self) -> list[Group]:
        if self._globus.cache_key not in self._active_cache:
            cache = self._group_cache[self._globus.cache_key]
            groups: list[Group] = []
            for group_resp in self._globus.groups.get_my_groups():
                group_id = group_resp["id"]
                group = cache.get(group_id) or Group(
                    id=group_id, name=group_resp["name"]
                )
                cache[group_id] = group
                groups.append(group)
            self._active_cache[self._globus.cache_key] = groups

        return self._active_cache[self._globus.cache_key]

    def get_group(self, group_id: str) -> Group | None:
        """
        Get a single group from Globus Groups.

        :return: A Group object or None if the group doesn't exist.
        """
        return self._ensure_cache([group_id])[group_id]

    def batch_get_groups(self, group_ids: list[str]) -> dict[str, Group | None]:
        """
        Get a batch of groups, caching the result.

        :return: dict of group id -> Group or None if the group couldn't be
            accessed.
        """
        cache = self._ensure_cache(group_ids)

        return {group_id: cache[group_id] for group_id in group_ids}

    def _ensure_cache(self, group_ids: list[str]) -> dict[str, Group | None]:
        cache = self._group_cache[self._globus.cache_key]

        to_query = {group_id for group_id in group_ids if group_id not in cache}
        if not to_query:
            return cache

        search_resp = self._globus.search.paginated.post_search(
            _GROUPS_METADATA_SEARCH_INDEX_ID,
            {
                "filters": [
                    {
                        "type": "match_any",
                        "field_name": "id",
                        "values": [str(gid) for gid in to_query],
                    }
                ],
            },
        )

        for page in search_resp.pages():
            for result in page["gmeta"]:
                try:
                    group = Group(
                        id=result["entries"][0]["content"]["id"],
                        name=result["entries"][0]["content"]["name"],
                    )
                    cache[group.id] = group
                    to_query.remove(group.id)
                except (KeyError, IndexError):
                    # Malformed Group Index Data
                    # Debug logging?
                    continue

        for omitted_id in to_query:
            cache[omitted_id] = None

        return cache
