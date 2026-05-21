# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import sys
import typing as t

from prompt_toolkit import HTML
from prompt_toolkit.formatted_text import AnyFormattedText

from globus_registered_api.rendering.prompt import prompt_selection


# Menu Navigation Controls
class BackSentinel: ...


BACK_SENTINEL = BackSentinel()


class ExitSentinel: ...


EXIT_SENTINEL = ExitSentinel()


class SubmitSentinel: ...


SUBMIT_SENTINEL = SubmitSentinel()


ControlSignal: t.TypeAlias = BackSentinel | ExitSentinel | SubmitSentinel

# More complex dispatch response types

_ResolvedDispatchOption: t.TypeAlias = "DispatchMenu | ControlSignal | None"
_DispatchCommand: t.TypeAlias = t.Callable[[], _ResolvedDispatchOption]

DispatchOption: t.TypeAlias = _DispatchCommand | _ResolvedDispatchOption

LabeledDispatchOptions: t.TypeAlias = list[tuple[DispatchOption, AnyFormattedText]]


class DataLabel(HTML):
    def __init__(
        self,
        label_text: str,
        value: t.Any | None = None,
        # TODO - can this be removed (is it vestigial?)
        key: str | None = None,
    ) -> None:
        label = label_text
        if value is not None:
            label += " ("
            if key is not None:
                label += f"{key}: "
            label += f"'<i>{value}</i>')"

        super().__init__(label)


@t.runtime_checkable
class DispatchMenu(t.Protocol):

    @property
    def menu_title(self) -> str:
        """
        Title string, to be displayed above the list of options.
        """

    @property
    def options(self) -> LabeledDispatchOptions:
        """
        List of options and associated dispatch.

        If a selected option is:
        1. A dispatch menu - the main dispatch thread will load that menu into
            context & prompt the user to select.
        2. A subcommand - the main dispatch thread will call that subcommand
            with no parameters.
            If the subcommand returns None, it will re-prompt from the original
            menu.
            If the subcommand returns a Menu, it will proceed as in (1).
        """


@t.runtime_checkable
class FormMenu(DispatchMenu, t.Protocol):

    def is_submittable(self) -> bool:
        """
        :return: True if the form has sufficient data for the user to be shown
        a submit option, False otherwise.
        """

    def on_submit(self) -> None:
        """
        Lifecycle hook - called when a form is submitted.
        """


class MenuDispatcher:

    def __init__(self, root_menu: DispatchMenu) -> None:
        self.menu = root_menu
        self.menu_default: DispatchOption = None
        # History of parent menus and selection paths
        self.breadcrumbs: list[tuple[DispatchMenu, DispatchOption]] = []

    def dispatch(self) -> None:
        while True:
            selection = self._prompt_menu_selection()

            if callable(selection):
                resolved = selection()
            else:
                resolved = selection

            self._process_selection(selection, resolved)

    def _prompt_menu_selection(self) -> DispatchOption:
        options: LabeledDispatchOptions = self.menu.options

        # Insert control signals as necessary
        if isinstance(self.menu, FormMenu):
            if self.menu.is_submittable():
                options = options + [(SUBMIT_SENTINEL, "<Submit>")]
            options = options + [(BACK_SENTINEL, "<Cancel>")]
        else:
            # Insert a "back" option if there are any breadcrumbs to return to.
            if len(self.breadcrumbs) > 0:
                options = options + [(BACK_SENTINEL, "<Back>")]
            options = options + [(EXIT_SENTINEL, "<Exit>")]

        if self.breadcrumbs:
            title = " > ".join(b.menu_title for b, _ in self.breadcrumbs)
            title += f" > {self.menu.menu_title}"
        else:
            title = self.menu.menu_title

        return prompt_selection(
            "Menu",
            options,
            show_selection=False,
            default=self.menu_default,
            message=title,
        )

    def _process_selection(
        self, selection: DispatchOption, resolved: _ResolvedDispatchOption
    ) -> None:
        if isinstance(resolved, ExitSentinel):
            # Selected option is "Exit", do that.
            sys.exit(0)

        elif isinstance(resolved, BackSentinel):
            # Selected option is "Back", step up any breadcrumbs,
            self._invoke_lifecycle_hooks("on_exit")

            if self.breadcrumbs:
                self.menu, self.menu_default = self.breadcrumbs.pop()
            else:
                sys.exit(0)

        elif isinstance(resolved, SubmitSentinel):
            # Selected option is "Submit", step up any breadcrumbs,
            self._invoke_lifecycle_hooks("on_submit", "on_exit")

            if self.breadcrumbs:
                self.menu, self.menu_default = self.breadcrumbs.pop()
            else:
                sys.exit(0)

        elif isinstance(resolved, DispatchMenu):
            # Selected option is a static menu, step into it.
            self.breadcrumbs.append((self.menu, selection))
            self.menu, self.menu_default = resolved, None

            self._invoke_lifecycle_hooks("on_enter")

        elif resolved is None:
            # Selection option is None, don't move.
            pass

        else:
            raise RuntimeError(f"Unrecognized menu selection type: {type(resolved)}")

    def _invoke_lifecycle_hooks(self, *hooks: str) -> None:
        for hook in hooks:
            if hasattr(self.menu, hook):
                getattr(self.menu, hook)()
