# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import re
from urllib.parse import urlparse
from urllib.parse import urlunparse

import click
import prompt_toolkit

from globus_registered_api.commands.manage.context import ManageContext
from globus_registered_api.config import GLOBUS_ENVIRONMENTS
from globus_registered_api.config import GlobusEnvironment
from globus_registered_api.config import StageConfig
from globus_registered_api.context import is_internal_globus_user
from globus_registered_api.openapi import OpenAPISpecAnalyzer
from globus_registered_api.openapi import SpecAnalysis
from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.rendering import DataLabel
from globus_registered_api.rendering import FormMenu
from globus_registered_api.rendering import LabeledDispatchOptions
from globus_registered_api.rendering import prompt_selection
from globus_registered_api.rendering.validation.click import ClickUniqueValueParam
from globus_registered_api.rendering.validation.click import ClickURLParam
from globus_registered_api.rendering.validation.prompt_toolkit import (
    PTKOpenAPISpecValidator,
)
from globus_registered_api.rendering.validation.prompt_toolkit import (
    PTKUrlOrPathCompleter,
)
from globus_registered_api.repositories import SubscriptionRepository
from globus_registered_api.repositories.clients import GlobusClientRepository
from globus_registered_api.repositories.subscriptions import SubscriptionInfo

_OPENAPI_URL_PATTERN = re.compile(r"^https?://.+/openapi\.json")


class StageRegistrationMenu(FormMenu):
    menu_title: str = "Add Stage"

    def __init__(self, context: ManageContext) -> None:
        self._globus = GlobusClientRepository.instance()
        self.config = context.config

        stages = list(self.config.stages.keys())
        self.builder = StageBuilder(stages)

        self._saved_environment: GlobusEnvironment | None = None

    @property
    def options(self) -> LabeledDispatchOptions:
        _options: LabeledDispatchOptions = [
            (self.builder.set_name, DataLabel("Set Name", self.builder.name)),
        ]

        if is_internal_globus_user():
            _options.append(
                (
                    self.builder.set_globus_environment,
                    DataLabel(
                        "Set Globus Environment", self.builder.globus_environment
                    ),
                )
            )

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
        return self.builder.is_buildable()

    def on_submit(self) -> None:
        stage_name, stage_config = self.builder.build()
        self.config.stages[stage_name] = stage_config
        self.config.commit()

    def on_enter(self) -> None:
        self._saved_environment = self._globus.environment

    def on_exit(self) -> None:
        if self._saved_environment:
            self._globus.environment = self._saved_environment


class StageBuilder:
    def __init__(
        self,
        existing_stages: list[str],
        name: str | None = None,
    ) -> None:
        self._existing_stages = existing_stages
        self._globus = GlobusClientRepository.instance()
        self._subscription_repository = SubscriptionRepository.instance()

        self._spec_analyzer = OpenAPISpecAnalyzer()
        self._spec_analysis: SpecAnalysis | None = None

        self.name = name
        self.base_url: str | None = None
        self.specification: str | None = None
        self._subscription: SubscriptionInfo | None = None
        self.globus_environment: GlobusEnvironment = "production"

    def _set_default_subscription(self) -> None:
        active_subs = self._subscription_repository.active_subscriptions()
        if len(active_subs) == 1:
            self._subscription = active_subs[0]
        else:
            # Unset subscription if it's been set.
            # This is mostly relevant for environment-switching.
            self._subscription = None

    @property
    def subscription_id(self) -> str | None:
        return self._subscription.id if self._subscription else None

    @property
    def subscription_name(self) -> str | None:
        return self._subscription.name if self._subscription else None

    def set_name(self) -> None:
        self.name = click.prompt(
            "Stage Name",
            type=ClickUniqueValueParam(self._existing_stages),
            default=self.name,
        )

    def set_base_url(self) -> None:
        options = []
        if old_value := self.base_url:
            options = [old_value]

        options.extend(self._base_url_options_from_spec_analysis())
        options.extend(self._base_url_options_from_spec_url())

        selection = prompt_selection(
            "Base Url",
            [(option, option) for option in options]
            + [
                (None, "<Enter url manually>"),
            ],
        )
        if not selection:
            selection = click.prompt(
                "Base Url", type=ClickURLParam(), default=old_value
            )
        self.base_url = selection

    def _base_url_options_from_spec_url(self) -> list[str]:
        """
        Extrapolate base url options based on standard patterns of
        service-hosted openapi locations.

        https://groups.api.globus.org/openapi.json
           -> ["https://groups.api.globus.org"]

        https://search.api.globus.org/autodoc/openapi.json
          -> [
                "https://search.api.globus.org/autodoc",
                "https://search.api.globus.org"
            ]
        """
        if not (spec := self.specification):
            return []
        elif not _OPENAPI_URL_PATTERN.match(spec):
            return []

        # Parse the URL
        parsed = urlparse(spec)
        # Get path segments, excluding the empty first item and the trailing
        # openapi.json
        path_parts = parsed.path.strip("/").split("/")[:-1]

        base_urls = []
        # Step back through each path segment, stop at domain
        while path_parts:
            # Build URL
            base_path = "/" + "/".join(path_parts) if path_parts else ""
            base_url = urlunparse((parsed.scheme, parsed.netloc, base_path, "", "", ""))
            base_urls.append(base_url)
            # Step back
            path_parts = path_parts[:-1]

        # Do it once more for the root domain alone.
        base_path = "/" + "/".join(path_parts) if path_parts else ""
        base_url = urlunparse((parsed.scheme, parsed.netloc, base_path, "", "", ""))
        base_urls.append(base_url)

        return base_urls

    def _base_url_options_from_spec_analysis(self) -> list[str]:
        if not (analysis := self._spec_analysis):
            return []

        return analysis.https_servers

    def set_specification(self) -> None:
        old_value = self.specification
        new_value = prompt_toolkit.prompt(
            "Specification Location (Path or URL): ",
            completer=PTKUrlOrPathCompleter(),
            validator=PTKOpenAPISpecValidator(),
            validate_while_typing=False,
        ).strip()

        self.specification = new_value
        if old_value != new_value:
            self._spec_analysis = self._spec_analyzer.analyze_specification(
                load_openapi_spec(new_value)
            )

    def set_globus_environment(self) -> None:
        old_value = self.globus_environment
        self.globus_environment = prompt_selection(
            "Globus Environment",
            [(env, env) for env in GLOBUS_ENVIRONMENTS],
            default=self.globus_environment,
        )

        if old_value != self.globus_environment:
            self._globus.environment = self.globus_environment
            self._set_default_subscription()

    def set_subscription(self) -> None:
        selection: SubscriptionInfo | None = None
        active_subs = self._subscription_repository.active_subscriptions()
        if active_subs:
            selection = prompt_selection(
                "Subscription",
                [
                    *[(sub, f"{sub.name} ({sub.id})") for sub in active_subs],
                    (None, "<Enter Subscription ID Manually>"),
                ],
            )

        if not selection:
            resp = click.prompt(
                "Subscription ID",
                type=click.UUID,
                default=self.subscription_id,
            )
            selection = SubscriptionInfo(id=str(resp), name=str(resp))
        self._subscription = selection

    def is_buildable(self) -> bool:
        """
        :return: True if `build` is expected to succeed, False otherwise.
        """
        return bool(
            self.name and self.base_url and self.specification and self._subscription
        )

    def build(self) -> tuple[str, StageConfig]:
        """
        Construct a name & Stage from the internally tracked state.

        :raises ValueError: if a field required for building was not populated.
        :return: name and StageConfig tuple
        """
        identity_id = GlobusClientRepository.instance().auth.userinfo()["sub"]

        # Type-verify that name is set.
        if (name := self.name) is None:
            raise ValueError("Unset StageBuilder.name value.")

        return name, StageConfig.model_validate(
            {
                "base_url": self.base_url,
                "globus_environment": self.globus_environment,
                "specification": self.specification,
                "subscription_id": self.subscription_id,
                "roles": [
                    {
                        "type": "identity",
                        "id": identity_id,
                        "access_level": "owner",
                    }
                ],
            }
        )
