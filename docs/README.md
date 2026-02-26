🏠 Documentation home

# Globus Registered API

_Manage Registered APIs in the Globus Flows service._

----

The Globus Flows service allows users to create and run state machines named "flows".
In the past, Flows' capabilities could be extended only be creating an Action Provider
-- a service that conforms to a specific API contract.

The Globus Flows service is beginning to support a new pre-GA feature: Registered APIs.
A Registered API allows a flow to make an HTTP request to an existing API
without requiring any new infrastructure.


## Table of contents

[**Tutorial**](tutorial/README.md)

* [Install and log in](tutorial/install.md#install-and-log-in)
* [Create a Registered API](tutorial/create-a-registered-api.md#create-your-first-registered-api)
* [Use a Registered API](tutorial/use-a-registered-api.md#use-a-registered-api-in-a-flow)


[**How-to**](how-to/README.md)

* [How do I fix an OpenAPI document?](how-to/openapi-fixes.md#fixing-an-openapi-document-by-hand)


[**Explanation**](explanation/README.md)

* [What is a Registered API?](explanation/what-is-a-registered-api.md#what-is-a-registered-api)
* [What is the Registered API CLI?](explanation/what-is-a-registered-api.md#what-is-the-globus-registered-api-cli)
* [What is OpenAPI?](explanation/what-is-openapi.md#what-is-openapi)
* [What is a service base URL?](explanation/what-is-a-service-base-url.md#what-is-a-service-base-url)
* [What is a target?](explanation/what-is-a-target.md#what-is-a-target)
* [What is a scope?](explanation/what-is-a-scope.md#what-is-a-scope)
* [What is a role?](explanation/what-is-a-role.md#what-is-a-role)
* [What is a parameter?](explanation/what-is-a-parameter.md#what-is-a-parameter)


[**Reference**](reference/README.md#reference)

* [API commands](reference/api-commands.md#api-commands)
* [OpenAPI requirements](reference/openapi-requirements.md#openapi-requirements)
* [Environment variables](reference/env-vars.md#environment-variables)
* [Shell completion](reference/shell-completion.md#shell-completion)
* [Glossary](reference/glossary.md#glossary)
