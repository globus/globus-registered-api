# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
import re
from dataclasses import dataclass

import openapi_pydantic as oa

from globus_registered_api.openapi.selector import TargetInfo


@dataclass
class OpenAPITarget:
    """An OpenAPI target containing the operation and its dependencies."""

    operation: oa.Operation
    destination: dict[str, str]
    components: dict[str, t.Any] | None = None
    transforms: dict[str, t.Any] | None = None

    def to_dict(self) -> dict[str, t.Any]:
        """Convert to the format expected by POST /registered_api."""
        result: dict[str, t.Any] = {
            "type": "openapi",
            "openapi_version": "3.1",
            "destination": self.destination,
            "specification": self.operation.model_dump(
                by_alias=True, exclude_none=True
            ),
            "transforms": self.transforms,
        }

        if self.components:
            result["components"] = self.components

        return result


def reduce_to_target(spec: oa.OpenAPI, target: TargetInfo) -> OpenAPITarget:
    """
    Reduce an OpenAPI spec to just the target operation and its dependencies.

    :param spec: The full OpenAPI specification
    :param target: Information about the target operation
    :return: A reduced spec with operation, destination, and collected components
    """
    # Build destination URL
    destination = _build_destination(spec, target)

    # Collect referenced components
    components = _collect_components(spec, target.operation)

    return OpenAPITarget(
        operation=target.operation,
        destination=destination,
        components=components if components else None,
        transforms=None,
    )


def _build_destination(spec: oa.OpenAPI, target: TargetInfo) -> dict[str, str]:
    """Build the destination dict with method and full URL."""
    base_url = ""
    if spec.servers and len(spec.servers) > 0:
        base_url = spec.servers[0].url.rstrip("/")

    url = f"{base_url}{target.matched_target.path}"

    return {
        "method": target.matched_target.method.lower(),
        "url": url,
    }


def _collect_components(
    spec: oa.OpenAPI, operation: oa.Operation
) -> dict[str, t.Any] | None:
    """
    Collect all components referenced by an operation.

    Traverses the operation to find all $ref references and collects
    the referenced schemas, including transitive references.
    """
    if spec.components is None or spec.components.schemas is None:
        return None

    # Find all $ref strings in the operation
    operation_dict = operation.model_dump(by_alias=True, exclude_none=True)
    refs = _find_all_refs(operation_dict)

    if not refs:
        return None

    # Collect schemas for each ref
    collected_schemas: dict[str, t.Any] = {}
    schemas_to_process = set(refs)
    processed_refs: set[str] = set()

    while schemas_to_process:
        ref = schemas_to_process.pop()
        if ref in processed_refs:
            continue
        processed_refs.add(ref)

        schema_name = _extract_schema_name(ref)
        if schema_name is None:
            continue

        if schema_name not in spec.components.schemas:
            continue

        schema = spec.components.schemas[schema_name]
        schema_dict = schema.model_dump(by_alias=True, exclude_none=True)
        collected_schemas[schema_name] = schema_dict

        # Find transitive refs in this schema
        transitive_refs = _find_all_refs(schema_dict)
        for tref in transitive_refs:
            if tref not in processed_refs:
                schemas_to_process.add(tref)

    if not collected_schemas:
        return None

    return {"schemas": collected_schemas}


def _find_all_refs(obj: t.Any) -> set[str]:
    """Recursively find all $ref strings in a nested dict/list structure."""
    refs: set[str] = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            # openapi-pydantic uses "ref" as the field name (maps to "$ref" in JSON)
            if key in ("$ref", "ref") and isinstance(value, str):
                refs.add(value)
            else:
                refs.update(_find_all_refs(value))
    elif isinstance(obj, list):
        for item in obj:
            refs.update(_find_all_refs(item))

    return refs


def _extract_schema_name(ref: str) -> str | None:
    """Extract the schema name from a $ref string like '#/components/schemas/Item'."""
    pattern = r"^#/components/schemas/(.+)$"
    match = re.match(pattern, ref)
    if match:
        return match.group(1)
    return None
