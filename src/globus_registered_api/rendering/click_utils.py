# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click


def em(text: str) -> str:
    """
    Returns the provided text with "emphasized" codes embedded.

    Unlike `click.style` alone, this does not reset any styles besides the ones
    that it controls (notably, it does not reset color & thus can be used inside
    a line with color).

    Usage:
    >>> click.secho(f"This is {em('important')} to say!", fg="red")
    """

    return click.style(text, bold=True, italic=True, reset=False) + click.style(
        "", bold=False, italic=False, reset=False
    )
