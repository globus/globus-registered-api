# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from collections import namedtuple
from functools import cached_property

from globus_registered_api.commands.manage.context import ManageContext
from globus_registered_api.config import TargetConfig
from globus_registered_api.domain import TargetSpecifier

_DiscoveredScopes: t.TypeAlias = str | list[str] | None


class SecurityExplorer:

    def __init__(
        self,
        context: ManageContext,
        target_specifier: TargetSpecifier,
        stages: list[str] | None = None,
    ) -> None:
        self.analyzer = context.analyzer
        self.specifier = target_specifier
        self.stages = stages

    @classmethod
    def for_config(
        cls, context: ManageContext, target_config: TargetConfig
    ) -> SecurityExplorer:
        stages = None if target_config.stages == "*" else target_config.stages
        return cls(context, target_config.specifier, stages)

    def has_discoverable_security(self) -> bool:
        """
        :return: True if any stage in this target has a discovered security.
        """
        scopes_by_stage = self._discovered_security_by_stage
        return any(scope is not None for scope in scopes_by_stage.values())

    @cached_property
    def rich_discovered_security(self) -> t.Any:
        """
        A rich-renderable object modeling the target's discovered security.
        """
        # Map of stage -> scope | list of unioned scopes | None
        #   for every stage this target applies to.
        scopes_by_stage = self._discovered_security_by_stage
        if len(scopes_by_stage) == 0:
            raise RuntimeError("No discoverable scope stages")

        random_scope = next(iter(scopes_by_stage.values()))
        if all(scope == random_scope for scope in scopes_by_stage.values()):
            # If every scope is equal, don't include a mention of stage names.
            key = "globus_auth_scope"
            if isinstance(random_scope, list):
                key = "globus_auth_scopes"
            single_cls = namedtuple("DiscoveredSecurity", [key])  # type: ignore[misc]
            return single_cls(**{key: random_scope})

        # Otherwise, include stage names in the display, even if some scope(s)
        # are duplicated.
        stages = sorted(scopes_by_stage.keys())
        stage_cls = namedtuple("DiscoveredSecurity", stages)  # type: ignore[misc]
        return stage_cls(**scopes_by_stage)

    @cached_property
    def _discovered_security_by_stage(self) -> dict[str, _DiscoveredScopes]:
        """
        Create a mapping of stage -> discovered globus scope(s) for a target.
        """
        stages = self.stages or list(self.analyzer.stage_analyses.keys())

        scopes_by_stage: dict[str, str | list[str] | None] = {}
        for stage in stages:
            analysis = self.analyzer.stage_analyses[stage]
            target_analysis = analysis.target_analyses.get(self.specifier)
            if not target_analysis or not target_analysis.well_known_scopes:
                scopes_by_stage[stage] = None
            elif len(target_analysis.well_known_scopes) == 1:
                scopes_by_stage[stage] = target_analysis.well_known_scopes[0]
            else:
                scopes_by_stage[stage] = target_analysis.well_known_scopes
        return scopes_by_stage
