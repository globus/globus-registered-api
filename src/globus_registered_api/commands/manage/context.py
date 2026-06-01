# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass

from globus_registered_api.config import GRAConfig
from globus_registered_api.openapi import OpenAPISpecAnalyzer


@dataclass
class ManageContext:
    """
    Context object for configurator subcommands.
    """

    config: GRAConfig
    analyzer: OpenAPISpecAnalyzer
