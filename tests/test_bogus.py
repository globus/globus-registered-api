# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: MIT

import pytest

import globus_registered_api.cli


def test_bogus_subcommand(capsys):
    with pytest.raises(SystemExit):
        globus_registered_api.cli.bogus()

    stdout, _ = capsys.readouterr()
    assert "bogus" in stdout
