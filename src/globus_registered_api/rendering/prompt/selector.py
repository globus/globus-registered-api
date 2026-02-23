# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t

from prompt_toolkit import Application
from prompt_toolkit.filters import is_done
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.layout import AnyContainer
from prompt_toolkit.layout import ConditionalContainer
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Box
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import RadioList

T = t.TypeVar("T")


def prompt_selection(
    option_type: str,
    options: t.Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
) -> T:
    """
    Prompt the user to select a single option from a supplied list.

    Note: for multiple selection, use ``prompt_multiselection`` instead.

    Usage:
    >>> from globus_registered_api.rendering.prompt import prompt_selection
    >>> options = [(1, "Red"), (2, "Green"), (3, "Blue")]
    >>> # color_index will be one of 1, 2, or 3
    >>> color_index = prompt_selection("Color", options, default=2)

    :param option_type: A string describing the category of options being presented.
        e.g., "Color", "File", "Path", etc.
    :param options: A sequence of tuples with 2 elements, each representing an option.
        The first element of each option represents the value to be returned.
        The second represents the text to be displayed to the user during selection.
        e.g., [(1, "Red"), (2, "Green"), (3, "Blue")]
    :param default: The value of the option to start as 'selected'. If None, the
        first option will be selected by default.
    :returns: The value of the user's selected option.
    """
    n = "n" if option_type[0] in "aeiouAEIOU" else ""
    message = f"Select a{n} {option_type}:"
    selector = Selector(
        message=message,
        options=options,
        default=default,
    )
    return selector.prompt()


class Selector(t.Generic[T]):
    def __init__(
        self,
        *,
        message: str | None,
        options: t.Sequence[tuple[T, AnyFormattedText]],
        default: T | None = None,
    ) -> None:
        self.message = message
        self.options = options
        self.default = default

    def prompt(self) -> T:
        return self._create_selection_application().run()

    def _create_selection_application(self) -> Application[T]:
        radio_list = self._create_radio_list()
        container: AnyContainer = Box(
            radio_list,
            padding_top=0,
            padding_left=2,
            padding_right=1,
            padding_bottom=0,
        )
        if self.message:
            header = Box(
                Label(text=self.message, dont_extend_height=True),
                padding_top=0,
                padding_left=1,
                padding_right=1,
                padding_bottom=0,
            )
            container = HSplit([header, container])

        final_container = Label("Replace Me!")
        layout = Layout(
            container=ConditionalContainer(
                content=container, alternative_content=final_container, filter=~is_done
            ),
            focused_element=radio_list,
        )

        kb = KeyBindings()

        @kb.add("enter", eager=True)
        def _accept_input(event: KeyPressEvent) -> None:
            """Accept input when enter has been pressed."""
            current_key = radio_list.values[radio_list._selected_index][1]
            final_container.text = f"Selected: {current_key}\n"
            event.app.exit(result=radio_list.current_value, style="class:accepted")

        @kb.add("c-c")
        @kb.add("<sigint>")
        def _keyboard_interrupt(event: KeyPressEvent) -> None:
            """Abort when Control-C has been pressed."""
            event.app.exit(exception=KeyboardInterrupt(), style="class:aborting")

        return Application(
            layout=layout,
            full_screen=False,
            key_bindings=kb,
        )

    def _create_radio_list(self) -> RadioList[T]:
        return RadioList(
            values=self.options,
            default=self.default,
            select_on_focus=True,
            open_character="",
            select_character=">",
            close_character="",
            show_cursor=False,
            show_numbers=True,
            container_style="class:input-selection",
            default_style="class:option",
            selected_style="",
            checked_style="class:selected-option",
            number_style="class:number",
            show_scrollbar=False,
        )
