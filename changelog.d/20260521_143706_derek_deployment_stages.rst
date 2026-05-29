
Breaking changes
----------------

*   Bump config & manifest files to v1.0 as the initial release version.

Added
-----

*   Add support for "stages", a new concept to represent different phases
    of the same deployed service.

    Examples: [alpha, beta, prod], [sandbox, staging, production], etc.

Changed
-------

*   Update existing commands to support stages, notably requiring a ``--stage``
    flag in ``gra publish`` if multiple stages have been defined.
