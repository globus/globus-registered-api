# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
import uuid

from globus_sdk import FlowsClient
from globus_sdk import GlobusHTTPResponse
from globus_sdk import paging


def _filter_nones(d: dict[str, t.Any]) -> dict[str, t.Any]:
    return {k: v for k, v in d.items() if v is not None}


class ExtendedFlowsClient(FlowsClient):
    """
    Extended FlowsClient with additional methods for registered API management.
    """

    @paging.has_paginator(paging.MarkerPaginator, items_key="registered_apis")
    def list_registered_apis(
        self,
        *,
        filter_roles: str | t.Iterable[str] | None = None,
        orderby: str | t.Iterable[str] | None = None,
        per_page: int | None = None,
        marker: str | uuid.UUID | None = None,
        query_params: dict[str, t.Any] | None = None,
    ) -> GlobusHTTPResponse:
        """
        List registered APIs for which the caller has a role.

        :param filter_roles: A list of role names to filter by. Valid values are
            owner, administrator, viewer.
        :param orderby: Field(s) to order results by
        :param per_page: Number of results per page (default 10, max 100)
        :param marker: Marker for pagination
        :param query_params: Any additional parameters to be passed through
        :return: Response containing list of registered APIs
        """
        if query_params is None:
            query_params = {}

        query_params = {
            **query_params,
            **_filter_nones(
                {
                    "filter_roles": (
                        filter_roles
                        if isinstance(filter_roles, str)
                        else ",".join(filter_roles) if filter_roles else None
                    ),
                    "orderby": (
                        orderby
                        if isinstance(orderby, str)
                        else list(orderby) if orderby else None
                    ),
                    "per_page": per_page,
                    "marker": str(marker) if marker else None,
                }
            ),
        }

        return self.get("/registered_apis", query_params=query_params)

    def get_registered_api(
        self,
        registered_api_id: str | uuid.UUID,
    ) -> GlobusHTTPResponse:
        """
        Get a single registered API by ID.

        :param registered_api_id: The ID of the registered API to retrieve
        :return: Response containing the registered API details
        """
        return self.get(f"/registered_apis/{registered_api_id}")

    def update_registered_api(
        self,
        registered_api_id: str | uuid.UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        owners: list[str] | None = None,
        administrators: list[str] | None = None,
        viewers: list[str] | None = None,
        target: dict[str, t.Any] | None = None,
    ) -> GlobusHTTPResponse:
        """
        Update a registered API by ID.

        :param registered_api_id: The ID of the registered API to update
        :param name: New name for the registered API
        :param description: New description for the registered API
        :param owners: List of owner URNs (replaces existing owners)
        :param administrators: List of administrator URNs (replaces existing)
        :param viewers: List of viewer URNs (replaces existing)
        :param target: Target definition dict
        :return: Response containing the updated registered API
        """
        body: dict[str, t.Any] = _filter_nones(
            {
                "name": name,
                "description": description,
                "target": target,
            }
        )

        roles = _filter_nones(
            {
                "owners": owners,
                "administrators": administrators,
                "viewers": viewers,
            }
        )
        if roles:
            body["roles"] = roles

        return self.patch(f"/registered_apis/{registered_api_id}", data=body)

    def create_registered_api(
        self,
        name: str,
        description: str,
        target: dict[str, t.Any],
    ) -> GlobusHTTPResponse:
        """
        Create a new registered API.

        :param name: Name for the registered API
        :param description: Description for the registered API
        :param target: Target definition dict (from OpenAPITarget.to_dict())
        :return: Response containing the created registered API
        """
        body: dict[str, t.Any] = {
            "name": name,
            "description": description,
            "target": target,
        }

        return self.post("/registered_apis", data=body)
