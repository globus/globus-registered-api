[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a service base URL?

# Explanation: What is a service base URL?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is a service base URL?

When you run the `gra init` command,
you will be asked for the service base URL.

It is common for the same service to run in different environments.
For example, the service might run in a production environment
with a URL like `https://domain.example/`,
while development versions of the service might run in a beta environment
with a URL like `https://beta.domain.example/`.

The service base URL is that differentiated URL --
either `https://domain.example/` or `https://beta.domain.example/`.

This is why [targets](what-is-a-target.md) in the OpenAPI specification
have relative paths like `/v2/resource`;
the relative path is appended to the service base URL
to form the complete URL of the API:

* `https://domain.example/v2/resource`
* `https://beta.domain.example/v2/resource`
