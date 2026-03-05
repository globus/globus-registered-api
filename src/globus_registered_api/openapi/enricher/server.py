# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import openapi_pydantic as oa

from globus_registered_api.config import RegisteredAPIConfig


class InjectBaseUrl:
    """
    Inject base URL from config into OpenAPI servers.

    Replaces the spec's servers array with a single server using the
    base_url from the config. This ensures destination URLs are built
    as absolute URLs rather than relative paths.
    """

    def __init__(self, config: RegisteredAPIConfig) -> None:
        self._config = config

    def mutate(self, schema: oa.OpenAPI) -> None:
        """
        Mutate the schema to use the configured base URL.

        :param schema: The OpenAPI schema to mutate
        """
        schema.servers = [oa.Server(url=self._config.core.base_url)]
