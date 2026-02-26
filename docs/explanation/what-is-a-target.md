[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a target?

# Explanation: What is a target?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [What is a target?](#what-is-a-target)
- [How are targets and Registered APIs related?](#how-are-targets-and-registered-apis-related)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is a target?

A target is a single API route, like `GET /resources`.

When users initialize a Globus Registered API repository using the `gra init` command,
the GRA CLI will ask for the URL to -- or a local file path for --
an OpenAPI specification document.
When the OpenAPI document is loaded, users can then choose one or more targets
to configure and eventually publish as Registered APIs in the Globus Flows service.

For example, an OpenAPI specification might define five individual APIs:

| Name                | HTTP method | Path                 |
|---------------------|-------------|----------------------|
| Create a new thing  | `POST`      | `/things`            |
| List all the things | `GET`       | `/things`            |
| Show one thing      | `GET`       | `/things/{thing_id}` |
| Update one thing    | `PATCH`     | `/things/{thing_id}` |
| Delete one thing    | `DELETE`    | `/things/{thing_id}` |

The GRA CLI would present all of these to the user as targets.
The user might create Registered APIs for all of these targets,
or they might choose some subset of targets to publish.

Targets may have different types of parameters that must be provided.
In the example table above, the last three paths include the text `{thing_id}`;
this indicates that those three targets require a path parameter.


## How are targets and Registered APIs related?

A target is one part of a Registered API.

Registered APIs include additional information, such as
[roles](what-is-a-role.md).
