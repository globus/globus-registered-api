# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from .selector import prompt_multiselection
from .selector import prompt_selection

__all__ = (
    "prompt_selection",
    "prompt_multiselection",
)
