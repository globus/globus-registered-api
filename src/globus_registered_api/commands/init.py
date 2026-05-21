# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.commands.manage.stage.registration import StageBuilder
from globus_registered_api.config import GRAConfig
from globus_registered_api.context import is_internal_globus_user
from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import FormMenu
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import MenuDispatcher


@click.command("init")
def init_command() -> None:
    """Initialize a local Registered API Repository."""
    GRAConfig.verify_nonexistence()
    config = GRAConfig()

    menu = InitMainMenu(config)
    MenuDispatcher(menu).dispatch()


class InitMainMenu(FormMenu):
    menu_title = "Initializing GRA Repository"

    def __init__(self, config: GRAConfig) -> None:
        default_stage = "production"
        self.builder = StageBuilder(existing_stages=[], name=default_stage)
        self.config = config

    @property
    def options(self) -> LabeledDispatchOptions:
        _options = []
        if is_internal_globus_user():
            _options = [
                (
                    self.builder.set_globus_environment,
                    DataLabel(
                        "Set Globus Environment", self.builder.globus_environment
                    ),
                )
            ]

        return [
            *_options,
            (
                self.builder.set_subscription,
                DataLabel("Set Subscription", self.builder.subscription_name),
            ),
            (
                self.builder.set_specification,
                DataLabel("Set OpenAPI Location", self.builder.specification),
            ),
            (
                self.builder.set_base_url,
                DataLabel("Set Base URL", self.builder.base_url),
            ),
        ]

    def is_submittable(self) -> bool:
        return bool(
            self.builder.name
            and self.builder.base_url
            and self.builder.specification
            and self.builder.globus_environment
            and self.builder.subscription_id
        )

    def on_submit(self) -> None:
        self.config.stages[self.builder.name] = self.builder.build()
        self.config.commit()

        click.echo("Successfully initialized GRA Repository at:")
        click.echo(f"  {self.config.path().parent.absolute()}")
        click.echo()
        click.echo("To start configuring APIs in your repository, run:")
        click.echo("  gra manage")
