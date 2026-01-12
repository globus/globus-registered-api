from __future__ import annotations

import re
import typing as t

import attrs



_HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "TRACE", "OPTIONS")
HTTPMethod = t.Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "TRACE", "OPTIONS"
]


_TARGET_SPECIFIER_REGEX = re.compile(
    r"^(?P<method>[A-Za-z]+)\s+(?P<path>/\S+)(\s+(?P<content_type>\S+))?$"
)

@attrs.define(frozen=True, eq=True)
class TargetSpecifier:
    # An HTTP method, uppercased.
    method: HTTPMethod = attrs.field(
        converter=lambda v: v.upper(),
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
        match = _TARGET_SPECIFIER_REGEX.match(value)
        return cls(
            method=match.group("method"),
            path=match.group("path"),
            content_type=match.group("content_type"),
        )
