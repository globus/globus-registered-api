
Added
-----

*   Add Access Role Control to ``gra api create``.

    Usage Example:

    .. code-block:: console

        gra api create "My API" ./target-json-structure.json --description "My API" \
            --owner "urn:globus:auth:identity:0b8067fc-0bb4-46e4-b23d-3ad543624519" \
            --admin "urn:globus:auth:identity:d86ff962-1b2a-4de8-8bde-7dc993494dcb" \
            --admin "urn:globus:groups:id:b0d11f00-5701-480f-a523-5b03869dfdbc" \
            --viewer "urn:globus:groups:id:ed3219c3-c4ef-4b04-932a-d00bf88ceea7"

Changed
-------

*   Change the ``gra api create`` command to accept a target file, instead of
    constructing one from a supplied openapi specification.

    New Usage Example:

    .. code-block:: console

        gra api create "My API" ./target-json-structure.json --description "My Cool API"

*   Change the ``gra api update`` command to accept a target file with the option
    ``--target`` instead of ``target-file``.

Development
-----------

*   Centralize registered api printing logic into a command-shared function.
