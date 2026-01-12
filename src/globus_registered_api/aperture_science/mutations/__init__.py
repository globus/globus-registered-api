# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0


from ._common import SchemaMutation
from .security import InjectDefaultSecuritySchemas

__all__ = (
    "SchemaMutation",
    "InjectDefaultSecuritySchemas",
)
