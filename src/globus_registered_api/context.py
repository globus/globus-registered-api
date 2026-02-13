# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import functools
import typing as t
from dataclasses import dataclass

import click
from globus_sdk import GlobusApp


@dataclass
class CLIContext:
    globus_app: GlobusApp
    profile: str | None


P = t.ParamSpec("P")
R = t.TypeVar("R")


def with_cli_context(
    func: t.Callable[t.Concatenate[CLIContext, P], R],
) -> t.Callable[P, R]:
    """
    Decorator to inject CLIContext into Click command functions.

    Usage:
        @click.command()
        @click.argument("MY_ARG")
        @with_cli_context
        def my_command(ctx: CLIContext, my_arg: ...):
            ...
    """

    def wrapper(ctx: click.Context, /, *args: P.args, **kwargs: P.kwargs) -> R:
        cli_context = CLIContext(
            globus_app=ctx.obj.globus_app,
            profile=ctx.obj.profile,
        )
        return func(cli_context, *args, **kwargs)

    return functools.wraps(func)(click.pass_context(wrapper))
    # return click.pass_context(wrapper)
