# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import functools
import typing as t
from unittest.mock import MagicMock

import click
import openapi_pydantic as oa
import prompt_toolkit
import pytest
from click.testing import CliRunner
from prompt_toolkit.formatted_text import AnyFormattedText

import globus_registered_api.cli as cli_module
import globus_registered_api.rendering.prompt.multiselector as multiselector_module
import globus_registered_api.rendering.prompt.selector as selector_module
from globus_registered_api.cli import cli as root_gra_command
from globus_registered_api.config import CoreConfig
from globus_registered_api.config import RegisteredAPIConfig


@pytest.fixture
def gra() -> t.Iterator[t.Callable[..., t.Any]]:
    """
    Factory fixture that provides a function to invoke the CLI with given arguments.

    Usage:
        def test_something(invoke_gra):
            result = gra(["some", "args"])
            result2 = gra("some other args")
    """
    runner = CliRunner()
    yield functools.partial(runner.invoke, root_gra_command)


@pytest.fixture(autouse=True)
def patched_globusapp(monkeypatch):
    """
    Always patch out the creation of a GlobusApp to avoid real authentication attempts.
    """
    monkeypatch.setattr(cli_module, "_create_globus_app", lambda: MagicMock())


@pytest.fixture
def openapi_schema() -> oa.OpenAPI:
    schema = {
        "openapi": "3.1.0",
        "info": {"title": "Minimal API", "version": "1.0.0"},
        "paths": {
            "/example": {
                "get": {"summary": "Example GET endpoint"},
                "post": {"summary": "Example POST endpoint"},
            }
        },
    }
    return oa.OpenAPI.model_validate(schema)


@pytest.fixture
def config(openapi_schema) -> RegisteredAPIConfig:
    core = CoreConfig(
        base_url="https://api.example.com",
        specification=openapi_schema,
    )
    config = RegisteredAPIConfig(core=core, targets=[], roles=[])
    return config


@pytest.fixture
def prompt_patcher(monkeypatch):
    return PromptPatcher(monkeypatch)


_PromptType = t.Literal[
    "click_prompt",
    "prompt_toolkit_prompt",
    "confirmation",
    "selection",
    "multiselection",
]
T = t.TypeVar("T")


class PromptPatcher:
    """
    Utility to aid tests in patching out user input from various prompt types:

    Supported prompt types:
        - click_prompt: click.prompt
        - prompt_toolkit_prompt: prompt_toolkit.prompt
        - confirmation: click.confirm
        - selection: rendering.prompt_selection
            - Input are compared against the supplied list of keys.
              If a match is found the corresponding value is returned, otherwise
                the input is returned as the value.
        - multiselection: rendering.prompt_multiselection
            - Similar behavior to `selection`, both keys and values are accepted.
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._monkeypatch = monkeypatch

        self._click_prompt_responses = self._patch_function(click, "prompt")
        self._confirm_responses = self._patch_function(click, "confirm")
        self._prompt_toolkit_responses = self._patch_function(prompt_toolkit, "prompt")

        # Selectors and MultiSelector get special handling to account for key mapping.
        self._select_responses = self._patch_selector(
            selector_module,
            "Selector",
        )
        self._multiselect_responses = self._patch_selector(
            multiselector_module,
            "MultiSelector",
        )

    def add_input(self, prompt_type: _PromptType, response: t.Any) -> None:
        if prompt_type == "click_prompt":
            self._click_prompt_responses.append(response)
        elif prompt_type == "confirmation":
            self._confirm_responses.append(response)
        elif prompt_type == "prompt_toolkit_prompt":
            self._prompt_toolkit_responses.append(response)
        elif prompt_type == "selection":
            self._select_responses.append(response)
        elif prompt_type == "multiselection":
            self._multiselect_responses.append(response)
        else:
            raise ValueError(f"Invalid prompt type: {prompt_type}")

    def _patch_function(self, target: object, func_name: str) -> list[t.Any]:
        """
        Monkeypatch out a target's function.

        :target: The object containing the element (func_name).
        :func_name: The attribute to patch on the target.
        :return: An empty list of responses to be subsequently populated by tests.
        """
        responses: list[t.Any] = []
        response_idx = 0

        def return_responses(*args, **kwargs):
            nonlocal response_idx
            if response_idx >= len(responses):
                name = f"{target.__name__}.{func_name}"
                raise AssertionError(f"Ran out of prompt inputs for function '{name}'")
            resp = responses[response_idx]

            response_idx += 1
            return resp

        self._monkeypatch.setattr(target, func_name, return_responses)
        return responses

    def _patch_selector(self, target: object, clazz: str) -> list[t.Any]:
        """
        Monkeypatch out a target's Selector-style class.

        In addition to regular response values, this patching will compare responses
        against user-facing keys. So if an option is (complex_value, "user key"), the
        response may be passed as either `complex_value` or `"user key"`.

        :target: The object containing the element (clazz).
        :clazz: The class to patch on the target.
        :meth: The method of the class to patch to return responses.
        :return: An empty list of responses to be subsequently populated by tests.
        """
        responses: list[t.Any] = []
        response_idx = 0

        class PatchedSelector(t.Generic[T]):
            def __init__(
                self, /, options: t.Sequence[tuple[T, AnyFormattedText]], **__: t.Any
            ) -> None:
                self.value_map = {k: v for v, k in options if isinstance(k, str)}

            def prompt(self) -> t.Any:
                nonlocal response_idx
                if response_idx >= len(responses):
                    name = f"{target.__name__}.{clazz}.prompt"
                    raise AssertionError(f"Ran out of prompt inputs for '{name}'")
                resp = responses[response_idx]
                if clazz == "Selector":
                    if isinstance(resp, str) and resp in self.value_map:
                        resp = self.value_map[resp]
                elif clazz == "MultiSelector":
                    for i, r in enumerate(resp):
                        if isinstance(r, str) and r in self.value_map:
                            resp[i] = self.value_map[r]

                response_idx += 1
                return resp

        self._monkeypatch.setattr(target, clazz, PatchedSelector)
        return responses
