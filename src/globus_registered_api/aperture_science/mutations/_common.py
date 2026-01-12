# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

class SchemaMutation(t.Protocol):

    def mutate(self, openapi_schema: dict[str, t.Any]) -> None:
        ...
