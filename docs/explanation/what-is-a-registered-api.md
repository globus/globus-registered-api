[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a Registered API?

# Explanation: What is a Registered API?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [What is a Registered API?](#what-is-a-registered-api)
- [What is the Globus Registered API CLI?](#what-is-the-globus-registered-api-cli)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is a Registered API?

Registered APIs are a new feature of the
[Globus Flows](https://docs.globus.org/api/flows/)
service.

Quoting from the page linked above:

> Globus Flows provides secure, managed automation of complex workflows at scale.
> These automations, called flows, are series of actions
> that can perform common chores

Registered APIs are new type of action that a flow can perform.
They allow users to define API routes and parameters
which a flow may call directly.

For example, Globus Groups provides an API for
[getting information about a group](https://docs.globus.org/api/groups/#get_group).
The API route looks like this:

```text
GET /v2/groups/{group_id}
```

By registering this API with the Globus Flows service,
you can then call it from within a flow.


## What is the Globus Registered API CLI?

The Globus Registered API CLI allows users to manage a collection of Registered APIs
associated with an existing OpenAPI specification document.
It supports mass-publication of, and updates to, the collection of Registered APIs.
