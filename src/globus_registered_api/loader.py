from __future__ import annotations

import json
import typing as t

import requests


def load_openapi_schema(uri: str) -> dict[str, t.Any]:
    loader = select_loader(uri)
    return loader.load_schema(uri)


def select_loader(uri: str) -> _UriOpenApiSchemaLoader:
    if uri.startswith("http://") or uri.startswith("https://"):
        return _HTTPOpenApiSchemaLoader()

    return _LocalOpenApiSchemaLoader()


class _UriOpenApiSchemaLoader(t.Protocol):
    def load_schema(self, uri: str) -> dict[str, t.Any]: ...

class _LocalOpenApiSchemaLoader(_UriOpenApiSchemaLoader):
    def load_schema(self, uri: str) -> dict[str, t.Any]:
        with open(uri, "r") as fp:
            return json.load(fp)

class _HTTPOpenApiSchemaLoader(_UriOpenApiSchemaLoader):
    def load_schema(self, uri: str) -> dict[str, t.Any]:
        resp = requests.get(uri)
        resp.raise_for_status()
        return resp.json()
