# Explanation: What is a scope?

[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a scope?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [What is a scope?](#what-is-a-scope)
- [How do scopes relate to Registered APIs?](#how-do-scopes-relate-to-registered-apis)
  - [Example: Globus Search scopes](#example-globus-search-scopes)
  - [Example: Globus Flows scopes](#example-globus-flows-scopes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is a scope?

When you use a browser or a command line tool for the first time
to interact with a Globus service, you will be asked to consent to
the browser or command line tool accessing information from the Globus service.

For example, when you log into the
[Globus Web App](https://app.globus.org/)
for the first time, you'll be asked something like this:

> **Globus Web App would like to:**
>
> ✅ Search for data using your identities and groups \
> ✅ Manage your Globus groups (v2) \
> ✅ Manage data using Globus Transfer \
> ✅ View the identities in your Globus account

A scope is some unit of permission that a tool can have to a Globus service.
Each of the items in the list above is associated with a scope.


## How do scopes relate to Registered APIs?

Scopes must always be associated with Registered APIs.
This allows the Globus Flows service to verify consents
when a user attempts to run a flow.

In the ideal case, the service's OpenAPI specification will already document
which scopes are required for each API route.

However, you might encounter an OpenAPI specification that doesn't document scopes.
In that circumstance, when using the `gra manage` command,
you'll need to list what scopes are required for each [target](what-is-a-target.md).


### Example: Globus Search scopes

Let's look at a concrete example.
The Globus Search service has a total of three scopes, summarized below.
Note that write access ("Ingest") does not imply read access ("Search").

| Scope    | Search | Ingest | Create index | Delete index |
|----------|--------|--------|--------------|--------------|
| `search` | ✅      | -      | -            | -            |
| `ingest` | -      | ✅      | -            | -            |
| `all`    | ✅      | ✅      | ✅            | ✅            |

If you wanted to create a Registered API for the Globus Search service's
[Query - GET](https://docs.globus.org/api/search/reference/get_query/#authentication_authorization)
API route, you would need to provide both the `search` and `all` scopes.

The order of the scopes matters!
Although either the `search` or the `all` scope would allow the API call to succeed,
the `search` scope should be listed first.
If the user hasn't given permission for a flow to use either scope,
they will be prompted to consent to the _first_ scope listed.

Therefore, if an OpenAPI specification is ever missing scope information,
you should list the scopes with the least-permissive scope listed first.

> [!NOTE]
>
> The
> [Globus Search OpenAPI specification](https://search.api.globus.org/autodoc/redoc)
> contains scope information, so you won't actually need to provide scopes yourself.


### Example: Globus Flows scopes

Let's look at another example.
The Globus Flows service has two flows-related scopes,
as well as an `all` scope.
Note that write access implies read access.

**Globus Flows scopes**

| Scope          | Read flows | Write flows |
|----------------|------------|-------------|
| `view_flows`   | ✅          | -           |
| `manage_flows` | ✅          | ✅           |
| `all`          | ✅          | ✅           |

If you wanted to
When creating a Registered API from an existing OpenAPI specification
