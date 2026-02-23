from __future__ import annotations

import typing as t
from datetime import datetime
from pathlib import Path

import openapi_pydantic as oa

import click
from pydantic import BaseModel, field_validator, field_serializer

from globus_registered_api.openapi.reducer import OpenAPITarget


_MANIFEST_PATH = Path(".globus_registered_api/manifest.json")


class RegisteredAPIManifest(BaseModel):
    build_timestamp: datetime
    targets: dict[str, ComputedRegisteredAPI]

    def commit(self) -> None:
        _MANIFEST_PATH.parent.mkdir(exist_ok=True)
        _MANIFEST_PATH.write_text(self.model_dump_json(indent=4))

    @classmethod
    def load(cls) -> RegisteredAPIManifest:
        if not cls.exists():
            click.echo("Error: Missing repository manifest file.")
            click.echo("Run 'gra build' first to generate a manifest.")
            raise click.Abort()

        return cls.model_validate_json(_MANIFEST_PATH.read_text())

    @classmethod
    def exists(cls) -> bool:
        """
        :return: True if a manifest file exists on disk, False otherwise.
        """
        return _MANIFEST_PATH.is_file()



class ComputedRegisteredAPI(BaseModel):
    target: OpenAPITarget

    @field_validator("target", mode="before")
    @classmethod
    def ensure_target(cls, value: dict[str, t.Any]) -> OpenAPITarget:
        if isinstance(value, OpenAPITarget):
            return value
        elif isinstance(value, dict):
            return OpenAPITarget(
                operation=oa.Operation.model_validate(value["specification"]),
                destination=value["destination"],
                components=value.get("components"),
                transforms=value.get("transforms"),
            )

        raise ValueError(f"Unrecognized target type: {type(value)}")

    @field_serializer("target")
    def serialize_target(self, value: OpenAPITarget) -> dict[str, t.Any]:
        return value.to_dict()
