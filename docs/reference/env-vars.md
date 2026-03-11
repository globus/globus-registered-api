[🏠 Documentation home](../README.md)
» [Reference](README.md)
» Environment variables

# Environment variables


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [Available environment variables](#available-environment-variables)
  - [`GLOBUS_PROFILE`](#globus_profile)
  - [`GLOBUS_REGISTERED_API_CLIENT_ID`](#globus_registered_api_client_id)
  - [`GLOBUS_REGISTERED_API_CLIENT_SECRET`](#globus_registered_api_client_secret)
  - [`GLOBUS_SDK_ENVIRONMENT`](#globus_sdk_environment)
- [Setting environment variables](#setting-environment-variables)
  - [Linux/macOS](#linuxmacos)
  - [Windows](#windows)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Available environment variables

> [!NOTE]
>
> Examples in the documentation below use shell syntax
> that is typically suitable for Linux and macOS shells.
>
> See the
> [Setting environment variables](#setting-environment-variables)
> section below for syntax for Windows shells.


### `GLOBUS_PROFILE`

The `GLOBUS_PROFILE` environment variable allows users to switch accounts
without logging out of the CLI and logging back in.

The `gra session whoami` command will include the profile
if this environment variable is set.

```console
$ gra session whoami
user@host.example

$ export GLOBUS_PROFILE="alternate"
$ gra session whoami
me@domain.example (profile: alternate)

$ unset GLOBUS_PROFILE
user@host.example
```


### `GLOBUS_REGISTERED_API_CLIENT_ID`

`GLOBUS_REGISTERED_API_CLIENT_ID` is one part of two environment variables
that allow users to interact with the Globus Flows service
via a Globus Auth confidential client.

Users might want to use a confidential client credential to script
building and publishing Registered APIs when a service is updated.
Confidential client credentials can be created in the
[Globus Web App developer settings](https://app.globus.org/settings/developers).

This environment must also have the
[`GLOBUS_REGISTERED_API_CLIENT_SECRET`](#globus_registered_api_client_secret)
environment variable set as well.

Example:

```shell
export GLOBUS_REGISTERED_API_CLIENT_ID="00000000-0000-0000-0000-000000000000"
export GLOBUS_REGISTERED_API_CLIENT_SECRET="the client secret"
```


### `GLOBUS_REGISTERED_API_CLIENT_SECRET`

`GLOBUS_REGISTERED_API_CLIENT_SECRET` is the second part
of two environment variables that allow users to interact
with the Globus Flows service via a Globus Auth confidential client.

This environment must also have the
[`GLOBUS_REGISTERED_API_CLIENT_ID`](#globus_registered_api_client_id)
environment variable set as well.

Example:

```shell
export GLOBUS_REGISTERED_API_CLIENT_ID="00000000-0000-0000-0000-000000000000"
export GLOBUS_REGISTERED_API_CLIENT_SECRET="the client secret"
```


### `GLOBUS_SDK_ENVIRONMENT`

`GLOBUS_SDK_ENVIRONMENT` allows users to target a different Globus environment.

Example:

```shell
export GLOBUS_SDK_ENVIRONMENT="preview"
gra api list
```


## Setting environment variables


### Linux/macOS

On Linux and macOS, environment variables can be set for the console session
or alternatively for a single command:

```shell
# Set a variable for the session
export GLOBUS_PROFILE="alternate"
gra session whoami

# Unset a variable
unset GLOBUS_PROFILE

# Set a variable for a single command
GLOBUS_PROFILE="alternate" gra session whoami
```


### Windows

On Windows, environment variables can be set for the console session:

```powershell
# Set a variable for the session (PowerShell syntax)
$env:GLOBUS_PROFILE = 'alternate'
gra session whoami

# Unset a variable (PowerShell syntax)
$env:GLOBUS_PROFILE = $null
```

```powershell
# Set a variable for the session (cmd.exe syntax)
set GLOBUS_PROFILE=alternate
gra session whoami

# Unset a variable (cmd.exe syntax)
set GLOBUS_PROFILE=
```
