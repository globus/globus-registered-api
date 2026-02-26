[🏠 Documentation home](../README.md)
» [Tutorials](README.md)
» Create your first Registered API

# Create your first Registered API


Once you've followed the tutorial to [install GRA and log in](install.md),
you're ready to publish your first Registered API!

This tutorial will guide you through the steps necessary
to publish a single Registered API that can list your flows
in the Globus Flows service.


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [Initialize the repository](#initialize-the-repository)
- [Add a target](#add-a-target)
- [Review roles](#review-roles)
- [Build and publish](#build-and-publish)
- [Recap](#recap)
- [Next steps](#next-steps)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Initialize the repository

The Globus Registered API CLI needs a place to store its configuration,
so the first step is to create a new directory, called `list-flows-demo`,
and change directories into it:

```shell
mkdir list-flows-demo
cd list-flows-demo
```

Then, initialize a new Globus Registered API repository
using the `gra init` command:

```shell
gra init
```

You'll be asked if your service has an existing OpenAPI specification.
For the purposes of this tutorial, the answer is "yes".
(Outside of this tutorial, you can respond "yes"
if you have an OpenAPI specification in JSON or YAML format.)

```text
Does your service have an OpenAPI specification? [Y/n]: y
```

Type "y" and press Enter to affirm that you have an OpenAPI specification.
Copy and paste this URL, which is the location of the Globus Flows service
OpenAPI specification in JSON format:

```text
https://globusonline.github.io/globus-flows/flows.openapi.json
```

You'll then be informed that multiple base servers were found,
and asked if you want to use either of them:

```text
I found multiple HTTPS servers in the specification:
  - https://flows.globus.org/
  - https://sandbox.flows.automate.globus.org
Would you like to use one of these as the service base URL? [y/N]:
```

Answer "yes", and select `https://flows.globus.org/` as the
[service base URL](../reference/glossary.md#service-base-url).

You'll see a success message, and `gra` will exit.

There is now a `.globus_registered_api/` subdirectory
in the `list-flows-demo/` directory that you created.
It is recommended that you commit this directory and its files
to a version control system, like git.


## Add a target

For this tutorial, we're going to define a
[target](../reference/glossary.md#target)
that refers to the Globus Flows API call that lists your flows.

First, run this command:

```shell
gra manage
```

The `gra manage` command is an interactive menu-based tool.
Note that the screens shown below may differ slightly,
but the goal remains the same:
registering the `/flows (GET)` route as new target.

You will see this main menu:

```text
 Select a Menu Option:
  >  1. Targets
     2. Roles
     3. <Exit>
```

Select "Targets" from the menu and press `[ENTER]`,
and you'll see this list of options related to targets:

```text
 Select a Menu Option:
     1. Display Target
     2. List Targets
     3. Modify Target
  >  4. Add Target
     5. Remove Target
     6. <Back>
     7. <Exit>
```

Select "Add Target" from the menu and press `[ENTER]`.

You will then see a number of available targets listed.
The one we're interested in is `/flows (GET)`,
which is number 3 in the list shown below.

```text
 Select a Target:
     1. <Enter custom path and method>
     2. /batch/runs (POST)
  >  3. /flows (GET)
     4. /flows (POST)
     5. /flows/validate (POST)
     6. /flows/{flow_id} (DELETE)
     7. /flows/{flow_id} (GET)
     8. /flows/{flow_id} (PUT)
     9. /flows/{flow_id}/run (POST)
     ...
```

Select `/flows (GET)` from the list and press `[ENTER]`.

You'll then be prompted to create an alias for the target:

```text
Target Alias:
```

Aliases are human-readable names for the combination
of the HTTP method and API path.
In this tutorial, type `list-flows` and press `[ENTER]`.

You'll then be prompted for a description.
You can accept the default, "Retrieve all Flows", by pressing `[ENTER]`.

You'll see output similar to this:

```text
╭──────────────────────────────────── list-flows (GET /flows) ────────────────────────────────────╮
│ TargetConfig(                                                                                   │
│     path='/flows',                                                                              │
│     method='GET',                                                                               │
│     alias='list-flows',                                                                         │
│     description='Retrieve all Flows',                                                           │
│     security=ImputedSecurity(                                                                   │
│         globus_auth_scopes=[                                                                    │
│             'https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/view_flows',   │
│             'https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/manage_flows', │
│             'https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/all'           │
│         ]                                                                                       │
│     ),                                                                                          │
│     registered_api_id=None                                                                      │
│ )                                                                                               │
╰─────────────────────────────────────────────────────────────────────────────────────────────────╯
```

The menu of target options will be displayed again:

```text
 Select a Menu Option:
     1. Display Target
     2. List Targets
     3. Modify Target
     4. Add Target
     5. Remove Target
  >  6. <Back>
     7. <Exit>
```

Select `<Back>` and press `[ENTER]` to return to the main menu.


## Review roles

By default, only your Globus Auth identity will have access
to the Registered APIs that you publish.
That's sufficient for the purposes of this tutorial,
but let's take a moment to see the default role that's defined.

```text
 Select a Menu Option:
     1. Targets
  >  2. Roles
     3. Exit
```

At the main menu shown above, select `Roles` and press `[ENTER]`.
Similar to the Targets menu, you'll see a number of menu options
that let you review and edit the roles that will be assigned
to all the Registered APIs you define:

```text
 Select a Menu Option:
  >  1. List Roles
     2. Modify Role
     3. Add Role
     4. Remove Role
     5. Back
     6. Exit
```

Select `List Roles` as shown above and press `[ENTER]`.
You'll see a table of roles displayed, similar to this:

```text
┏━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃   ┃ Entity Type ┃ Identifier          ┃ Access Level ┃
┡━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 1 │ identity    │ user@example.domain │ owner        │
└───┴─────────────┴─────────────────────┴──────────────┘
 Select a Menu Option:
     1. List Roles
     2. Modify Role
     3. Add Role
     4. Remove Role
     5. Back
  >  6. Exit
```

Select `Exit` from the menu and press `[ENTER]`.

If you're using a version control system like git,
remember to commit changes to the files in the `.globus_registered_api/` subdirectory.


## Build and publish

Now that a target has been added, and roles have been reviewed,
it's time to build and publish the repository to the Globus Flows service!

First, build the repository by running the `gra build` command:

```console
$ gra build
Loaded OpenAPI specification from https://globusonline.github.io/globus-flows/flows.openapi.json.
Successfully computed manifest artifact
Wrote manifest to disk (.globus_registered_api/manifest.json)
```

Next, run the `gra publish` command and confirm that you want to proceed:

```console
$ gra publish
Preparing to publish 1 following targets:
  - list-flows
Would you like to proceed? [y/N]: y
```

You'll see output similar to this:

```text
Creating registered API for list-flows...
  Created with ID: 00000000-0000-0000-0000-000000000000
```

Copy the Registered API ID.
You'll need it for the next part of the tutorial!

If you lose track of the list-flows Registered API ID,
you can use the `gra api list` command to find it again:

```console
$ gra api list
ID                                   | Name
-------------------------------------|-----
00000000-0000-0000-0000-000000000000 | list-flows
```


## Recap

In this part of the tutorial, you've worked through

* Initializing a new Globus Registered API repository
* Defining a target
* Reviewing the roles that will be assigned to all the Registered APIs
* Building and publishing the Registered API to the Globus Flows service


## Next steps

Remember to copy the newly-created Registered API ID;
in the next part of the tutorial you'll actually use it in a flow.

* Continue the tutorial: [Use a Registered API in a flow](use-a-registered-api.md)
* [🏠 Documentation home](../README.md)
