# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import json
import uuid

import pytest
import responses
from conftest import GET_REGISTERED_API_URL
from conftest import LIST_REGISTERED_APIS_URL
from conftest import UPDATE_REGISTERED_API_URL
from globus_sdk import GlobusHTTPResponse

from globus_registered_api.extended_flows_client import ExtendedFlowsClient


@pytest.fixture
def client():
    return ExtendedFlowsClient()


def test_list_registered_apis_basic(client):
    api_id = str(uuid.uuid4())
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": api_id, "name": "Test API"},
            ],
            "has_next_page": False,
            "marker": None,
            "limit": 1,
        },
    )

    response = client.list_registered_apis()

    assert isinstance(response, GlobusHTTPResponse)
    assert len(response["registered_apis"]) == 1
    assert response["registered_apis"][0]["id"] == api_id
    assert response["registered_apis"][0]["name"] == "Test API"


def test_list_registered_apis_with_filter_roles(client):
    api_id = str(uuid.uuid4())
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": api_id, "name": "Owned API"},
            ],
            "has_next_page": False,
            "marker": None,
            "limit": 1,
        },
    )

    response = client.list_registered_apis(filter_roles=["owner", "administrator"])

    assert "filter_roles=owner%2Cadministrator" in responses.calls[0].request.url
    assert len(response["registered_apis"]) == 1
    assert response["registered_apis"][0]["id"] == api_id


def test_list_registered_apis_with_filter_roles_string(client):
    api_id = str(uuid.uuid4())
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": api_id, "name": "Viewable API"},
            ],
            "has_next_page": False,
            "marker": None,
            "limit": 1,
        },
    )

    response = client.list_registered_apis(filter_roles="viewer")

    assert "filter_roles=viewer" in responses.calls[0].request.url
    assert len(response["registered_apis"]) == 1
    assert response["registered_apis"][0]["name"] == "Viewable API"


def test_list_registered_apis_with_per_page(client):
    api_ids = [str(uuid.uuid4()) for _ in range(3)]
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": api_ids[0], "name": "API One"},
                {"id": api_ids[1], "name": "API Two"},
                {"id": api_ids[2], "name": "API Three"},
            ],
            "has_next_page": False,
            "marker": None,
            "limit": 3,
        },
    )

    response = client.list_registered_apis(per_page=50)

    assert "per_page=50" in responses.calls[0].request.url
    assert len(response["registered_apis"]) == 3
    assert response["registered_apis"][0]["id"] == api_ids[0]


def test_list_registered_apis_with_marker(client):
    marker = str(uuid.uuid4())
    api_id = str(uuid.uuid4())
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": api_id, "name": "Next Page API"},
            ],
            "has_next_page": False,
            "marker": None,
            "limit": 1,
        },
    )

    response = client.list_registered_apis(marker=marker)

    assert f"marker={marker}" in responses.calls[0].request.url
    assert len(response["registered_apis"]) == 1
    assert response["registered_apis"][0]["id"] == api_id
    assert response["registered_apis"][0]["name"] == "Next Page API"


def test_list_registered_apis_with_orderby_string(client):
    api_ids = [str(uuid.uuid4()) for _ in range(2)]
    responses.add(
        responses.GET,
        LIST_REGISTERED_APIS_URL,
        json={
            "registered_apis": [
                {"id": api_ids[0], "name": "Alpha API"},
                {"id": api_ids[1], "name": "Beta API"},
            ],
            "has_next_page": False,
            "marker": None,
            "limit": 2,
        },
    )

    response = client.list_registered_apis(orderby="name ASC")

    assert "orderby=name" in responses.calls[0].request.url
    assert len(response["registered_apis"]) == 2
    assert response["registered_apis"][0]["name"] == "Alpha API"
    assert response["registered_apis"][1]["name"] == "Beta API"


def test_get_registered_api(client):
    api_id = uuid.uuid4()
    responses.add(
        responses.GET,
        GET_REGISTERED_API_URL,
        json={
            "id": str(api_id),
            "name": "Test API",
            "description": "A test API",
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "updated_timestamp": "2025-01-01T00:00:00+00:00",
        },
    )

    response = client.get_registered_api(api_id)

    assert isinstance(response, GlobusHTTPResponse)
    assert response["id"] == str(api_id)
    assert response["name"] == "Test API"
    assert response["description"] == "A test API"
    assert f"/registered_apis/{api_id}" in responses.calls[0].request.url


def test_update_registered_api_basic(client):
    api_id = uuid.uuid4()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": str(api_id),
            "name": "Updated API",
            "description": "Updated description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    response = client.update_registered_api(api_id, name="Updated API")

    assert isinstance(response, GlobusHTTPResponse)
    assert response["name"] == "Updated API"
    assert f"/registered_apis/{api_id}" in responses.calls[0].request.url
    assert responses.calls[0].request.method == "PATCH"


def test_update_registered_api_with_description(client):
    api_id = uuid.uuid4()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": str(api_id),
            "name": "Test API",
            "description": "New description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    response = client.update_registered_api(api_id, description="New description")

    assert response["description"] == "New description"


def test_update_registered_api_with_roles(client):
    api_id = uuid.uuid4()
    new_owners = ["urn:globus:auth:identity:user1", "urn:globus:auth:identity:user2"]
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": str(api_id),
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": new_owners,
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    response = client.update_registered_api(api_id, owners=new_owners)

    assert response["roles"]["owners"] == new_owners


def test_update_registered_api_with_target(client):
    api_id = uuid.uuid4()
    target = {
        "type": "openapi",
        "openapi_version": "3.1",
        "destination": {"method": "get", "url": "https://example.com/api"},
        "specification": {"operationId": "test-op", "responses": {}},
    }
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": str(api_id),
            "name": "Test API",
            "description": "Test",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "target": target,
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": "2025-01-02T00:00:00+00:00",
        },
    )

    response = client.update_registered_api(api_id, target=target)

    assert response["target"] == target


def test_update_registered_api_omitted_params_not_in_request(client):
    api_id = uuid.uuid4()
    responses.add(
        responses.PATCH,
        UPDATE_REGISTERED_API_URL,
        json={
            "id": str(api_id),
            "name": "Updated Name",
            "description": "Original description",
            "roles": {
                "owners": ["urn:globus:auth:identity:user1"],
                "administrators": [],
                "viewers": [],
            },
            "created_timestamp": "2025-01-01T00:00:00+00:00",
            "edited_timestamp": None,
        },
    )

    client.update_registered_api(api_id, name="Updated Name")

    request_body = json.loads(responses.calls[0].request.body)
    # Only 'name' should be in the request, not None values for omitted params
    assert "name" in request_body
    assert "description" not in request_body
    assert "target" not in request_body
    assert "roles" not in request_body
