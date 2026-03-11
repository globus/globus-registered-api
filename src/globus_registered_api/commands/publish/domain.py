# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.extended_flows_client import ExtendedFlowsClient
from globus_registered_api.manifest import RegisteredAPIManifest


@dataclass
class PublishContext:
    """Context object for publish operations."""

    config: RegisteredAPIConfig
    manifest: RegisteredAPIManifest
    flows_client: ExtendedFlowsClient
    role_urns: dict[str, list[str]]
