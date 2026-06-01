# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import os
import typing as t

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.validation import Validator

from globus_registered_api.openapi.loader import OpenAPILoadError
from globus_registered_api.openapi.loader import load_openapi_spec


class PTKOpenAPISpecValidator(Validator):
    """
    PromptToolkit Validator

    Fails if the document does not reference a valid OpenAPI spec.
    """

    def validate(self, document: Document) -> None:
        try:
            load_openapi_spec(document.text.strip())
        except OpenAPILoadError as e:
            raise ValidationError(
                cursor_position=len(document.text),
                message=str(e),
            )


class PTKUrlOrPathCompleter(Completer):
    """
    PromptToolkit Completer

    If the input looks like it could be a URL, no autocompletion is suggested.
    If it doesn't, autocomplete it as though it's a filepath.
    """

    def __init__(self) -> None:
        self._path_completer = PathCompleter(
            expanduser=True,
            file_filter=_is_dir_or_data_file,
        )

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> t.Iterable[Completion]:
        text = document.text_before_cursor

        could_input_be_http = text.startswith(
            "http://"[: len(text)]
        ) or text.startswith("https://"[: len(text)])
        if not could_input_be_http:
            yield from self._path_completer.get_completions(document, complete_event)


def _is_dir_or_data_file(filename: str) -> bool:
    if os.path.isdir(filename):
        return True

    _, ext = os.path.splitext(filename)
    return ext.lower() in {".json", ".yaml", ".yml"}
