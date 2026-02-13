
Added
-----

*   Added stubs for planned commands:

    * ``gra init``
    * ``gra manage``
    * ``gra publish``
    * ``gra api delete``

Removed
-------

*   Deleted ``gra willdelete`` commands.

Changed
-------

*   Reorganized the command hierarchy:

    *   Top-level non-grouped commands (``gra init``, ``gra manage``, ``gra publish``)
        operate at the upcoming "repository" abstraction.

    *   Api interfaces are now under ``gra api`` group:

        * ``gra api show`` (formerly ``gra get``)
        * ``gra api list``
        * ``gra api create``
        * ``gra api update``
        *  ``gra api delete`` (stubbed)

    *   Globus Auth session management commands are now under ``gra session``:

        * ``gra session logout``
        * ``gra session whoami``
