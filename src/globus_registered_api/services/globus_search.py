# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from uuid import UUID

from globus_sdk.scopes import SearchScopes

from globus_registered_api.config import CoreConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import RoleConfig
from globus_registered_api.config import TargetConfig

# Temporarily load the OpenAPI spec from a local file.
# This file was obtained from https://search.api.globus.org/openapi.json but
#    modified to document itself a 3.1.0 instead of 3.0.3.
_spec_location = Path(__file__).parent / "specifications/2025.02.03.search.openapi.json"

SEARCH_CONFIG = RegisteredAPIConfig(
    core=CoreConfig(
        base_url="https://search.api.globus.org", specification=str(_spec_location)
    ),
    targets=[
        TargetConfig(
            alias="create-index",
            path="/v1/index",
            method="POST",
            scope_strings=[str(SearchScopes.all)],
        ),
        TargetConfig(
            alias="view-index",
            path="/v1/index/{index_id}",
            method="GET",
            scope_strings=[str(SearchScopes.all)],
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
