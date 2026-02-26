# Explanation: What is a role?

[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a role?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is a role?

Roles are the collective term for the permissions assigned to a
[Registered API](what-is-a-registered-api.md).

There are three types of roles:

* Owners
* Administrators
* Viewers

Their capabilities are shown in the table below.

| Registered API Interaction       | Anyone | Viewer | Administrator | Owner                      |
|----------------------------------|--------|--------|---------------|----------------------------|
| Use the Registered API in a flow | ✅      | ✅      | ✅             | ✅                          |
| Show the Registered API          |        | ✅      | ✅             | ✅                          |
| List the Registered API          |        | ✅      | ✅             | ✅                          |
| Update a Registered API          |        |        | ✅             | ✅                          |
| Update the Viewers role          |        |        | ✅             | ✅                          |
| Update the Administrator role    |        |        |               | ✅                          |
| Update the Owner role            |        |        |               | ✅ (See [note](#ownership)) |
| Delete a Registered API          |        |        |               | ✅                          |

> [!NOTE]
>
> <a name="ownership"></a>
> Although owners can update the Owner role,
> owners are protected from removing their own access to the Registered API.
>
> Owners are allowed to remove their individual account access
> if they assign ownership to a group that they are part of.
>
> Beware that if an owner assigns access to a group and then leaves that group,
> they can still lose access to their own
