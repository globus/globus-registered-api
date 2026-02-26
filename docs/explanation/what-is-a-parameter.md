# Explanation: What is a parameter?

[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a parameter?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## What is a parameter?

APIs sometimes require variable information to work correctly.
Each individual piece of variable information is called a "parameter".

Here's an example of a type of parameter called a "path parameter"
that you are likely to see when configuring
[targets](what-is-a-target.md)
in the GRA CLI:

```text
/things/{thing_id} (DELETE)
```

The text `{thing_id}` flags that when an attempt is made to `DELETE` a thing,
the thing's ID must be provided.
