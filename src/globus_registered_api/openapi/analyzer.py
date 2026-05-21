# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from dataclasses import dataclass
from urllib.parse import urlparse

import openapi_pydantic as oa

from globus_registered_api.config import GRAConfig
from globus_registered_api.config import StageConfig
from globus_registered_api.domain import HTTP_METHODS
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.openapi.loader import load_openapi_spec


@dataclass
class SpecAnalysis:
    target_analyses: dict[TargetSpecifier, TargetAnalysis]
    https_servers: list[str]


@dataclass
class TargetAnalysis:
    description: str | None
    well_known_scopes: list[str]


@dataclass
class AggTargetAnalysis:
    description: str | None
    well_known_scopes: set[str]
    stages: t.Literal["*"] | set[str]


class OpenAPISpecAnalyzer:

    def __init__(self) -> None:
        # Mapping of stage ->
        self._spec_analyses: dict[str, SpecAnalysis] = {}
        self.agg_target_analyses: dict[TargetSpecifier, AggTargetAnalysis] = {}
        self.agg_well_known_scopes: set[str] = set()

    def analyze(self, config: GRAConfig) -> None:
        for stage, stage_config in config.stages.items():
            self.analyze_stage(stage, stage_config)

        self._compute_aggregates()

    def analyze_stage(self, stage: str, config: StageConfig) -> None:
        spec = load_openapi_spec(config.specification)
        self._spec_analyses[stage] = self.analyze_specification(spec)

    def analyze_specification(self, spec: oa.OpenAPI) -> SpecAnalysis:
        target_analyses: dict[TargetSpecifier, TargetAnalysis] = {}

        for path, path_schema in (spec.paths or {}).items():
            for method in HTTP_METHODS:
                if operation := getattr(path_schema, method.lower(), None):
                    specifier = TargetSpecifier.create(method, path)

                    well_known_scopes = []
                    for requirement in operation.security or []:
                        if (
                            len(requirement) == 1
                            and (globus_auth_scopes := requirement.get("GlobusAuth"))
                            and len(globus_auth_scopes) == 1
                        ):
                            well_known_scopes.append(globus_auth_scopes[0])

                    target_analyses[specifier] = TargetAnalysis(
                        description=operation.summary or operation.description,
                        well_known_scopes=well_known_scopes,
                    )

        https_servers = [
            server.url
            for server in spec.servers
            if urlparse(server.url).scheme == "https"
        ]

        return SpecAnalysis(
            target_analyses=target_analyses,
            https_servers=https_servers,
        )

    def _compute_aggregates(self) -> None:
        self.agg_target_analyses = {}
        self.agg_well_known_scopes = set()

        for stage, spec_analysis in self._spec_analyses.items():
            for specifier, target_analysis in spec_analysis.target_analyses.items():
                well_known_scopes = set(target_analysis.well_known_scopes)
                self.agg_well_known_scopes.update(well_known_scopes)

                if analysis := self.agg_target_analyses.get(specifier, None):
                    if isinstance(analysis.stages, set):
                        analysis.stages.add(stage)
                    analysis.well_known_scopes.update(well_known_scopes)

                else:
                    self.agg_target_analyses[specifier] = AggTargetAnalysis(
                        description=target_analysis.description,
                        well_known_scopes=well_known_scopes,
                        stages={stage},
                    )

        all_stages = self._spec_analyses.keys()
        for agg_target_analysis in self.agg_target_analyses.values():
            if agg_target_analysis.stages == all_stages:
                agg_target_analysis.stages = "*"

    def remove(self, stage: str) -> None:
        self._spec_analyses.pop(stage, None)

    def rename_stage(self, original_stage: str, new_stage: str) -> None:
        if original_stage not in self._spec_analyses:
            raise RuntimeError(f"'{original_stage}' is not an analyzed stage.")
        elif new_stage in self._spec_analyses:
            raise RuntimeError(f"'{new_stage}' is a duplicate stage analysis.")

        self._spec_analyses[new_stage] = self._spec_analyses[original_stage]
        self._spec_analyses.pop(original_stage, None)
