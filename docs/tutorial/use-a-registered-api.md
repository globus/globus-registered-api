# Use a Registered API in a flow

[🏠 Documentation home](../README.md)
» [Tutorials](README.md)
» Use a Registered API in a flow


Now that you've [created your first Registered API](create-a-registered-api.md),
you're ready to use it in a flow!


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [Prerequisites](#prerequisites)
- [Create a flow definition file](#create-a-flow-definition-file)
- [Create the flow](#create-the-flow)
- [Run the flow](#run-the-flow)
- [Recap](#recap)
- [Next steps](#next-steps)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Prerequisites

You'll need these three things before continuing with this tutorial

* The [Globus CLI](https://docs.globus.org/cli/) must be installed.
* You need to log into the Globus CLI with the same Globus Auth identity
  that you used in the previous section of the tutorial.
* You'll need the Registered API ID that you copied
  at the end of the last section of the tutorial.


## Create a flow definition file

Create a file named `definition.json`
and copy in the JSON document shown below:

```json
{
  "StartAt": "DemoRegisteredApi",
  "States": {
    "DemoRegisteredApi": {
      "Type": "Action",
      "Handler": {
        "Type": "RegisteredAPI",
        "Id": "REPLACE_ME_WITH_YOUR_REGISTERED_API_ID!"
      },
      "Parameters": {},
      "ResultPath": "$.MyFlows",
      "End": true
    }
  }
}
```

> [!NOTE]
>
> Be sure to replace the text `REPLACE_ME_WITH_YOUR_REGISTERED_API_ID!`
> with the Registered API ID that you copied
> in the previous section of the tutorial.


## Create the flow

In the same directory that you created the `definition.json` file above,
run this Globus CLI command:

```shell
globus flows create "Demo: List my flows" definition.json
```

You'll see output similar to this:

```shell
$ globus flows create "Demo: List my flows" definition.json
Flow ID:                  00000000-0000-0000-0000-000000000000
Title:                    Demo: List my flows
Subtitle:
Description:
Keywords:
Owner:                    user@example.domain
High Assurance:           False
Authentication Policy ID: None
Subscription ID:          None
Created At:               2026-03-01 00:00:00
Updated At:               2026-03-01 00:00:00
Administrators:
Viewers:
Starters:
Run Managers:
Run Monitors:
```

Copy the flow ID for the next step.
(You can always run `globus flows list` if you lose track of it!)


## Run the flow

You'll need to run the next Globus CLI command twice,
replacing the all-zeroes ID with the real flow ID
that you copied from the previous step.

```shell
globus flows start 00000000-0000-0000-0000-000000000000
```

The first time it's run, you'll be directed to run a `globus login` command.
This is required whenever you start a flow for the first time with the Globus CLI.

Copy and run the `globus login` command as directed,
which will launch your web browser
and direct you through a Globus Auth login flow.

Once you've consented to the Globus CLI interacting with your new flow,
return to the console and re-run the `globus flows start` command.
You'll see output similar to this:

```console
$ globus flows start 00000000-0000-0000-0000-000000000000
Run ID:       ffffffff-ffff-ffff-ffff-ffffffffffff
Run Label:    None
Run Tags:
Status:       ACTIVE
Started At:   2026-03-01 11:11:11
Completed At: None
Flow ID:      00000000-0000-0000-0000-000000000000
Flow Title:   Demo: List my flows
Run Owner:    user@example.domain
Run Managers: user@example.domain
Run Monitors:
```

You can then review the run's logs.
Copy and paste the run ID from your `globus flows start` output
and insert it into this command:

```console
$ globus flows run show-logs --format=json ffffffff-ffff-ffff-ffff-ffffffffffff
{
  ...
}
```


## Recap

You've reached the end of the tutorial!

Let's look back at what you've accomplished:

* You initialized a Registered API repository using the `gra init` command.
* You configured a single target and reviewed the roles associated with it
  using the `gra manage` command.
* You built and published the repository
  using the `gra build` and `gra publish` commands,
  which created a single new Registered API.
* You created a flow that used that Registered API and ran it.

Great work!


## Next steps

If you'd like to explore Registered APIs more, here are some ideas:

* Use the `gra manage` command to configure some additional targets.
* Create a new directory and initialize a new Registered API repository
  using the `gra init` command...
  but choose a different Globus service's OpenAPI specification URL!

* [🏠 Documentation home](../README.md)
