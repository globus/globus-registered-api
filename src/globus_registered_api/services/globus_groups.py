from pathlib import Path

from globus_sdk.scopes import GroupsScopes

GROUPS_CONFIG = {
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
