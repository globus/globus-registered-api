[🏠 Documentation home](../README.md)
» [Reference](README.md)
» OpenAPI requirements

# OpenAPI requirements


## Table of contents

* [Version](#version)
* [Security](#security)


## Version

The Globus Flows service -- and therefore this Globus Registered API CLI --
currently requires OpenAPI version `3.1`.

OpenAPI documents should declare this version:

```yaml
openapi: 3.1.0
```


## Security

If Globus scopes are required, they must be declared in the `security` key.
(Not all APIs require authorization or consent; see the note below.)

Many Globus services allow multiple scopes for the same operation;
for example, if you've consented to management access,
it follows that you've consented to read access...
and if you've consented to all access,
then that includes management and read access.

Given the "any of these three scopes will work" relationship suggested above,
the example below shows how that would be represented in an OpenAPI spec:

```yaml
paths:
  /things:
    get:
      security:
        - GlobusAuth:
            - "https://auth.globus.org/scopes/00000000-0000-0000-0000-000000000000/read_things"
        - GlobusAuth:
            - "https://auth.globus.org/scopes/00000000-0000-0000-0000-000000000000/manage_things"
        - GlobusAuth:
            - "https://auth.globus.org/scopes/00000000-0000-0000-0000-000000000000/all"
```

Within the Globus Flows service, the order of the scopes matters.
The Globus Flows service will check the scopes that the user has consented to
when they attempt to start a flow that uses Registered APIs;
if the user has not consented to at least one of the required scopes,
the first scope listed is the one that will be requested.
(In the OpenAPI `security` example above, the first scope is the `read_things` scope.)
This is why it's suggested that the first scope have the least privileges
associated with it.

> [!NOTE]
>
> If an API target doesn't require authorization,
> then the `security:` field is not required, and should not be included.
