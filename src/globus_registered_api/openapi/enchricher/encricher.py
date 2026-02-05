# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import openapi_pydantic as oa

from globus_registered_api.config import RegisteredAPIConfig

from .interface import SchemaMutation
from .security_scheme import InjectDefaultSecuritySchemas


class OpenAPIEnricher:
    """
    An OpenAPI schema enricher.

    Applies a series of configured mutations, preparing it for use as an isolated
    RegisteredAPI.
    """

    def __init__(self, config: RegisteredAPIConfig, environment: str) -> None:
        self.mutations: list[SchemaMutation] = [
            InjectDefaultSecuritySchemas(config, environment),
        ]

    def enrich(self, schema: oa.OpenAPI) -> oa.OpenAPI:
        """
        Enrich the provided OpenAPI schema.
        The supplied schema will not be changed.

        :param schema: An OpenAPI schema as a pydantic model.
        :returns: A modified copy of the OpenAPI schema.
        """
        # Deep copy the pydantic model to ensure we're not modifying the original.
        mutable_schema = schema.model_copy(deep=True)

        for mutation in self.mutations:
            mutation.mutate(mutable_schema)

        return mutable_schema
