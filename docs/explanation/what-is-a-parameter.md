[🏠 Documentation home](../README.md)
» [Explanations](README.md)
» Explanation: What is a parameter?

# Explanation: What is a parameter?


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [What is a parameter?](#what-is-a-parameter)
- [What types of parameters exist?](#what-types-of-parameters-exist)

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

## What types of parameters exist?

In the previous section, an example was given of a "path parameter",
but there are several types of parameters:

* **Path parameters**

  Path parameters are part of, and visible in, the URL's path.
  They are always required.

  In the example below, `thing_id` is the name of the path parameter:

  ```text
  https://domain.example/things/{thing_id}
                                ^^^^^^^^^^
  ```

* **Query parameters**

  Query parameters are part of, and visible in, the URL's query string.

  In the example below, `page` and `page_size` are the names of the query parameters:

  ```text
  https://domain.example/things/?page=2&page_size=25
                                 ^^^^   ^^^^^^^^^
  ```

* **Header parameters**

  Header parameters are added as headers to the HTTP request
  when an API is called.
  They are not visible in the URL.

* **Cookie parameters**

  Cookie parameters are added to the `Cookie` header in the HTTP request
  when an API is called.
  They are not visible in the URL.

For more information about parameter types, see
[this page](https://swagger.io/docs/specification/v3_0/describing-parameters/#parameter-types).
