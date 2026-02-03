# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

import openapi_pydantic as oa
import pytest
from globus_sdk import Scope

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.openapi.enchricher import OpenAPIEnricher


@pytest.fixture
def basic_openapi_schema() -> oa.OpenAPI:
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


def test_mutation_inserts_targeted_scopes(basic_openapi_schema):
    config: RegisteredAPIConfig = {
        "globus_auth": {
            "scopes": {
                Scope("my_service:read"): {
                    "description": "Read access to My Service",
                    "targets": ["get /example"],
                },
                Scope("my_service:write"): {
                    "description": "Write access to My Service",
                    "targets": ["post /example"],
                },
            }
        }
    }

    enricher = OpenAPIEnricher(config, "production")
    enriched = enricher.enrich(basic_openapi_schema)

    assert enriched.components.securitySchemes["GlobusAuth"].type == "oauth2"

    get_security = enriched.paths["/example"].get.security
    post_security = enriched.paths["/example"].post.security

    assert get_security == [{"GlobusAuth": ["my_service:read"]}]
    assert post_security == [{"GlobusAuth": ["my_service:write"]}]


def test_mutation_inserts_all_scopes(basic_openapi_schema):
    config: RegisteredAPIConfig = {
        "globus_auth": {
            "scopes": {
                Scope("my_service:all"): {
                    "description": "Full access to My Service",
                    "targets": "*",
                },
            }
        }
    }

    enricher = OpenAPIEnricher(config, "production")
    enriched = enricher.enrich(basic_openapi_schema)

    assert enriched.components.securitySchemes["GlobusAuth"].type == "oauth2"

    get_security = enriched.paths["/example"].get.security
    post_security = enriched.paths["/example"].post.security

    assert get_security == [{"GlobusAuth": ["my_service:all"]}]
    assert post_security == [{"GlobusAuth": ["my_service:all"]}]


def test_mutation_combines_all_and_targeted_scopes(basic_openapi_schema):
    config: RegisteredAPIConfig = {
        "globus_auth": {
            "scopes": {
                Scope("my_service:all"): {
                    "description": "Full access to My Service",
                    "targets": "*",
                },
                Scope("my_service:read"): {
                    "description": "Read access to My Service",
                    "targets": ["get /example"],
                },
            }
        }
    }

    enricher = OpenAPIEnricher(config, "production")
    enriched = enricher.enrich(basic_openapi_schema)

    assert enriched.components.securitySchemes["GlobusAuth"].type == "oauth2"

    get_security = enriched.paths["/example"].get.security
    post_security = enriched.paths["/example"].post.security

    assert get_security == [
        {"GlobusAuth": ["my_service:all"]},
        {"GlobusAuth": ["my_service:read"]},
    ]
    assert post_security == [{"GlobusAuth": ["my_service:all"]}]
