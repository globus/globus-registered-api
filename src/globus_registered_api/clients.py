# This file is a part of globus-registered-api.
# https://github.com/globus/globus-registered-api
# Copyright 2025-2026 Globus <support@globus.org>
# SPDX-License-Identifier: Apache-2.0

from globus_sdk import AuthClient
from globus_sdk import GlobusApp

from globus_registered_api import ExtendedFlowsClient


def create_auth_client(app: GlobusApp) -> AuthClient:
    """
    Create an AuthClient for the given app.

    :param app: A Globus app instance to use for authentication
    :return: An AuthClient configured with the provided app
    """
    return AuthClient(app=app)


def create_flows_client(app: GlobusApp) -> ExtendedFlowsClient:
    """
    Create an ExtendedFlowsClient for the given app.

    :param app: A Globus app instance to use for authentication
    :return: An ExtendedFlowsClient configured with the provided app
    """
    return ExtendedFlowsClient(app=app)
