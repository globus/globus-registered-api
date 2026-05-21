# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from globus_registered_api.config import GRAConfig
from globus_registered_api.config import StageConfig
from globus_registered_api.manifest import ComputedRegisteredAPI
from globus_registered_api.manifest import GRAManifest


@dataclass
class PublishContext:
    """Context object for publish operations."""

    config: GRAConfig
    manifest: GRAManifest
    stage: str
    role_urns: dict[str, list[str]]

    @property
    def stage_config(self) -> StageConfig:
        return self.config.stages[self.stage]

    @property
    def registered_apis(self) -> dict[str, ComputedRegisteredAPI]:
        """
        Access point for registered apis in the current stage.

        :return: A mapping of API aliases to ComputedRegisteredAPIs
        """
        return self.manifest.registered_apis[self.stage]
