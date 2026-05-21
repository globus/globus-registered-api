# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

import click


class ClickURLParam(click.ParamType):
    """
    Click ParamType

    Fails if a value doesn't look like an HTTP or HTTPS url.
    """

    name = "url"

    def convert(
        self,
        value: t.Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> str:
        if not isinstance(value, str):
            self.fail(f"{value!r} is not a valid string", param, ctx)

        if not (value.startswith("http://") or value.startswith("https://")):
            self.fail(f"{value!r} is not a valid URL", param, ctx)

        return value


class ClickUniqueValueParam(click.ParamType):
    """
    Click ParamType

    Fails if a value already exists in a supplied value list.
    """

    name: str = "unique-value"

    def __init__(self, existing_values: t.Sequence[t.Any]) -> None:
        self.existing_values = existing_values

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> str:
        if value in self.existing_values:
            self.fail(f"{value!r} is already exists.", param, ctx)
        return value
