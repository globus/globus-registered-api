# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
from uuid import UUID

from globus_sdk.scopes import GroupsScopes

from globus_registered_api.config import CoreConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig

GROUPS_CONFIG = RegisteredAPIConfig(
    core=CoreConfig(
        base_url="https://groups.api.globus.org",
        specification="https://groups.api.globus.org/openapi.json",
    ),
    targets=[
        TargetConfig(
            alias="view_my_groups_and_memberships",
            method="GET",
            path="/v2/groups/my_groups",
            scope_strings=[
                str(GroupsScopes.all),
                str(GroupsScopes.view_my_groups_and_memberships),
            ],
        ),
    ],
    roles=[
        RoleConfig(
            type="group",
            id=UUID("3d0e217c-d0d3-11ee-9017-139481b69648"),
            access_level="owner",
        )
    ],
)
