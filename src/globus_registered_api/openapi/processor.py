# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

"""
Facade for OpenAPI target processing.

This module provides a simplified interface for OpenAPI processing
by coordinating loader, selector, and reducer components.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import openapi_pydantic as oa

from globus_registered_api.openapi.loader import load_openapi_spec
from globus_registered_api.openapi.reducer import OpenAPITarget
from globus_registered_api.openapi.reducer import reduce_to_target
from globus_registered_api.openapi.selector import TargetSpecifier
from globus_registered_api.openapi.selector import find_target


@dataclass
class ProcessingResult:
    """Result of target processing."""

    target: OpenAPITarget
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to the format expected by POST /registered_api."""
        return self.target.to_dict()


def process_target(
    spec_or_path: oa.OpenAPI | str | Path,
    target: TargetSpecifier,
) -> ProcessingResult:
    """
    Process an OpenAPI spec to extract a target endpoint.

    This is the primary entry point for target extraction. It coordinates
    loading, selection, and reduction into a single operation.

    For fine-grained control, use the underlying modules directly:
    - `loader.load_openapi_spec()` - Parse OpenAPI files
    - `selector.find_target()` - Locate targets in a spec
    - `reducer.reduce_to_target()` - Extract target with dependencies

    :param spec_or_path: OpenAPI spec object or path to spec file
    :param target: Target specifier (method, path, optional content-type)
    :return: ProcessingResult containing the reduced spec
    :raises OpenAPILoadError: If spec file cannot be loaded
    :raises TargetNotFoundError: If route or method not found
    :raises AmbiguousContentTypeError: If content-type selection is ambiguous
    """
    # Load if given a path
    if isinstance(spec_or_path, (str, Path)):
        spec = load_openapi_spec(spec_or_path)
    else:
        spec = spec_or_path

    # Find and reduce
    target_info = find_target(spec, target)
    openapi_target = reduce_to_target(spec, target_info)

    return ProcessingResult(target=openapi_target)
