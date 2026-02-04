# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import typing as t
from pathlib import Path
from urllib.parse import urlparse

import openapi_pydantic as oa
import requests
import yaml
from pydantic import ValidationError


class OpenAPILoadError(Exception):
    """Raised when an OpenAPI spec cannot be loaded or parsed."""


def load_openapi_spec(path: str | Path) -> oa.OpenAPI:
    """
    Load and parse an OpenAPI specification from a local file or http uri.

    Supports both JSON and YAML formats. The file format is determined
    by the file extension (.json, .yaml, or .yml).

    :param path: Path to the OpenAPI specification file
    :return: Parsed OpenAPI specification object
    :raises OpenAPILoadError: If the file cannot be found, parsed, or validated
    """
    if isinstance(path, str) and urlparse(path).scheme in {"http", "https"}:
        data = _load_http_schema(path)
    else:
        data = _load_local_schema(path)

    try:
        return oa.OpenAPI.model_validate(data)
    except ValidationError as e:
        raise OpenAPILoadError("Malformed OpenAPI specification") from e


def _load_http_schema(uri: str) -> dict[str, t.Any]:
    try:
        resp = requests.get(uri, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise OpenAPILoadError(f"Failed to fetch schema from URL: {uri}") from e

    return _load_schema_content(resp.text)


def _load_local_schema(path: str | Path) -> dict[str, t.Any]:
    path = Path(path) if isinstance(path, str) else path
    try:
        content = path.read_text()
    except OSError as e:
        raise OpenAPILoadError(f"Failed to read file: {path}") from e

    return _load_schema_content(content)



def _load_schema_content(content: str) -> dict[str, t.Any]:
    """
    Load schema from a content string.
    Loading is first attempted as JSON, then as YAML.

    :raises OpenAPILoadError: if content cannot be parsed as either JSON or YAML.
    """

    try:
        return json.loads(content)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        pass

    try:
        return yaml.safe_load(content)  # type: ignore[no-any-return]
    except yaml.YAMLError as e:
        pass

    raise OpenAPILoadError("Failed to parse OpenAPI content as JSON or YAML")
