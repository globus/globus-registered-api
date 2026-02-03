# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0
import typing as t

import globus_sdk.config
import openapi_pydantic as oa
from globus_sdk import Scope

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.domain import HTTP_METHODS
from globus_registered_api.domain import TargetSpecifier
from globus_registered_api.openapi.enchricher.interface import SchemaMutation


class _GlobusAuthSecurityScheme(oa.SecurityScheme):

    def __init__(self, config: RegisteredAPIConfig, environment: str) -> None:
        auth_url = globus_sdk.config.get_service_url("auth", environment=environment)
        scopes = {
            str(scope): scope_config.get("description") or ""
            for scope, scope_config in config["globus_auth"]["scopes"].items()
        }

        super().__init__(
            type="oauth2",
            flows=oa.OAuthFlows(
                authorizationCode=oa.OAuthFlow(
                    authorizationUrl=f"{auth_url}v2/oauth2/authorize",
                    tokenUrl=f"{auth_url}v2/oauth2/token",
                    scopes=scopes,
                )
            ),
        )

    def verify_contained_in(self, other: t.Any) -> None:
        """
        Confirm that `other` contains this security scheme.

        Scope descriptions are not compared, only scope keys.

        :raises TypeError: if `other` is not a SecurityScheme.
        :raises ValueError: if `other` does not match this scheme.
        """

        if not isinstance(other, oa.SecurityScheme):
            raise TypeError(f"Unsupported security scheme comparison: {type(other)}.")

        if self.type != other.type:
            raise ValueError(f"Security scheme mismatch: {self.type} != {other.type}.")

        oflows, sflows = other.flows, self.flows
        if oflows is None or sflows is None:
            raise ValueError("'flows' cannot be None.")

        ocode, scode = oflows.authorizationCode, sflows.authorizationCode
        if ocode is None or scode is None:
            raise ValueError("'authorizationCode' flow cannot be None.")

        for key in ("authorizationUrl", "tokenUrl"):
            oval, sval = getattr(ocode, key), getattr(scode, key)
            if oval != sval:
                raise ValueError(f"'{key}': {oval} != {sval}.")

        oscopes, sscopes = ocode.scopes, scode.scopes
        if oscopes and sscopes:
            if missing := (sscopes.keys() - oscopes.keys()):
                raise ValueError(f"Missing scopes in security scheme: {missing}.")


class InjectDefaultSecuritySchemas(SchemaMutation):
    """
    A schema mutation which injects standard Globus Auth components.

    This mutation will insert (if they don't already exist):
        *   A top-level component at `components/securitySchemes/GlobusAuth`
        *   Operation-level "GlobusAuth" security requirements with configured scopes.
    """

    def __init__(self, config: RegisteredAPIConfig, environment: str) -> None:
        self._security_scheme = _GlobusAuthSecurityScheme(config, environment)

        self._wildcard_scopes: list[Scope] = []
        self._target_specifier_scopes: dict[TargetSpecifier, list[Scope]] = {}

        # Populate the scope indices
        for scope, scope_config in config["globus_auth"]["scopes"].items():
            targets = scope_config.get("targets", [])

            if targets == "*":
                self._wildcard_scopes.append(scope)
                continue

            for target in targets:
                specifier = TargetSpecifier.load(target)
                self._target_specifier_scopes.setdefault(specifier, []).append(scope)

    def mutate(self, schema: oa.OpenAPI) -> None:
        self._validate_and_update_components(schema)

        for path_str, path in (schema.paths or {}).items():
            for method in HTTP_METHODS:
                if operation := getattr(path, method.lower(), None):
                    self._validate_and_update_operation(path_str, method, operation)

    def _validate_and_update_components(self, schema: oa.OpenAPI) -> None:
        """
        Ensure the components security sufficiently defines the GlobusAuth scheme:

        // editorconfig-checker-disable
        ```yaml
        components:
          securitySchemes:
            GlobusAuth:
              type: oauth2
              flows:
                authorizationCode:
                  authorizationUrl: https://auth.globus.org/v2/oauth2/authorize
                  tokenUrl: https://auth.globus.org/v2/oauth2/token
                  scopes:
                    resource:all: Full access to the resource.
                    resource:read: Read-only access to the resource.
        ```
        // editorconfig-checker-enable

        If the scheme already exists, it is validated.
        Otherwise, it is inserted.
        """
        components = schema.components or oa.Components()
        schema.components = components

        security_schemes = components.securitySchemes or {}
        components.securitySchemes = security_schemes

        if existing_scheme := security_schemes.get("GlobusAuth", None):
            # If the scheme already exists, ensure it matches our expected config.
            self._security_scheme.verify_contained_in(existing_scheme)

        else:
            # If it doesn't exist, insert it.
            security_schemes["GlobusAuth"] = self._security_scheme

    def _validate_and_update_operation(
        self,
        path: str,
        method: str,
        operation: oa.Operation,
    ) -> None:
        """
        Ensure every operation has the configured security scopes defined as
        isolated security requirements in the form:

        // editorconfig-checker-disable
        ```yaml
        /my-resource:
          get:
            security:
              - GlobusAuth: ["resource:all"]
              - GlobusAuth: ["resource:read"]
        ```
        // editorconfig-checker-enable

        Any missing scopes are inserted automatically.
        """
        security = operation.security or []

        # Identify any scopes already present on the model.
        registered_scopes: set[str] = set()
        for requirement in security:
            globus_scopes = requirement.get("GlobusAuth")
            if globus_scopes and len(globus_scopes) == 1:
                registered_scopes.add(globus_scopes[0])

        # Insert any target-specifier matched scopes to the start of the list:
        #    Given the operation's level of specificity, this ignores content-types.
        for specifier, scopes in self._target_specifier_scopes.items():
            if specifier.path == path and specifier.method == method:
                for scope in scopes:
                    scope_str = str(scope)
                    if scope_str not in registered_scopes:
                        registered_scopes.add(scope_str)
                        security.insert(0, {"GlobusAuth": [scope_str]})

        # Insert any wildcard scopes to the start of the list:
        for scope in self._wildcard_scopes:
            scope_str = str(scope)
            if scope_str not in registered_scopes:
                registered_scopes.add(scope_str)
                security.insert(0, {"GlobusAuth": [scope_str]})

        if security:
            operation.security = security
