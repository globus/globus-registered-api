# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import typing as t
from dataclasses import dataclass

import attrs



_HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "TRACE", "OPTIONS")
HTTPMethod = t.Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "TRACE", "OPTIONS"
]


_TARGET_SPECIFIER_REGEX = re.compile(
    r"^(?P<method>[A-Za-z]+)\s+(?P<path>/\S+)(\s+(?P<content_type>\S+))?$"
)


def _uppercase(v: str) -> str:
    return v.upper()

@attrs.define(frozen=True, eq=True)
# @dataclass(frozen=True, eq=True)
class TargetSpecifier:
    # An HTTP method, uppercased.
    method: HTTPMethod = attrs.field(
        converter=_uppercase,
        validator=attrs.validators.in_(_HTTP_METHODS)
    )

    # An operation path, starting with a leading slash.
    path: str

    # Optional Content-Type specifier.
    # Currently unused.
    content_type: str | None = attrs.field(default=None)

    @classmethod
    def load(cls, value: str) -> TargetSpecifier:
        """
        Load a TargetSpecifier string in the form "METHOD /path [content-type]".
        """
        if (match := _TARGET_SPECIFIER_REGEX.match(value)) is None:
            raise ValueError(
                f"Invalid TargetSpecifier string: {value!r}. "
                "Expected format: 'METHOD /path [content-type]'"
            )

        return cls(
            method=match.group("method"),
            path=match.group("path"),
            content_type=match.group("content_type"),
        )
