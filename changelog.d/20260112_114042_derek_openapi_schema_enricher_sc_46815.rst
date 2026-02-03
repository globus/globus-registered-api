
Development
-----------

*   Added an OpenAPI Mutator framework to enrich schemas.

*   Added a basic service-config format.


Added
-----

*   Added a new command, ``willdelete print-service-target``, which prints a target from
    a registered service's config whose schema has been "enriched".

*   Added service config registration for globus-search and globus-groups.


Changed
-------

*   Changed ``willdelete print`` to ``willdelete print-target``

    *   Updated the ordering of the `ROUTE` and `METHOD` arguments.
    *   New order: `willdelete print-target <METHOD> <ROUTE>`
