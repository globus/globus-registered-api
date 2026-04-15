# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import openapi_pydantic as oa
import pytest

from globus_registered_api.config import CoreConfig
from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.openapi.enricher import OpenAPIEnricher


@pytest.fixture
def openapi_schema() -> oa.OpenAPI:
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
def core_config(openapi_schema) -> CoreConfig:
    return CoreConfig(
        base_url="https://api.example.com",
        specification=openapi_schema,
        subscription_id="a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    )


@pytest.fixture
def target_configs() -> SimpleNamespace:
    return SimpleNamespace(
        get_example=TargetConfig(
            alias="get-example",
            path="/example",
            method="GET",
            description="Example GET endpoint",
            security=TargetConfig.Security(globus_auth_scope="my_service:read"),
        ),
        post_example=TargetConfig(
            alias="post-example",
            path="/example",
            method="POST",
            description="Example POST endpoint",
            security=TargetConfig.Security(globus_auth_scope="my_service:write"),
        ),
    )


def test_enrichment_inserts_target_scopes(openapi_schema, core_config, target_configs):
    config = RegisteredAPIConfig(
        core=core_config,
        targets=[target_configs.get_example, target_configs.post_example],
        roles=[],
    )

    enricher = OpenAPIEnricher(config)
    enriched = enricher.enrich(openapi_schema)

    get_security = enriched.paths["/example"].get.security
    post_security = enriched.paths["/example"].post.security

    assert get_security == [{"GlobusAuth": ["my_service:read"]}]
    assert post_security == [{"GlobusAuth": ["my_service:write"]}]


def test_enrichment_only_enriches_configured_targets(
    openapi_schema, core_config, target_configs
):
    config = RegisteredAPIConfig(
        core=core_config,
        targets=[target_configs.get_example],
        roles=[],
    )

    enricher = OpenAPIEnricher(config)
    enriched = enricher.enrich(openapi_schema)

    get_security = enriched.paths["/example"].get.security
    post_security = enriched.paths["/example"].post.security

    assert get_security == [{"GlobusAuth": ["my_service:read"]}]
    assert post_security is None


def test_enrichment_without_paths(core_config, target_configs):
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
    config = RegisteredAPIConfig(
        core=core_config,
        targets=[target_configs.get_example],
        roles=[],
    )
    schema = {
        "info": {"title": "No OpenAPI spec", "version": "-1"},
        "paths": None,
    }
    openapi_schema = oa.OpenAPI.model_validate(schema)

    # Act
    # The lack of a crash demonstrates that the bug has not regressed.
    OpenAPIEnricher(config).enrich(openapi_schema)
