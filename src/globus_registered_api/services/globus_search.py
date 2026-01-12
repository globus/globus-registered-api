# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from globus_registered_api.config import RegisteredApiConfig

SEARCH_CONFIG: RegisteredApiConfig = {
    # Load the OpenAPI spec from the specifications directory
    "openapi_uri": str(
        Path(__file__).parent / "specifications" / "search.openapi.json"
    ),
    "globus_auth": {}
}
