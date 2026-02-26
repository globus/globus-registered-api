[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a role?

# Explanation: What is a role?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is a role?

Roles are the collective term for the access controls assigned to a
[Registered API](what-is-a-registered-api.md).

A role is capable of performing certain operations on a Registered API.
When a Globus Auth identity or a Globus Groups group is assigned to a role,
that identity or group is then allowed to perform the operations
associated with that role.

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
> Beware that if an Owner assigns ownership to a group and then leaves that group,
> they can lose access to the Registered API.
