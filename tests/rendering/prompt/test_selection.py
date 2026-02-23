# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import typing as t

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import PipeInput
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from globus_registered_api.rendering import prompt_multiselection
from globus_registered_api.rendering import prompt_selection

KEY_UP = "\x1b[A"
KEY_DOWN = "\x1b[B"
KEY_ENTER = "\r"


@pytest.fixture
def input_simulator() -> t.Iterator[PipeInput]:
    """
    A PipeInput which will be patched in to any PromptToolkit application created in
    the context of this fixture.

    Usage:
    def test_something(input_simulator):
        input_simulator.send_text('inputdata')

        response = prompt_toolkit.shortcuts.prompt('> ')
        assert response == 'inputdata'
    """

    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input


@pytest.mark.parametrize(
    "input_sequence, expected_response",
    [
        (KEY_ENTER, 1),  # Select first option
        (KEY_DOWN + KEY_ENTER, 2),  # Select second option
        (KEY_DOWN * 2 + KEY_ENTER, 3),  # Select third option
        (KEY_DOWN * 3 + KEY_ENTER, 3),  # Don't allow going below the last option
        (KEY_UP + KEY_ENTER, 1),  # Don't allow going above the first option
    ],
)
def test_prompt_selection(input_sequence, expected_response, input_simulator):
    """
    Rendering
    =========
    Select a Color:
     > Red
       Green
       Blue
       <Submit>
    """
    input_simulator.send_text(input_sequence)

    options = [(1, "Red"), (2, "Green"), (3, "Blue")]
    response = prompt_selection("Color", options)

    assert response == expected_response


def test_prompt_selection_with_default(input_simulator):
    input_simulator.send_text(KEY_ENTER)

    options = [(1, "Red"), (2, "Green"), (3, "Blue")]
    response = prompt_selection("Color", options, default=2)

    assert response == 2


def test_prompt_multiselection(input_simulator):
    """
    Rendering
    =========
    Select one or more Colors:
     > Red
       Green
       Blue
       <Submit>
    """
    input_simulator.send_text(KEY_ENTER)  # Select the first option.
    input_simulator.send_text(KEY_DOWN + KEY_ENTER)  # Select the second option.
    input_simulator.send_text(KEY_DOWN * 2 + KEY_ENTER)  # Select the submit button.

    options = [(1, "Red"), (2, "Green"), (3, "Blue")]
    response = prompt_multiselection("Color", options)

    assert response == [1, 2]


def test_prompt_multiselection_with_defaults(input_simulator):
    # When defaults are provided, "Submit" will be hovered at the start, so just enter.
    input_simulator.send_text(KEY_ENTER)

    options = [(1, "Red"), (2, "Green"), (3, "Blue")]
    response = prompt_multiselection("Color", options, defaults=[1, 2])

    assert response == [1, 2]


def test_prompt_multiselection_deselection(input_simulator):
    input_simulator.send_text(KEY_ENTER)  # Select the first option.
    input_simulator.send_text(KEY_ENTER)  # Deselect the first option.
    input_simulator.send_text(KEY_DOWN * 4 + KEY_ENTER)  # Select the submit button.

    options = [(1, "Red"), (2, "Green"), (3, "Blue")]
    response = prompt_multiselection("Color", options)

    assert response == []


def test_prompt_multiselection_enter_custom_input(input_simulator):
    """
    Rendering
    =========
    Select one or more Colors:
     > Red
       Green
       Blue
       <Custom Value>
       <Submit>
    """

    # Select the 'Enter custom input' option.
    input_simulator.send_text(KEY_DOWN * 3 + KEY_ENTER)
    input_simulator.send_text("pink" + KEY_ENTER)  # Enter "pink" as the custom input.
    input_simulator.send_text(KEY_ENTER)  # Select the submit button.

    options = [("red", "Red"), ("green", "Green"), ("blue", "Blue")]
    response = prompt_multiselection("Color", options, custom_input=True)

    assert response == ["pink"]
