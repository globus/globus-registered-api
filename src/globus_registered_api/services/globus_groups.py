# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from globus_sdk.scopes import GroupsScopes

from globus_registered_api.config import RegisteredAPIConfig

GROUPS_CONFIG: RegisteredAPIConfig = {
    # Load the OpenAPI spec from the service-hosted URI
    "openapi_uri": "https://groups.api.globus.org/openapi.json",
    "globus_auth": {
        "scopes": {
            GroupsScopes.all: {
                "description": "Full access to all Groups API features",
                "targets": "*",
            },
            GroupsScopes.view_my_groups_and_memberships: {
                "description": "View your groups and memberships",
                "targets": [
                    "GET /v2/groups/my_groups",
                ]
            }
        }
    }
}
