# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path

import openapi_pydantic as oa
import yaml
from pydantic import ValidationError


class OpenAPILoadError(Exception):
    """Raised when an OpenAPI spec cannot be loaded or parsed."""


def load_openapi_spec(path: str | Path) -> oa.OpenAPI:
    """
    Load and parse an OpenAPI specification from a file.

    Supports both JSON and YAML formats. The file format is determined
    by the file extension (.json, .yaml, or .yml).

    :param path: Path to the OpenAPI specification file
    :return: Parsed OpenAPI specification object
    :raises OpenAPILoadError: If the file cannot be found, parsed, or validated
    """
    path = Path(path)

    if not path.exists():
        raise OpenAPILoadError(f"File not found: {path}")

    try:
        content = path.read_text()
    except OSError as e:
        raise OpenAPILoadError(f"Failed to read file: {path} - {e}") from e

    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(content)
        elif suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        else:
            # Try JSON first, then YAML
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                data = yaml.safe_load(content)
    except json.JSONDecodeError as e:
        raise OpenAPILoadError(f"Failed to parse JSON: {e}") from e
    except yaml.YAMLError as e:
        raise OpenAPILoadError(f"Failed to parse YAML: {e}") from e

    try:
        return oa.OpenAPI.model_validate(data)
    except ValidationError as e:
        raise OpenAPILoadError(f"Invalid OpenAPI specification: {e}") from e
