# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import functools
import typing as t
from pathlib import Path
from unittest.mock import MagicMock

import click
import prompt_toolkit
import pytest
from click import BadParameter
from click.testing import CliRunner
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.formatted_text import to_plain_text

import globus_registered_api.rendering.prompt.selector as selector_module
from globus_registered_api.cli import cli as root_gra_command
from globus_registered_api.config import GRAConfig
from globus_registered_api.openapi import loader as loader_module
from globus_registered_api.openapi.loader import OpenAPILoadError
from globus_registered_api.rendering import DataLabel
from globus_registered_api.repositories.clients import GlobusClientRepository


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
    globus = GlobusClientRepository.instance()
    globusapp = MagicMock()
    monkeypatch.setitem(globus._globus_app_cache, globus.cache_key, globusapp)

    return globusapp


@pytest.fixture
def openapi_schema(monkeypatch) -> dict[str, t.Any]:
    """
    Patch out schema loading (via `load_openapi_spec`) to return
    this central dictionary.

    Note:
      * If a schema path is local & exists (e.g., tests/files/openapi_specs/...)
        that file is still loaded. Otherwise, any url or invalid path reference
        ("https://foobar.com" or "dummy.json") returns this schema.

    :returns: the dictionary that will be returned each time load is attempted.
    """

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
    # Always patch out http schemata
    monkeypatch.setattr(loader_module, "_load_http_schema", lambda _: schema)

    # Fallback patch out local schemata
    real_load_local_schema = loader_module._load_local_schema

    def _load_local_schema_with_fallback(path: str | Path) -> dict[str, t.Any]:
        try:
            return real_load_local_schema(path)
        except OpenAPILoadError:
            return schema

    monkeypatch.setattr(
        loader_module, "_load_local_schema", _load_local_schema_with_fallback
    )
    return schema


@pytest.fixture
def config(openapi_schema, subscription_id) -> GRAConfig:
    config_dict = {
        "targets": {},
        "stages": {
            "production": {
                "base_url": "https://api.example.com",
                "specification": "dummy_path.json",
                "subscription_id": subscription_id,
                "roles": [],
            }
        },
    }
    return GRAConfig.model_validate(config_dict)


@pytest.fixture
def prompt_patcher(monkeypatch):
    return PromptPatcher(monkeypatch)


_PromptType = t.Literal[
    "click_prompt",
    "prompt_toolkit_prompt",
    "confirmation",
    "selection",
]
T = t.TypeVar("T")


class PromptPatcher:
    """
    Utility to aid tests in patching out user input from various prompt types:

    Supported prompt types:
        - click_prompt: click.prompt
        - prompt_toolkit_prompt: prompt_toolkit.prompt
        - confirmation: click.confirm

    Specialized function prompt type:
        - selection: rendering.prompt_selection
            - str -> matches against the display values
            - int -> matches against the index of options
            - other -> returns the value as supplied
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._monkeypatch = monkeypatch

        self._click_prompt_responses = self._patch_function(click, "prompt")
        self._confirm_responses = self._patch_function(click, "confirm")
        self._prompt_toolkit_responses = self._patch_function(prompt_toolkit, "prompt")

        # Selectors get special handling to account for key mapping.
        self._select_responses = self._patch_selector(
            selector_module,
            "Selector",
        )

    def add_input(self, prompt_type: _PromptType, response: t.Any) -> None:
        """
        Register the next input to be made for a specific prompt type.

        This value will be returned when that prompting function is next called.
        Note: for selections, see `add_selection` and `add_selections`.
        """
        if prompt_type == "click_prompt":
            self._click_prompt_responses.append(response)
        elif prompt_type == "confirmation":
            self._confirm_responses.append(response)
        elif prompt_type == "prompt_toolkit_prompt":
            self._prompt_toolkit_responses.append(response)
        else:
            raise ValueError(f"Invalid prompt type: {prompt_type}")

    def add_selections(self, *display_values) -> None:
        """
        Convenience wrapper around `add_selection`.

        Register multiples subsequent selections (typically with related
           context) in the same method call.
        """

        for display_value in display_values:
            self.add_selection(display_value)

    def add_selection(
        self,
        display_value: str | None,
        *,
        index: int | None = None,
        raw_value: t.Any | None = None,
    ) -> None:
        """
        Register the next value to be selected when a selection is prompted.

        If the value is not present as specified, an error is raised instead.
        """

        supplied = sum([bool(display_value), bool(index), bool(raw_value)])
        if supplied != 1:
            raise ValueError("Must provide exactly one mutexed selection type.")

        if display_value is not None:
            self._select_responses.append(("display", display_value))
        elif index is not None:
            self._select_responses.append(("index", index))
        elif raw_value is not None:
            self._select_responses.append(("raw", raw_value))
        else:
            raise ValueError("Must provide one of display_value, index, or raw_value")

    def _patch_function(self, target: object, func_name: str) -> list[t.Any]:
        """
        Monkeypatch out a target's function.

        :target: The object containing the element (func_name).
        :func_name: The attribute to patch on the target.
        :return: An empty list of responses to be subsequently populated by tests.
        """
        responses: list[t.Any] = []
        response_idx = 0

        name = f"{target.__name__}.{func_name}"

        def return_responses(*args, **kwargs):
            nonlocal response_idx
            if response_idx >= len(responses):
                raise AssertionError(f"Ran out of prompt inputs for function '{name}'")
            resp = responses[response_idx]

            if name == "click.prompt":
                if isinstance(param_type := kwargs.get("type"), click.ParamType):
                    try:
                        resp = param_type(resp)
                    except BadParameter as e:
                        msg = "click.prompt supplied input failed validation"
                        raise AssertionError(msg) from e

            response_idx += 1
            return resp

        self._monkeypatch.setattr(target, func_name, return_responses)
        return responses

    def _patch_selector(self, target: object, clazz: str) -> list[tuple[str, t.Any]]:
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
                # Pre-process supplied options into str display names.
                #   for simpler human comprehension of selection terms.
                self._option_index: dict[str, T] = {}
                self._options: list[tuple[T, str]] = []
                for option_val, display_name in options:
                    if isinstance(display_name, DataLabel):
                        display_name = display_name.label_text
                    else:
                        display_name = to_plain_text(display_name)
                    self._option_index[display_name] = option_val
                    self._options.append((option_val, display_name))
                self._options_rendering = ", ".join(
                    [option[1] for option in self._options]
                )

            def prompt(self) -> T:
                nonlocal response_idx
                if response_idx >= len(responses):
                    name = f"{target.__name__}.{clazz}.prompt"
                    raise AssertionError(f"Ran out of prompt inputs for '{name}'")

                # Pop the next supplied responses value if there is one.
                selection = responses[response_idx]
                if clazz == "Selector":
                    if selection[0] == "display":
                        if selection[1] in self._option_index:
                            response_idx += 1
                            return self._option_index[selection[1]]
                        pytest.fail(
                            f"Selected option ('{selection[1]}') is not an "
                            f"option. Options: {self._options_rendering}."
                        )

                    elif selection[0] == "index":
                        if len(self._options) <= selection[1]:
                            response_idx += 1
                            return self._options[selection[1] - 1][0]

                        pytest.fail(
                            f"Selected index ({selection[1]}) is out of range."
                            f"Options: {self._options_rendering}."
                        )

                    elif selection[0] == "raw":
                        response_idx += 1
                        return selection[1]

                raise RuntimeError(f"Invalid selection type: {selection[0]}")

            def _option_names(self) -> str:
                return ", ".join([option[1] for option in self._options])

        self._monkeypatch.setattr(target, clazz, PatchedSelector)
        return responses
