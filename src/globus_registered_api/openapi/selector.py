# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import fnmatch
from dataclasses import dataclass

import openapi_pydantic as oa

from globus_registered_api.domain import TargetSpecifier


class TargetNotFoundError(Exception):
    """Raised when a target cannot be found in the OpenAPI spec."""


class AmbiguousContentTypeError(Exception):
    """Raised when multiple content types match and none was specified."""



@dataclass
class TargetInfo:
    """Information about a matched target in an OpenAPI spec."""

    # An operation target specifier, resolved to the concrete openapi schema content.
    matched_target: TargetSpecifier
    operation: oa.Operation


def find_target(
    spec: oa.OpenAPI,
    target: TargetSpecifier,
) -> TargetInfo:
    """
    Find a target operation in an OpenAPI spec.

    :param spec: The parsed OpenAPI specification
    :param target: The target specifier (method, path, optional content-type)
    :return: Information about the matched target
    :raises TargetNotFoundError: If the route or method is not found
    :raises AmbiguousContentTypeError: If multiple content types exist and none specified
    """
    # Convert to lowercase for OpenAPI spec lookup
    method = target.method.lower()

    # Find matching path
    matched_path = _find_matching_path(spec, target.path)
    if matched_path is None or spec.paths is None:
        msg = f"Route not found: '{target.path}'."
        if spec.paths:
            available_routes = "\n  ".join(sorted(spec.paths.keys()))
            msg += f"\n Available routes:\n  {available_routes}"

        raise TargetNotFoundError(msg)

    path_item = spec.paths[matched_path]

    # Get operation for method
    method_map = _operation_method_map(path_item)
    if (operation := method_map.get(method, None)) is None:
        msg = f"Method '{target.method}' not found for route '{matched_path}'."
        if method_map:
            available_methods = ", ".join(
                m.upper() for m, op in method_map.items() if op is not None
            )
            msg += f"\n Available methods:\n  {available_methods}"

        raise TargetNotFoundError(msg)

    # Resolve content type
    resolved_content_type = _resolve_content_type(operation, target.content_type)

    # Build resolved specifier with actual matched path and content-type
    resolved_specifier = TargetSpecifier(
        method=target.method,
        path=matched_path,
        content_type=resolved_content_type,
    )

    return TargetInfo(
        matched_target=resolved_specifier,
        operation=operation,
    )


def _find_matching_path(spec: oa.OpenAPI, route: str) -> str | None:
    """Find a path in the spec that matches the route pattern."""
    if spec.paths is None:
        return None

    # Try exact match first
    if route in spec.paths:
        return route

    # Try fnmatch wildcard matching
    for path in spec.paths:
        if fnmatch.fnmatch(path, route):
            return path

    return None


def _operation_method_map(path_item: oa.PathItem) -> dict[str, oa.Operation | None]:
    """Map HTTP methods to their corresponding operations in a PathItem."""
    return {
        "get": path_item.get,
        "put": path_item.put,
        "post": path_item.post,
        "delete": path_item.delete,
        "options": path_item.options,
        "head": path_item.head,
        "patch": path_item.patch,
        "trace": path_item.trace,
    }


def _resolve_content_type(
    operation: oa.Operation,
    content_type: str,
) -> str:
    """
    Resolve the content type for an operation's request body.

    Returns the input content_type unchanged if there's no request body.
    Auto-selects if there's exactly one content type.
    Uses fnmatch pattern matching for wildcards like "*" or "application/*".
    """
    if operation.requestBody is None:
        return content_type

    # Handle Reference objects
    request_body = operation.requestBody
    if isinstance(request_body, oa.Reference):
        # For now, we don't resolve $ref for request bodies
        return content_type

    if request_body.content is None:
        return content_type

    available_types = list(request_body.content.keys())

    if not available_types:
        return content_type

    # Try exact match first
    if content_type in available_types:
        return content_type

    # Try fnmatch wildcard matching
    matches = [ct for ct in available_types if fnmatch.fnmatch(ct, content_type)]

    if not matches:
        raise TargetNotFoundError(
            f"Content-type '{content_type}' not found. "
            f"Available: {', '.join(available_types)}"
        )

    if len(matches) > 1:
        raise AmbiguousContentTypeError(
            f"Multiple content-types match '{content_type}': "
            f"{', '.join(matches)}. Please specify one."
        )

    return matches[0]
