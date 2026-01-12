# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0


from .globus_groups import GROUPS_CONFIG
from .globus_search import SEARCH_CONFIG
from ..config import RegisteredApiConfig

SERVICE_CONFIGS: dict[str, RegisteredApiConfig] = {
    "search": SEARCH_CONFIG,
    "groups": GROUPS_CONFIG,
}
