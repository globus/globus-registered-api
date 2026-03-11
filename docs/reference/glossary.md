[🏠 Documentation home](../README.md)
» [Reference](README.md)
» Glossary

# Glossary


A number of terms are used throughout this documentation.
This glossary offers a starting point for understanding various terms.


## Table of contents

* [Service base URL](#service-base-url)
* [Target](#target)


## Terms

* <a name="service-base-url"></a> **Service base URL**

  OpenAPI definitions generally use relative paths, like `/v2/resource`,
  to define API endpoints. This path may be hosted on multiple domains,
  including development environment.

  Therefore, OpenAPI allows one or more base URLs to be defined.
  These are stored in the OpenAPI definition separate from the relative paths.

  When the service base URL is combined with a relative path,
  it forms a complete API endpoint.

  For example, if the service base URL is `https://example.domain`,
  and if a relative path like `/v2/resource` is defined, then the complete URL is:

  ```text
  https://example.domain/v2/resource
  ```

* <a name="target"></a> **Target**

  A "target" refers to a specific combination of
  an HTTP method (like `GET`) and a relative path (like `/v2/resource`).

  A single target, when combined with roles and other metadata,
  forms a single Registered API.
