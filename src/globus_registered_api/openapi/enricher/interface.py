# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

import openapi_pydantic as oa


class SchemaMutation(t.Protocol):

    def mutate(self, openapi_schema: oa.OpenAPI) -> None: ...
