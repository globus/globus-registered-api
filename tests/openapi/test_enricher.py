# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import openapi_pydantic as oa
import pytest

from globus_registered_api.config import GRAConfig
from globus_registered_api.config import StageConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.openapi.enricher import OpenAPIEnricher


@pytest.fixture
def openapi_schema(monkeypatch) -> oa.OpenAPI:
    schema = {
        "openapi": "3.1.0",
        "info": {"title": "Minimal API", "version": "1.0.0"},
        "paths": {
            "/example": {
                "get": {"summary": "Example GET endpoint"},
                "post": {"summary": "Example POST endpoint"},
            }
        },
    }
    return oa.OpenAPI.model_validate(schema)


@pytest.fixture
def stage_config(openapi_schema) -> StageConfig:
    return StageConfig(
        base_url="https://api.example.com",
        specification="dummy_path.json",
        subscription_id="a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
        roles=[],
    )


@pytest.fixture
def target_configs() -> SimpleNamespace:
    return SimpleNamespace(
        get_example=TargetConfig(
            path="/example",
            method="GET",
            description="Example GET endpoint",
            security=TargetConfig.Security(globus_auth_scope="my_service:read"),
        ),
        post_example=TargetConfig(
            path="/example",
            method="POST",
            description="Example POST endpoint",
            security=TargetConfig.Security(globus_auth_scope="my_service:write"),
        ),
    )


def test_enrichment_inserts_target_scopes(openapi_schema, stage_config, target_configs):
    config = GRAConfig(
        targets={
            "get-example": target_configs.get_example,
            "post-example": target_configs.post_example,
        },
        stages={"production": stage_config},
    )

    enricher = OpenAPIEnricher(config, "production")
    enriched = enricher.enrich(openapi_schema)

    get_security = enriched.paths["/example"].get.security
    post_security = enriched.paths["/example"].post.security

    assert get_security == [{"GlobusAuth": ["my_service:read"]}]
    assert post_security == [{"GlobusAuth": ["my_service:write"]}]


def test_enrichment_only_enriches_configured_targets(
    openapi_schema, stage_config, target_configs
):
    config = GRAConfig(
        targets={"get-example": target_configs.get_example},
        stages={"production": stage_config},
    )

    enricher = OpenAPIEnricher(config, "production")
    enriched = enricher.enrich(openapi_schema)

    get_security = enriched.paths["/example"].get.security
    post_security = enriched.paths["/example"].post.security

    assert get_security == [{"GlobusAuth": ["my_service:read"]}]
    assert post_security is None


def test_enrichment_without_paths(monkeypatch, stage_config, target_configs):
    """Verify that a config with no listed paths doesn't crash.

    This is a regression test; it ensures that the following error is fixed:

        TypeError: Type Dict cannot be instantiated; use dict() instead

    which occurred when `oa.Paths()` was instantiated directly.
    """

    # The bug was triggered when the following conditions are both true:
    #
    #   *   A target must be defined.
    #       The crash did not occur if *targets* was an empty list.
    #   *   The schema must have no *paths* defined.
    #       When `oa.OpenAPI` is instantiated, *paths* is None by default.
    #
    schema = {
        "info": {"title": "No OpenAPI spec", "version": "-1"},
        "paths": None,
    }
    openapi_schema = oa.OpenAPI.model_validate(schema)

    config = GRAConfig(
        targets={"get-example": target_configs.get_example},
        stages={"production": stage_config},
    )

    # Act
    # The lack of a crash demonstrates that the bug has not regressed.
    OpenAPIEnricher(config, "production").enrich(openapi_schema)
