# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

import click


class GRACommandLineError(RuntimeError):
    def __init__(
        self,
        error_message: str,
        resolution_message: str | None = None,
    ) -> None:
        super().__init__(error_message)
        self.error = error_message
        self.resolution = resolution_message

    def click_echo(self) -> None:
        self.labeled_echo("Error", self.error, fg="red")
        if self.resolution:
            self.labeled_echo("Resolution", self.resolution, fg="yellow")

    @staticmethod
    def labeled_echo(
        label: str,
        message: str,
        fg: str | None = None,
        err: bool = True,
    ):
        content = (
            click.style(label, fg=fg, bold=True, underline=True)
            + ": "
            + click.style(message, fg=fg)
        )
        click.secho(content, err=err)


class GRAArgumentError(GRACommandLineError):
    def __init__(
        self,
        error_message: str,
        allowed_values: t.Sequence[str],
    ) -> None:
        super().__init__(error_message)
        self.allowed = ", ".join(sorted(allowed_values))

    def click_echo(self) -> None:
        super().click_echo()
        self.labeled_echo("Allowed Values", self.allowed, fg="green", err=False)
