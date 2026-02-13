import typing as t
from dataclasses import dataclass
from urllib.parse import urlparse

import openapi_pydantic as oa

from globus_registered_api.domain import HTTP_METHODS
from globus_registered_api.domain import TargetSpecifier


@dataclass
class SpecAnalysis:
    # A list of all targets defined in the specification
    targets: list[TargetSpecifier]

    # A list of all unique scope strings used in operations across the specification.
    # Note: these only include "well-formed" scopes in the shape
    #   `{"GlobusAuth": [scope_string]}` with a single scope string in the list.
    scope_strings: list[str]

    # A mapping of targets and scopes, identifying well-defined scopes per target.
    scopes_by_target: dict[TargetSpecifier, list[str]]

    # All servers defined in the specification with an HTTPS scheme.
    https_servers: list[str]


class OpenAPISpecAnalyzer:
    def analyze(self, spec: oa.OpenAPI) -> SpecAnalysis:
        targets: list[TargetSpecifier] = []
        scopes: t.Set[str] = set()
        scopes_by_target: dict[TargetSpecifier, list[str]] = {}

        for path, path_schema in spec.paths.items():
            for method in HTTP_METHODS:
                if operation := getattr(path_schema, method.lower()):
                    target = TargetSpecifier.create(method, path)
                    targets.append(target)
                    scopes_by_target[target] = []
                    for requirement in operation.security or []:
                        if (
                            len(requirement) == 1
                            and (globus_auth_scopes := requirement.get("GlobusAuth"))
                            and len(globus_auth_scopes) == 1
                        ):
                            scopes.add(globus_auth_scopes[0])
                            scopes_by_target[target].append(globus_auth_scopes[0])

        http_servers: list[str] = [
            server.url
            for server in spec.servers
            if urlparse(server.url).scheme == "https"
        ]

        return SpecAnalysis(
            targets=targets,
            scope_strings=sorted(scopes),
            scopes_by_target=scopes_by_target,
            https_servers=http_servers,
        )
