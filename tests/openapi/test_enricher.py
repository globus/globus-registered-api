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
    )


@pytest.fixture
def target_configs() -> SimpleNamespace:
    return SimpleNamespace(
        get_example=TargetConfig(
            alias="get-example",
            path="/example",
            method="GET",
            scope_strings=["my_service:read"],
        ),
        post_example=TargetConfig(
            alias="post-example",
            path="/example",
            method="POST",
            scope_strings=["my_service:write"],
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
