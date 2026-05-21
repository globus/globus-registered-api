# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import click

from globus_registered_api.config import GlobusEnvironment
from globus_registered_api.rendering import BACK_SENTINEL
from globus_registered_api.rendering import ControlSignal
from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import DispatchMenu
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import prompt_selection
from globus_registered_api.rendering.validation.click import ClickUniqueValueParam
from globus_registered_api.rendering.validation.click import ClickURLParam
from globus_registered_api.repositories import SubscriptionRepository
from globus_registered_api.repositories.clients import GlobusClientRepository
from globus_registered_api.repositories.subscriptions import SubscriptionInfo

from ..context import ManageContext


class StageModificationMenu(DispatchMenu):
    def __init__(self, context: ManageContext, stage: str) -> None:
        self._globus = GlobusClientRepository.instance()
        self.modifier = StageModifier(context, stage)
        self.stage_config = self.modifier.stage_config

        self._saved_environment: GlobusEnvironment | None = None

    @property
    def menu_title(self) -> str:
        return f"'{self.modifier.stage}'"

    @property
    def options(self) -> LabeledDispatchOptions:
        return [
            (
                self.modifier.rename_stage,
                DataLabel("Rename Stage", self.modifier.stage),
            ),
            (
                self.modifier.modify_subscription,
                DataLabel("Modify Subscription", self.modifier.subscription_name),
            ),
            (
                self.modifier.modify_base_url,
                DataLabel("Modify Base URL", self.stage_config.base_url),
            ),
            (self.modifier.remove_stage, "Remove Stage"),
        ]

    def on_enter(self) -> None:
        self._saved_environment = self._globus.environment
        self._globus.environment = self.stage_config.globus_environment

    def on_exit(self) -> None:
        self._globus.environment = self._saved_environment


class StageModifier:
    def __init__(self, context: ManageContext, stage: str) -> None:
        self.config = context.config
        self.analyzer = context.analyzer
        self.stage = stage
        self.stage_config = self.config.stages[self.stage]

        self._subscription_repository = SubscriptionRepository.instance()
        self._subscription = self._subscription_repository.get_subscription(
            self.stage_config.subscription_id
        )
        self._globus = GlobusClientRepository.instance()

    @property
    def subscription_name(self) -> str:
        if self._subscription:
            return self._subscription.name

        return self.stage_config.subscription_id

    def rename_stage(self) -> None:
        old_value = self.stage

        # Disallow renaming a stage to different stage's name.
        disallowed_names = list(self.config.stages.keys() - {old_value})
        new_value = click.prompt(
            "New Stage",
            type=ClickUniqueValueParam(disallowed_names),
            default=self.stage,
        )

        # 1. Swap config.stages[old_value] -> config.stages[new_value]
        self.config.stages[new_value] = self.stage_config
        del self.config.stages[old_value]

        # 2. Update targets which explicitly specify this stage
        for target_config in self.config.targets.values():
            if isinstance(target_config.stages, list):
                target_config.stages = [
                    new_value if stage == old_value else stage
                    for stage in self.config.stages
                ]

        self.analyzer.rename_stage(old_value, new_value)

        self.config.commit()

    def remove_stage(self) -> ControlSignal | None:
        if len(self.config.stages) == 1:
            click.secho("Cannot remove the only remaining stage!", fg="red")
            click.secho("Please add a new stage to delete this one", fg="yellow")
            return None
        elif not click.confirm(f"Do you want to remove '{self.stage}'?"):
            click.secho("Aborted stage removal", fg="yellow")
            return None

        del self.config.stages[self.stage]
        self.config.commit()
        click.echo(f"Removed '{self.stage}'")
        return BACK_SENTINEL

    def modify_base_url(self) -> None:
        old_value = self.stage_config.base_url
        new_value = click.prompt(
            "Base URL",
            type=ClickURLParam(),
            default=old_value,
        )

        if new_value != old_value:
            self.stage_config.base_url = new_value
            self.config.commit()

    def modify_subscription(self) -> None:
        active_subs = self._subscription_repository.active_subscriptions()

        selection: SubscriptionInfo | None = None
        if active_subs:
            selection = prompt_selection(
                "Subscription",
                [
                    *[(sub, f"{sub.name} ({sub.id})") for sub in active_subs],
                    (None, "<Enter Subscription ID Manually>"),
                ],
                default=self._subscription,
            )

        if not selection:
            resp = click.prompt(
                "Subscription ID",
                type=click.UUID,
                default=self.stage_config.subscription_id,
            )
            selection = SubscriptionInfo(id=str(resp), name=str(resp))

        if selection.id != self.stage_config.subscription_id:
            self._subscription = selection
            self.stage_config.subscription_id = selection.id
            self.config.commit()
