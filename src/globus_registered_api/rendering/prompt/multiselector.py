# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t
from dataclasses import dataclass

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
from prompt_toolkit.widgets import CheckboxList
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import TextArea

T = t.TypeVar("T")


class _SubmitSentinel: ...


class _CustomInputSentinel: ...


_SUBMIT_SENTINEL = _SubmitSentinel()
_CUSTOM_INPUT_SENTINEL = _CustomInputSentinel()


def prompt_multiselection(
    option_type: str,
    options: t.Sequence[tuple[T, AnyFormattedText]],
    *,
    defaults: t.Sequence[T] | None = None,
    custom_input: bool = False,
) -> list[T]:
    """
    Prompt the user to select 0 or more options from a supplied list.

    Note: for single selection, use ``prompt_selection`` instead.

    Usage:
    >>> from globus_registered_api.rendering.prompt import prompt_selection
    >>> options = [(1, "Red"), (2, "Green"), (3, "Blue")]
    >>> # color_index will be a list of 0 or more values from 1, 2, and 3
    >>> color_index = prompt_selection("Color", options, defaults=[2, 3])

    :param option_type: A string describing the category of options being presented.
        e.g., "Color", "File", "Path", etc.
    :param options: A sequence of tuples with 2 elements, each representing an option.
        The first element of each option represents the value to be returned.
        The second represents the text to be displayed to the user during selection.
        e.g., [(1, "Red"), (2, "Green"), (3, "Blue")]
    :param defaults: The values that should start as selected.
        If None, no options will be selected by default.
    :param custom_input: If True, the user will have the ability to enter custom
        input that is not in the original list. This return type of this custom input
        will be a string.
    :returns: The list of values selected by the user.
    """

    message = f"Select one or more {option_type}s:"
    selector = MultiSelector(
        message=message,
        options=options,
        defaults=list(defaults) if defaults else None,
        custom_input=custom_input,
    )
    return selector.prompt()


@dataclass
class _CustomCheckboxResponse(t.Generic[T]):
    add_custom_input: bool
    current_values: list[T]


class MultiSelector(t.Generic[T]):
    def __init__(
        self,
        *,
        message: str,
        options: t.Sequence[tuple[T, AnyFormattedText]],
        defaults: list[T] | None,
        custom_input: bool,
    ) -> None:
        if custom_input and not all(isinstance(options[0], str) for options in options):
            raise ValueError("Custom input is only supported for string options.")

        self.message = message
        self.options = list(options)
        self.defaults = defaults
        self.custom_input = custom_input

    def prompt(self) -> list[T]:
        response = self._create_selection_application().run()
        while response.add_custom_input:
            custom_input_str = self._create_custom_input_application().run()
            self.options.append((custom_input_str, custom_input_str))  # type: ignore[arg-type]
            self.defaults = response.current_values + [custom_input_str]  # type: ignore[list-item]

            response = self._create_selection_application().run()

        return response.current_values

    def _create_selection_application(self) -> Application[_CustomCheckboxResponse[T]]:
        checkbox_list = self._create_checkbox_list()
        header = Box(
            Label(text=self.message, dont_extend_height=True),
            padding_top=0,
            padding_left=1,
            padding_right=1,
            padding_bottom=0,
        )
        body = Box(
            checkbox_list,
            padding_top=0,
            padding_left=2,
            padding_right=1,
            padding_bottom=0,
        )
        container: AnyContainer = HSplit([header, body])
        # Use a conditional container to hide the checkbox list after submission.
        container = ConditionalContainer(content=container, filter=~is_done)
        layout = Layout(container=container, focused_element=checkbox_list)

        kb = KeyBindings()

        @kb.add("c-c")
        @kb.add("<sigint>")
        def _keyboard_interrupt(event: KeyPressEvent) -> None:
            """Abort when Control-C has been pressed."""
            event.app.exit(exception=KeyboardInterrupt(), style="class:aborting")

        return Application(layout=layout, full_screen=False, key_bindings=kb)

    def _create_custom_input_application(self) -> Application[str]:
        text_area = TextArea(
            prompt="Enter a new value: ",
            multiline=False,
            style="class:custom-input",
        )
        container = ConditionalContainer(content=text_area, filter=~is_done)
        layout = Layout(container=container, focused_element=text_area)

        kb = KeyBindings()

        @kb.add("enter", eager=True)
        def _accept_input(event: KeyPressEvent) -> None:
            event.app.exit(result=text_area.text, style="class:accepted")

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

    def _create_checkbox_list(self) -> _CustomCheckboxList[T]:
        return _CustomCheckboxList(
            values=self.options,
            custom_input=self.custom_input,
            default_values=self.defaults,
            open_character="",
            select_character=">",
            close_character="",
            container_style="class:input-selection",
            default_style="class:option",
            selected_style="",
            checked_style="class:selected-option",
        )


class _CustomCheckboxList(
    t.Generic[T], CheckboxList[T | _SubmitSentinel | _CustomInputSentinel]
):
    """
    An extended CheckboxList widget.

    In addition to normal CheckboxList behavior, this widget includes:
    - a "Submit" option which causes the current application to exit, returning the
        current selection.
    - an optional "<Custom Input>" option which causes the current application to exit,
        returning the current selection and a signal that additional input is desired.
    """

    def __init__(
        self,
        values: t.Sequence[tuple[T, AnyFormattedText]],
        default_values: t.Sequence[T] | None,
        open_character: str,
        select_character: str,
        close_character: str,
        container_style: str,
        default_style: str,
        selected_style: str,
        checked_style: str,
        custom_input: bool,
    ) -> None:
        combined_values: list[
            tuple[T | _SubmitSentinel | _CustomInputSentinel, AnyFormattedText]
        ] = list(values)

        # Attach custom control buttons to the end of the list.
        if custom_input:
            combined_values += [(_CUSTOM_INPUT_SENTINEL, "<Custom Value>")]
        combined_values += [(_SUBMIT_SENTINEL, "<Submit>")]

        super().__init__(
            values=combined_values,
            default_values=default_values,
            open_character=open_character,
            select_character=select_character,
            close_character=close_character,
            container_style=container_style,
            default_style=default_style,
            selected_style=selected_style,
            checked_style=checked_style,
        )

        key_bindings = self.control.key_bindings
        if not isinstance(key_bindings, KeyBindings):
            raise RuntimeError("Unexpected key bindings type on CheckboxList control.")

        key_bindings.add_binding("enter")(self._intercept_enter)
        if default_values:
            # If defaults are provided, start on the "Submit" option.
            self._selected_index = len(combined_values) - 1

    def _intercept_enter(self, event: KeyPressEvent) -> None:
        # Override default enter behavior if control options are selected.
        selected_val = self.values[self._selected_index][0]
        if selected_val is _SUBMIT_SENTINEL:
            result = _CustomCheckboxResponse(
                add_custom_input=False,
                current_values=self.current_values,
            )
            event.app.exit(result=result)
        elif selected_val is _CUSTOM_INPUT_SENTINEL:
            result = _CustomCheckboxResponse(
                add_custom_input=True,
                current_values=self.current_values,
            )
            event.app.exit(result=result)
        else:
            self._handle_enter()
