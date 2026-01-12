# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import fnmatch
import re
import typing as t
from dataclasses import dataclass

import openapi_pydantic as oa


HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE")
HTTPMethod = t.Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]

_TARGET_SPECIFIER_REGEX = re.compile(
    r"^(?P<method>[A-Za-z]+)\s+(?P<path>/\S+)(\s+(?P<content_type>\S+))?$"
)


class TargetNotFoundError(Exception):
    """Raised when a target cannot be found in the OpenAPI spec."""


class AmbiguousContentTypeError(Exception):
    """Raised when multiple content types match and none was specified."""


@dataclass(frozen=True, eq=True)
class TargetSpecifier:
    """
    Identifies a target operation in an OpenAPI spec.

    Combines HTTP method, path, and optional content-type into a single
    immutable identifier. Methods are stored uppercase (canonical form).

    Both ``path`` and ``content_type`` support fnmatch-style pattern matching:

    - ``*`` matches everything
    - ``?`` matches any single character
    - ``[seq]`` matches any character in seq
    - ``[!seq]`` matches any character not in seq

    Examples:
        - ``/items/*`` matches ``/items/{id}``
        - ``/item?`` matches ``/items``
        - ``application/*`` matches ``application/json`` or ``application/xml``

    :param method: HTTP method (stored uppercase).
    :param path: Path to match. Supports fnmatch patterns.
    :param content_type: Content-type for request body. Supports fnmatch patterns.
        Defaults to ``"*"`` which matches any content-type.
    """

    method: HTTPMethod
    path: str
    content_type: str = "*"

    def __post_init__(self) -> None:
        if self.method not in HTTP_METHODS:
            raise ValueError(
                f"Invalid HTTP method: {self.method}. "
                f"Must be one of: {', '.join(HTTP_METHODS)}"
            )
        if not self.path.startswith("/"):
            raise ValueError(f"Path must start with '/': {self.path}")

    @classmethod
    def create(
        cls,
        method: str,
        path: str,
        content_type: str = "*",
    ) -> TargetSpecifier:
        """
        Create a TargetSpecifier with method normalization.

        :param method: HTTP method (case-insensitive)
        :param path: Operation path (must start with /)
        :param content_type: Content-type for request body (default: "*")
        :return: TargetSpecifier with uppercase method
        """
        return cls(
            method=t.cast(HTTPMethod, method.upper()),
            path=path,
            content_type=content_type,
        )

    @classmethod
    def load(cls, value: str) -> TargetSpecifier:
        """
        Parse a TargetSpecifier from string format.

        Format: "METHOD /path [content-type]"

        Examples:
            - "GET /items"
            - "POST /items application/json"
            - "PUT /items/{id} application/json"

        :param value: String in the format "METHOD /path [content-type]"
        :return: Parsed TargetSpecifier
        :raises ValueError: If the string format is invalid
        """
        match = _TARGET_SPECIFIER_REGEX.match(value)
        if match is None:
            raise ValueError(
                f"Invalid TargetSpecifier string: {value!r}. "
                "Expected format: 'METHOD /path [content-type]'"
            )

        return cls.create(
            method=match.group("method"),
            path=match.group("path"),
            content_type=match.group("content_type") or "*",
        )


@dataclass
class TargetInfo:
    """Information about a matched target in an OpenAPI spec."""

    specifier: TargetSpecifier
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
        raise TargetNotFoundError(f"Route not found: {target.path}")

    path_item = spec.paths[matched_path]

    # Get operation for method
    operation = _get_operation_for_method(path_item, method)
    if operation is None:
        raise TargetNotFoundError(
            f"Method '{target.method}' not found for route '{matched_path}'"
        )

    # Resolve content type
    resolved_content_type = _resolve_content_type(operation, target.content_type)

    # Build resolved specifier with actual matched path and content-type
    resolved_specifier = TargetSpecifier(
        method=target.method,
        path=matched_path,
        content_type=resolved_content_type,
    )

    return TargetInfo(
        specifier=resolved_specifier,
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


def _get_operation_for_method(
    path_item: oa.PathItem, method: str
) -> oa.Operation | None:
    """Get the operation for a given HTTP method from a path item."""
    method_map = {
        "get": path_item.get,
        "put": path_item.put,
        "post": path_item.post,
        "delete": path_item.delete,
        "options": path_item.options,
        "head": path_item.head,
        "patch": path_item.patch,
        "trace": path_item.trace,
    }
    return method_map.get(method)


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
