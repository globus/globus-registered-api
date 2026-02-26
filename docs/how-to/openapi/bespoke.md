# How do I fix an OpenAPI document?

[🏠 Documentation home](../README.md)
» [How-to](../README.md)
» How do I fix an OpenAPI document?


## Fixing an OpenAPI document by hand

If an OpenAPI document is incompatible with the Globus Registered API CLI,
it may be possible to fix the document by editing a local copy
and using the edited copy with the `gra init` command.

This document shows an example OpenAPI document for reference.

> [!NOTE]
>
> OpenAPI is a very expressive specification.
> This how-to offers a high-level overview of the OpenAPI format
> and requirements imposed by the Globus Flows service.
> However, you may need to open a support ticket with Globus
> for guidance with a specific OpenAPI document.
>
> Please email [support@globus.org](mailto:support@globus.org) if needed.

The YAML document below is a basic OpenAPI document stub
that suggests that this API route exists:

```text
PATCH /things/{thing_id}
```

A single path parameter, `{thing_id}`, is required
to identify which
It shows that a JSON body is required with a format like this:

```json
{"name": "the new name of the thing"}
```

and further shows that a response like this can be expected
if the thing is successfully updated:

```json
{"status": "ok"}
```

**Example OpenAPI document**

```yaml
openapi: "3.1.0"                                                           # [1]
info:                                                                      #
  title: "Example"                                                         #
  version: "1.0"                                                           #
                                                                           #
servers:                                                                   #
  - url: "https://domain.example"                                          # [2]
                                                                           #
security:                                                                  #
  - bearer_token: []                                                       #
                                                                           #
paths:                                                                     #
  /things/{thing_id}:                                                      # [3]
    parameters:                                                            #
      - name: "thing_id"                                                   #
        in: "path"                                                         #
        description: "The ID of the thing"                                 #
        required: true                                                     #
        schema:                                                            #
          type: "string"                                                   #
          format: "uuid"                                                   #
                                                                           #
    patch:                                                                 # [4]
      summary: "Update a thing"                                            #
      operationId: "update-a-thing"                                        #
                                                                           #
      security:                                                            # [5]
        - GlobusAuth:                                                      #
            - "https://auth.globus.org/scopes/UUID/manage"                 #
        - GlobusAuth:                                                      #
            - "https://auth.globus.org/scopes/UUID/all"                    #
                                                                           #
      requestBody:                                                         #
        description: "Info about the thing to update"                      #
        required: true                                                     #
        content:                                                           #
          application/json:                                                #
            schema:                                                        # [6]
              type: "object"                                               #
              required:                                                    #
                - "name"                                                   #
              properties:                                                  #
                name:                                                      #
                  type: "string"                                           #
                                                                           #
      responses:                                                           #
        "200":                                                             #
          description: "The thing was successfully updated."               #
          content:                                                         #
            application/json:                                              #
              schema:                                                      # [7]
                type: "object"                                             #
                properties:                                                #
                  status:                                                  #
                    type: "string"                                         #
                    const: "ok"                                            #
```

### [1] The OpenAPI version

The OpenAPI version must be `"3.1.0"` for compatibility
with the current Globus Flows implementation of Registered APIs.

If the version is not `"3.1.0"` (or if there is no `openapi:` key)
try setting the value to `"3.1.0"`.

### [2] Server base URLs

This is the base URL of the server.

If this field is missing, or has an incorrect value,
try adding the field and setting it to the correct value.

### [3] Paths and path parameters

This is the path of the API route that updates things.
`{thing_id}`, wrapped in braces, is a parameter.

If a different parameter format appears, like `<thing_id>` or `$THING_ID`,
this needs to be transformed to use braces.

### [4] Parameter definitions

In the example, a single path parameter, `thing_id`, is required,
and it must be defined in this section.

Make sure that all required parameters are defined correctly.

### [5] Globus scopes

Two Globus scopes are listed for this made-up example: `manage`, and `all`.

The order of these scopes matters to the Globus Flows service implementation;
it's recommended that the scope with the least privilege is listed first.

The Globus Registered API CLI will prompt for scopes if none are defined.

However, if the scope information is malformed or incorrect.

### [6] Request schemas

Schemas are defined using
[JSON Schema](https://json-schema.org/docs)
syntax.
This schema states that a request body is required,
it must be a JSON object,
and it must have a `"name"` field with a string value.
For example:

```json
{"name": "A new name for the thing"}
```

Including a schema is valuable for validating flows and runs
in the Globus Flows service.

### [7] Responses

This describes the response from the API when a thing is successfully updated.
In this case, `"200"` refers to the HTTP status code,
and it describes what the JSON response will look like:

```json
{"status": "ok"}
```

If the response schema doesn't match the service's API responses,
this can lead to flow validation errors.
