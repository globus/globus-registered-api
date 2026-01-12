import typing as t

import pytest
from globus_sdk import Scope

from globus_registered_api.aperture_science import OpenApiEnrichmentCenter
from globus_registered_api.config import RegisteredApiConfig


@pytest.fixture
def basic_openapi_schema() -> dict[str, t.Any]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Minimal API", "version": "1.0.0"},
        "paths": {
            "/example": {
                "get": {"summary": "Example GET endpoint"},
                "post": {"summary": "Example POST endpoint"},
            }
        },
    }

def test_enricher_inserts_targeted_scopes(basic_openapi_schema):
    config: RegisteredApiConfig = {
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

    enricher = OpenApiEnrichmentCenter(config)
    enriched = enricher.enrich(basic_openapi_schema)

    assert enriched["components"]["securitySchemes"]["GlobusAuth"]["type"] == "oauth2"

    get_security = enriched["paths"]["/example"]["get"]["security"]
    post_security = enriched["paths"]["/example"]["post"]["security"]
    assert get_security == [{"GlobusAuth": ["my_service:read"]}]
    assert post_security == [{"GlobusAuth": ["my_service:write"]}]


def test_enricher_inserts_all_scopes(basic_openapi_schema):
    config: RegisteredApiConfig = {
        "globus_auth": {
            "scopes": {
                Scope("my_service:all"): {
                    "description": "Full access to My Service",
                    "targets": "*",
                },
            }
        }
    }

    enricher = OpenApiEnrichmentCenter(config)
    enriched = enricher.enrich(basic_openapi_schema)

    assert enriched["components"]["securitySchemes"]["GlobusAuth"]["type"] == "oauth2"

    get_security = enriched["paths"]["/example"]["get"]["security"]
    assert get_security == [{"GlobusAuth": ["my_service:all"]}]
    post_security = enriched["paths"]["/example"]["post"]["security"]
    assert post_security == [{"GlobusAuth": ["my_service:all"]}]


def test_enricher_combines_all_and_targeted_scopes(basic_openapi_schema):
    config: RegisteredApiConfig = {
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

    enricher = OpenApiEnrichmentCenter(config)
    enriched = enricher.enrich(basic_openapi_schema)

    assert enriched["components"]["securitySchemes"]["GlobusAuth"]["type"] == "oauth2"

    get_security = enriched["paths"]["/example"]["get"]["security"]
    post_security = enriched["paths"]["/example"]["post"]["security"]
    assert get_security == [
        {"GlobusAuth": ["my_service:all"]}, {"GlobusAuth": ["my_service:read"]}
    ]
    assert post_security == [{"GlobusAuth": ["my_service:all"]}]

