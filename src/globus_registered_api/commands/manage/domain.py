import typing as t
from dataclasses import dataclass

from globus_sdk import GlobusApp

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.openapi import SpecAnalysis


@dataclass
class ManageContext:
    """Context object for manage subcommands."""

    config: RegisteredAPIConfig
    analysis: SpecAnalysis
    globus_app: GlobusApp


ManageSubcommand = t.Callable[[], None]
ManageMenuOptions = list[tuple[str, ManageSubcommand]]


class SubcommandCanceled(Exception):
    """Exception raised that the in-progress command has been canceled."""
