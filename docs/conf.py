# This file is a part of globus-registered-api.
# https://github.com/globusonline/globus-registered-api
# Copyright 2025 Globus <support@globus.org>
# SPDX-License-Identifier: MIT

import pathlib
import tomllib

# General configuration
# ---------------------

# The suffix of source filenames.
source_suffix = ".rst"

# The main toctree document.
master_doc = "index"

# General information about the project.
project = "Globus Registered API"
copyright = "2025 Globus"

# Extract the project version.
pyproject_ = pathlib.Path(__file__).parent.parent / "pyproject.toml"
info_ = tomllib.loads(pyproject_.read_text())
version = release = info_["project"]["version"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# Don't show "Powered by" text.
html_show_sphinx = False


# HTML theme configuration
# ------------------------

html_theme = "alabaster"
html_theme_options = {
    "description": "Manage Registered APIs in the Globus Flows service.",
}

# Don't copy source .rst files into the built documentation.
html_copy_source = False
