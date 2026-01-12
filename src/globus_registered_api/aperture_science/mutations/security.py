from globus_sdk import Scope

import typing as t

from ._common import SchemaMutation
from globus_registered_api.config import GlobusAuthConfig
from globus_registered_api.domain import TargetSpecifier


class InjectDefaultSecuritySchemas(SchemaMutation):
    """
    A schema mutation which injects standard Globus Auth components.

    This mutation will insert (if they don't already exist):
        *   A top-level component at `components/securitySchemes/GlobusAuth`
        *   Operation-level "GlobusAuth" security requirements with configured scopes.
    """

    def __init__(self, config: GlobusAuthConfig):

        self.scope_descriptions = {
            scope: scope_config["description"] or ""
            for scope, scope_config in config.get("scopes", {}).items()
        }

        self._all_scopes: list[Scope] = []
        self._target_specifier_scopes: dict[TargetSpecifier, list[Scope]] = {}

        self._init_scope_mappings(config)

    def _init_scope_mappings(self, config: GlobusAuthConfig) -> None:
        for scope, scope_config in config.get("scopes", {}).items():
            targets = scope_config.get("targets", [])

            if targets == "*":
                self._all_scopes.append(scope)
                continue

            for target in targets:
                specifier = TargetSpecifier.load(target)
                self._target_specifier_scopes.setdefault(specifier, []).append(scope)

    def mutate(
        self,
        root_schema: dict[str, t.Any],
    ) -> None:
        self._insert_component_security_schema(root_schema)
        for specifier, operation_schema in _iter_operations(root_schema):
            self._insert_operation_security_schema(specifier, operation_schema)


    def _insert_component_security_schema(self, root_schema: dict[str, t.Any]) -> None:
        components = root_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})

        if "globus_auth" not in security_schemes:
            security_schemes["GlobusAuth"] = {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://auth.globus.org/v2/oauth2/authorize",
                        "tokenUrl": "https://auth.globus.org/v2/oauth2/token",
                        "scopes": {
                            str(scope): description
                            for scope, description in self.scope_descriptions.items()
                        },
                    }
                }
            }

    def _insert_operation_security_schema(
        self,
        specifier: TargetSpecifier,
        operation_schema: dict[str, t.Any],
    ) -> None:
        security = operation_schema.setdefault("security", [])
        if not any("GlobusAuth" in schema for schema in security):
            scopes = self._all_scopes + self._target_specifier_scopes.get(specifier, [])

            security.extend({"GlobusAuth": [str(s)]} for s in scopes)




def _iter_operations(
    root_schema: dict[str, t.Any]
) -> t.Iterator[tuple[TargetSpecifier, dict[str, t.Any]]]:
    """
    Iterate over all operations in the OpenAPI schema.
    """

    for operation_path, path_schema in root_schema.get("paths", {}).items():
        for method_name, operation_schema in path_schema.items():
            # TODO - incorporate content type
            yield TargetSpecifier(method_name, operation_path), operation_schema
