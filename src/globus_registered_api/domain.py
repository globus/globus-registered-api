# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import typing as t
from dataclasses import dataclass

HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "TRACE", "OPTIONS")
HTTPMethod = t.Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "TRACE", "OPTIONS"
]


_TARGET_SPECIFIER_REGEX = re.compile(
    r"^(?P<method>[A-Za-z]+)\s+(?P<path>/\S+)(\s+(?P<content_type>\S+))?$"
)


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
