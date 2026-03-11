[🏠 Documentation home](../README.md)
» [Reference](README.md)
» API commands

# API commands

The `gra api` commands perform direct API calls to the Globus Flows service.
They differ from the CLI's high-level management commands
-- like `gra manage` and `gra publish` --
in that they perform a direct API call.


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [`gra api create`](#gra-api-create)
- [`gra api list`](#gra-api-list)
- [`gra api show`](#gra-api-show)
- [`gra api update`](#gra-api-update)
- [`gra api delete`](#gra-api-delete)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## `gra api create`

The `gra api create` command creates a Registered API.

At minimum, a name, description, and target definition are required:

```shell
gra api create "NAME" --description "DESCRIPTION" --target TARGET.json
```

A number of command options are available:

* `--description` sets the description of the Registered API.
* `--owner` assigns the Owner role to a given identity or group.

  The value of this option must be an identity URN or a group URN.
  This option can be given multiple times, to assign multiple users or groups.
  The account creating the Registered API must be one of the identities,
  or must be a member of one of the groups.

  For example:

  ```shell
  $ gra api create "NAME" \
      --owner "urn:globus:auth:identity:11111111-1111-1111-1111-111111111111" \
      --owner "urn:globus:groups:id:22222222-2222-2222-2222-222222222222"
  ```

* `--administrator` assigns the Administrator role to a given identity or group.

  The value of this option must be an identity URN or a group URN.
  Like the `--owner` option, this can be given multiple times.
  For example:

  ```shell
  $ gra api create $API_ID \
      --administrator "urn:globus:auth:identity:33333333-3333-3333-3333-333333333333" \
      --administrator "urn:globus:groups:id:44444444-4444-4444-4444-444444444444"
  ```

* `--viewer` assigns the Viewer role to a given identity or group.

  The value of this option must be an identity URN or a group URN.
  Like the `--owner` option, this can be given multiple times.
  For example:

  ```shell
  $ gra api create $API_ID \
      --viewer "urn:globus:auth:identity:55555555-5555-5555-5555-555555555555" \
      --viewer "urn:globus:groups:id:66666666-6666-6666-6666-666666666666"
  ```

* `--target` must be a file containing the API target definition.

Run `gra api create --help` to see all available options.


## `gra api list`

The `gra api list` command lists Registered API that you have access to.

Example:

```console
$ gra api list
ID                                   | Name
-------------------------------------|-----
00000000-0000-0000-0000-000000000000 | list-flows
```

By default, only Registered APIs for which your account has the "Owner" role
are listed (including via membership in a group that has the "Owner" role).

The `--filter-roles` argument can be given to override this default.
Valid values are:

* `--filter-roles owner`
* `--filter-roles administrator`
* `--filter-roles viewer`

The `--filter-roles` argument can be given multiple times
to show Registered APIs that you have ANY of the given roles for.
For example, to show Registered APIs for which you have
Owner OR Administrator roles:

```shell
$ gra api list --filter-roles owner --filter-roles administrator
```

Run `gra api list --help` to show all available options.


## `gra api show`

The `gra api show` command gets information about a Registered API by ID.

For example, you might see output like this after following the
[tutorial](../tutorial/create-a-registered-api.md):

```shell
$ gra api show 00000000-0000-0000-0000-000000000000
ID:             00000000-0000-0000-0000-000000000000
Name:           list-flows
Description:    Retrieve all Flows
Owners:         urn:globus:auth:identity:11111111-1111-1111-1111-111111111111
Administrators:
Viewers:
Created:        2026-03-01T00:00:00.0+00:00
Updated:        2026-03-01T00:00:00.0+00:00
```

Run `gra api show --help` to see all available options.


## `gra api update`

The `gra api update` command updates a Registered API by ID.
For example:

```shell
$ gra api update 00000000-0000-0000-0000-000000000000 --name 'A better name'
```

A number of command options are available:

* `--name` updates the name of the Registered API.
* `--description` updates the description of the Registered API.
* `--owner` **overwrites** the existing owner role of the Registered API.

  The value of this option must be an identity URN or a group URN.
  This option can be given multiple times, to assign multiple users or groups.
  For example:

  ```shell
  $ gra api update $API_ID \
      --owner "urn:globus:auth:identity:11111111-1111-1111-1111-111111111111" \
      --owner "urn:globus:groups:id:22222222-2222-2222-2222-222222222222"
  ```

* `--administrator` **overwrites** the existing administrator role of the Registered API.

  The value of this option must be an identity URN or a group URN.
  Like the `--owner` option, this can be given multiple times.
  For example:

  ```shell
  $ gra api update $API_ID \
      --administrator "urn:globus:auth:identity:33333333-3333-3333-3333-333333333333" \
      --administrator "urn:globus:groups:id:44444444-4444-4444-4444-444444444444"
  ```

* `--no-administrators` **erases** the existing administrator role of the Registered API.

  It cannot be used with the `--administrator` option.

* `--viewer` **overwrites** the existing viewer role of the Registered API.

  The value of this option must be an identity URN or a group URN.
  Like the `--owner` option, this can be given multiple times.
  For example:

  ```shell
  $ gra api update $API_ID \
      --viewer "urn:globus:auth:identity:55555555-5555-5555-5555-555555555555" \
      --viewer "urn:globus:groups:id:66666666-6666-6666-6666-666666666666"
  ```

* `--no-viewer` **erases** the existing viewer role of the Registered API.

  It cannot be used with the `--viewer` option.

* `--target` overwrites the existing target information.
  The value of this option must be a file containing the new target definition.

  Individual target properties (like the HTTP method or route) cannot be changed;
  the entire target definition must be overwritten.

Run `gra api update --help` to see all available options.


## `gra api delete`

The `gra api delete` command deletes a Registered API by ID.

For example

```shell
$ gra api delete 00000000-0000-0000-0000-000000000000
```
