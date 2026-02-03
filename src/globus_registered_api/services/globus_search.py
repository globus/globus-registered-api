# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from globus_sdk.scopes import SearchScopes

from globus_registered_api.config import RegisteredAPIConfig

SEARCH_CONFIG: RegisteredAPIConfig = {
    # Temporarily load the OpenAPI spec from a local file.
    # This file was obtained from https://search.api.globus.org/openapi.json but
    #    but modified to document itself a 3.1.0 instead of 3.0.3.
    "openapi_uri": str(
        Path(__file__).parent / "specifications" / "search.openapi.json"
    ),
    "globus_auth": {
        "scopes": {
            SearchScopes.all: {
                "description": (
                    "Query Globus Search for data which you have permissions to see or "
                    "upload new data by submitting Ingest tasks. Monitor task status, "
                    "delete data from indices where you have permissions, and perform "
                    "any other actions requiring the Ingest or Search scopes."
                ),
                "targets": "*",
            },
            SearchScopes.ingest: {
                "description": (
                    "Ingest data into Globus Search using your identities to prove "
                    "that you have permissions to do so. This also grants rights to "
                    "view Ingest Tasks which are in progress on the index and to "
                    "perform deletion operations."
                ),
                "targets": [
                    "POST /v1/index/{index_id}/ingest",
                    "GET /v1/task/{task_id}",
                    "GET /v1/task_list/{index_id}",
                    "POST /v1/index/{index_id}/entry",
                    "PUT /v1/index/{index_id}/entry",
                    "DELETE /v1/index/{index_id}/entry",
                ],
            },
            SearchScopes.search: {
                "description": (
                    "Submit queries to the Globus Search service, which uses your "
                    "identities to ensure that you can only search for data which you "
                    "have permission to see."
                ),
                "targets": [
                    "GET /v1/index/{index_id}/search",
                    "POST /v1/index/{index_id}/search",
                    "POST /v1/index/{index_id}/scroll",
                    "GET /v1/index/{index_id}/entry",
                ],
            },
        }
    },
}
