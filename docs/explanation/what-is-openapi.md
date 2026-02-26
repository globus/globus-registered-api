[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is OpenAPI?

# Explanation: What is OpenAPI?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [What is OpenAPI?](#what-is-openapi)
- [How do I get an OpenAPI specification document?](#how-do-i-get-an-openapi-specification-document)
- [Am I required to have OpenAPI specification document?](#am-i-required-to-have-openapi-specification-document)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is OpenAPI?

[OpenAPI](https://www.openapis.org/)
is an industry standard for describing web APIs.

Globus services all provide APIs,
and OpenAPI is an excellent way to document those APIs.

[Registered APIs](what-is-a-registered-api.md#what-is-a-registered-api)
refer to service APIs that have been registered with the Globus Flows service.

The Globus Flows service currently supports OpenAPI 3.1.
Older versions, like OpenAPI 3.0, are not supported.


## How do I get an OpenAPI specification document?

Many popular web frameworks are able to generate OpenAPI specification documents
automatically, or via plugins.

For example, FastAPI, a popular Python web framework,
[automatically generates OpenAPI specification documents](https://fastapi.tiangolo.com/reference/openapi/docs/).
Others, like Django and Flask, may require a plugin
to generate OpenAPI specifications.


## Am I required to have OpenAPI specification document?

No.
If you don't have an OpenAPI specification document,
the Globus Registered API CLI can still create and manage Registered APIs for you,
though you will have to manually define targets.
