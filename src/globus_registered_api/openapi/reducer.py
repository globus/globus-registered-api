# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
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

    # Deduplicate parameters
    target.operation.parameters = _deduplicate_parameters(spec, target.operation)

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
    if spec.components is None:
        return None
    spec_components: dict[t.Literal["schemas", "parameters"], dict[str, t.Any]] = {
        "schemas": spec.components.schemas or {},
        "parameters": spec.components.parameters or {},
    }

    # Find all $ref strings in the operation
    operation_dict = operation.model_dump(by_alias=True, exclude_none=True)
    refs = _find_all_refs(operation_dict)

    if not refs:
        return None

    # Collect schemas for each ref
    collected_components: dict[str, dict[str, t.Any]] = {}
    schemas_to_process = set(refs)
    processed_refs: set[str] = set()

    while schemas_to_process:
        ref = schemas_to_process.pop()
        if ref in processed_refs:
            continue
        processed_refs.add(ref)

        subcomponent, name = _extract_reference(ref)
        if subcomponent is None:
            continue

        if name not in spec_components[subcomponent]:
            continue

        definition = spec_components[subcomponent][name]
        definition_dict = definition.model_dump(by_alias=True, exclude_none=True)
        collected_components.setdefault(subcomponent, {})[name] = definition_dict

        # Find transitive refs in this schema
        transitive_refs = _find_all_refs(definition_dict)
        for tref in transitive_refs:
            if tref not in processed_refs:
                schemas_to_process.add(tref)

    if not collected_components:
        return None

    return collected_components


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


def _extract_reference(
    ref: str,
) -> tuple[t.Literal["schemas", "parameters"], str] | tuple[None, None]:
    """Extract the subcomponent name and reference name from a $ref string.

    For example, '#/components/schemas/Item' will return `("schemas", "Item")`.
    """

    try:
        _, _, subcomponent, name = ref.rsplit("/", maxsplit=3)
        if subcomponent not in ("schemas", "parameters"):
            raise ValueError(f"Invalid subcomponent {subcomponent}")
        if not name:
            raise ValueError("'name' is empty")
    except ValueError:
        return None, None

    return t.cast(t.Literal["schemas", "parameters"], subcomponent), name


def _deduplicate_parameters(
    spec: oa.OpenAPI, operation: oa.Operation
) -> list[oa.Parameter | oa.Reference] | None:
    """
    Deduplicate parameters.

    If parameters are duplicated, only the last one listed is kept.
    """

    if not operation.parameters:
        return None

    spec_parameters = (spec.components.parameters if spec.components else None) or {}

    # The key is the tuple `(parameter.param_in, parameter.name)`.
    collected_parameters: dict[tuple[str, str], oa.Parameter | oa.Reference] = {}

    for parameter in operation.parameters:
        if isinstance(parameter, oa.Parameter):
            key = (parameter.param_in, parameter.name)
            collected_parameters[key] = parameter
        else:  # isinstance(parameter, oa.Reference)
            # Reject invalid references.
            if not parameter.ref.startswith("#/components/parameters/"):
                msg = f"'{parameter.ref}' must start with '#/components/parameters/'."
                raise ValueError(msg)
            _, _, _, name = parameter.ref.rsplit("/", maxsplit=3)
            if name not in spec_parameters:
                msg = f"'{parameter.ref}' cannot be found in 'components'."
                raise ValueError(msg)
            defined_parameter = spec_parameters[name]
            if isinstance(defined_parameter, oa.Reference):
                msg = f"'{parameter.ref}' must not be another reference."
                raise ValueError(msg)
            key = defined_parameter.param_in, defined_parameter.name
            collected_parameters[key] = defined_parameter

    if collected_parameters:
        return list(collected_parameters.values())
    return None
