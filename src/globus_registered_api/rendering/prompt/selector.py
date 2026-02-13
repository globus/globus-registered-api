from __future__ import annotations

import typing as t
from dataclasses import dataclass

from prompt_toolkit import Application
from prompt_toolkit.filters import is_done
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.layout import ConditionalContainer
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Box
from prompt_toolkit.widgets import CheckboxList
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import RadioList
from prompt_toolkit.widgets import TextArea

T = t.TypeVar("T")
CustomInputFunction = t.Callable[[str], T]


class _SubmitSentinel: ...


class _CustomInputSentinel: ...


_SUBMIT_SENTINEL = _SubmitSentinel()
_CUSTOM_INPUT_SENTINEL = _CustomInputSentinel()


def prompt_selection(
    option_type: str,
    options: t.Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
):
    """
    A custom choice function.

    Prompts the user for an input from a list of options then hides the prompt.

    :returns: The user's selection.
    """
    n = "n" if option_type[0] in "aeiouAEIOU" else ""
    message = f"Select a{n} {option_type}:"
    selector = Selector(
        message=message,
        options=options,
        default=default,
    )
    return selector.prompt()


def prompt_multiselection(
    option_type: str,
    options: t.Sequence[tuple[T, AnyFormattedText]],
    *,
    defaults: t.Sequence[T] | None = None,
    custom_input: bool | CustomInputFunction = False,
):
    message = f"Select one or more {option_type}s:"
    selector = MultiSelector(
        message=message,
        options=list(options),
        defaults=list(defaults),
        custom_input=custom_input,
    )
    return selector.prompt()


class Selector:
    def __init__(
        self,
        *,
        message: str | None,
        options: t.Sequence[tuple[T, AnyFormattedText]],
        default: T | None = None,
        custom_input: bool | CustomInputFunction = False,
    ) -> None:
        self.message = message
        self.options = options
        self.default = default
        self.custom_input = custom_input

    def prompt(self) -> T:
        response = self._create_selection_application().run()
        if response is not _CUSTOM_INPUT_SENTINEL:
            return response

        custom_input_str = self._create_custom_input_application().run()
        if callable(self.custom_input):
            return self.custom_input(custom_input_str)
        else:
            return custom_input_str

    def _create_selection_application(self) -> Application[T | _CustomInputSentinel]:
        radio_list = self._create_radio_list()
        container = Box(
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

    def _create_radio_list(self) -> _CustomRadioList[T]:
        return _CustomRadioList(
            values=self.options,
            custom_input=bool(self.custom_input),
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


class _CustomRadioList(RadioList[T]):
    def __init__(
        self,
        *args,
        values: t.Sequence[tuple[T, AnyFormattedText]],
        custom_input: bool,
        **kwargs,
    ) -> None:
        if custom_input:
            values = list(values) + [(_CUSTOM_INPUT_SENTINEL, "<Custom Value>")]
        super().__init__(*args, values=values, **kwargs)
        self.control.key_bindings.add_binding("enter")(self._intercept_enter)

    def _intercept_enter(self, event: KeyPressEvent) -> None:
        selected_val = self.values[self._selected_index][0]
        if selected_val is _CUSTOM_INPUT_SENTINEL:
            event.app.exit(result=_CUSTOM_INPUT_SENTINEL, style="class:accepted")
        else:
            self._handle_enter()


@dataclass
class _MultiSelectResponse(t.Generic[T]):
    add_custom_input: bool
    current_values: list[T]


class MultiSelector:
    def __init__(
        self,
        *,
        message: str | None,
        options: list[tuple[T, AnyFormattedText]],
        defaults: list[T] | None = None,
        custom_input: bool | CustomInputFunction = False,
    ) -> None:
        self.message = message
        self.options = options
        self.defaults = defaults
        self.custom_input = custom_input

    def prompt(self) -> list[T]:
        response = self._create_selection_application().run()
        while response.add_custom_input:
            custom_input_str = self._create_custom_input_application().run()
            # Maybe add a "convert user input function" here.
            if callable(self.custom_input):
                custom_input_value = self.custom_input(custom_input_str)
            else:
                custom_input_value = custom_input_str

            self.options.append((custom_input_value, custom_input_str))
            self.defaults = response.current_values + [custom_input_value]
            response = self._create_selection_application().run()

        return response.current_values

    def _create_selection_application(self) -> Application[_MultiSelectResponse]:
        checkbox_list = self._create_checkbox_list()

        container = Box(
            checkbox_list,
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
        container = ConditionalContainer(content=container, filter=~is_done)

        layout = Layout(
            container=container,
            focused_element=checkbox_list,
        )

        kb = KeyBindings()

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

    def _create_checkbox_list(self) -> CheckboxList[T]:
        return _CustomCheckboxList(
            values=self.options,
            custom_input=bool(self.custom_input),
            default_values=self.defaults,
            open_character="",
            select_character=">",
            close_character="",
            container_style="class:input-selection",
            default_style="class:option",
            selected_style="",
            checked_style="class:selected-option",
        )


class _CustomCheckboxList(CheckboxList[T]):
    def __init__(
        self,
        *args,
        values: t.Sequence[tuple[T, AnyFormattedText]],
        custom_input: bool,
        **kwargs,
    ) -> None:
        if custom_input:
            values = list(values) + [(_CUSTOM_INPUT_SENTINEL, "<Custom Value>")]

        values = list(values) + [(_SUBMIT_SENTINEL, "Submit")]
        super().__init__(*args, values=values, **kwargs)
        self.control.key_bindings.add_binding("enter")(self._intercept_enter)

    def _intercept_enter(self, event: KeyPressEvent) -> None:
        selected_val = self.values[self._selected_index][0]
        if selected_val is _SUBMIT_SENTINEL:
            result = _MultiSelectResponse(
                add_custom_input=False,
                current_values=self.current_values,
            )
            event.app.exit(result=result)
        elif selected_val is _CUSTOM_INPUT_SENTINEL:
            result = _MultiSelectResponse(
                add_custom_input=True,
                current_values=self.current_values,
            )
            event.app.exit(result=result)
        else:
            self._handle_enter()
