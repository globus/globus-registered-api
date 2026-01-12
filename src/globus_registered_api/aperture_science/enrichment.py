# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t
from copy import deepcopy

from .mutations import InjectDefaultSecuritySchemas, SchemaMutation
from globus_registered_api.config import RegisteredApiConfig


class OpenApiEnrichmentCenter:
    """
    An OpenApi schema enricher.

    Mutates service OpenAPI schemas, preparing for use as individual RegisteredApis.
    """

    def __init__(self, config: RegisteredApiConfig) -> None:
        self.mutations: list[SchemaMutation] = []
        if auth_config := config.get("globus_auth"):
            self.mutations.append(InjectDefaultSecuritySchemas(auth_config))


    def enrich(self, openapi_schema: dict[str, t.Any]) -> dict[str, t.Any]:
        """
        Enrich the provided OpenAPI schema as configured.
        The supplied schema will not be changed, rather a mutated copy will be returned.

        :param openapi_schema: The original OpenAPI schema as a dictionary.
        :return: The enriched OpenAPI schema as a dictionary.
        """
        mutable_openapi_schema = deepcopy(openapi_schema)

        for mutation in self.mutations:
            mutation.mutate(mutable_openapi_schema)

        return mutable_openapi_schema



