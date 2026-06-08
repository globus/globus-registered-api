#!/usr/bin/env bash

set -e

# Amend the CHANGELOG.
git add CHANGELOG.rst
git commit --amend -m 'Update project metadata'
