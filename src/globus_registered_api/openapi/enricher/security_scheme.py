# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

import openapi_pydantic as oa

from globus_registered_api.config import RegisteredAPIConfig
from globus_registered_api.config import TargetConfig
from globus_registered_api.domain import TargetSpecifier

from .interface import SchemaMutation


class InjectSecuritySchemes(SchemaMutation):
    """
    A schema mutation which injects standard Globus Auth components.

    This mutation will insert (if they don't already exist):
        *   Operation-level "GlobusAuth" security requirements with configured scopes.
    """

    def __init__(self, config: RegisteredAPIConfig) -> None:
        self._config = config

    def mutate(self, schema: oa.OpenAPI) -> None:
        for target in self._config.targets:
            operation = self._ensure_exists(schema, target.specifier)
            self._validate_and_update_operation(operation, target)

    def _ensure_exists(
        self, schema: oa.OpenAPI, specifier: TargetSpecifier
    ) -> oa.Operation:
        """
        Ensure the existence of an Operation for the provided TargetSpecifier.
        If the specifier does not exist, it is created.

        :returns: The existing or newly created Operation.
        """
        # Ensure that the 'paths' key exists on the top-level schema.
        paths = schema.paths or oa.Paths()
        schema.paths = paths

        # Ensure that the specific path exists in the 'paths' dict.
        path_item = paths.setdefault(specifier.path, oa.PathItem())

        # Ensure that the method exists for that path.
        method_key = specifier.method.lower()
        if (existing_operation := getattr(path_item, method_key, None)) is not None:
            return existing_operation  # type: ignore[no-any-return]

        new_operation = oa.Operation()
        setattr(path_item, method_key, new_operation)
        return new_operation

    def _validate_and_update_operation(
        self, operation: oa.Operation, target: TargetConfig
    ) -> None:
        """
        Ensure every operation has the configured security scopes defined as
        isolated security requirements in the form:

        ```yaml
        /my-resource:
            get:
                security:
                    - GlobusAuth: ["resource:read"]
                    - GlobusAuth: ["resource:all"]
        ```

        Any missing scopes are inserted automatically.
        """
        security = operation.security or []

        # Identify any scopes already present on the model.
        predefined_scopes: set[str] = set()
        for requirement in security:
            globus_scopes = requirement.get("GlobusAuth")
            if globus_scopes and len(globus_scopes) == 1:
                predefined_scopes.add(globus_scopes[0])

        # Insert any missing scopes to the start of the list:
        #    Given the operation's level of specificity, this ignores content-types.
        for scope in target.scope_strings:
            if scope not in predefined_scopes:
                security.insert(0, {"GlobusAuth": [scope]})

        # Only update the model if we made changes, to avoid unnecessary mutations.
        if security:
            operation.security = security
