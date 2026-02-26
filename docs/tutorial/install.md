# Install and log in

[🏠 Documentation home](../README.md)
» [Tutorials](README.md)
» Install and log in


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [Requirements](#requirements)
- [Install](#install)
  - [Install using `pip`](#install-using-pip)
  - [Install using `pipx`](#install-using-pipx)
  - [Install using `uv pip`](#install-using-uv-pip)
  - [Run using `uv run`](#run-using-uv-run)
- [Log in](#log-in)
- [Next steps](#next-steps)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Requirements

The Globus Registered API, or "GRA", is console application written in Python.

Regardless of which installation tool you choose to use,
your system must have Python 3.10 or higher already installed.

You can check whether Python is already installed by running:

```shell
python --version
```

If you see a Python version printed, like `Python 3.14.3`
and the displayed version is "3.10.0" or higher,
then congratulations! Python is already installed.

However, if Python is not installed, you will need to
[download Python](https://www.python.org/downloads/)
and install it.


## Install

There are a handful of tools that are commonly used to install Python software.
It is outside the scope of this tutorial to describe each tool in detail,
but basic installation instructions are provided below for each tool.

### Install using `pip`

`pip` is included with Python and is a common way to install Python software.

You can install `globus-registered-api` to your user install directory
using this command:

```shell
python -m pip install --upgrade --user globus-registered-api
```

The `--upgrade` ensures that GRA will be upgraded if it is already installed.


### Install using `pipx`

[`pipx`](https://pipx.pypa.io/stable/) is not included with Python
but is a common tool for installing and managing Python applications.

You can check if `pipx` is installed by running this command:

```shell
pipx --version
```

If you see a version number printed, like `1.8.0`,
then `pipx` is installed and available.
You can then install GRA with this command:

```shell
pipx install globus-registered-api
```

If you need to upgrade GRA, you can run this command:

```shell
pipx upgrade globus-registered-api
```

### Install using `uv pip`

[`uv`](https://docs.astral.sh/uv/) is not included with Python
but is a common tool in the Python development.

You can check if `uv` is installed by running this command:

```shell
uv --version
```

If you see a version printed, like `uv 0.10.7`, then `uv` is installed.

You can install GRA with a command like this:

```shell
uv pip install --upgrade --user globus-registered-api
```

The `--upgrade` ensures that GRA will be upgraded if it is already installed.


### Run using `uv run`

As noted in the previous section, `uv` is not included with Python.
You will need to confirm whether `uv` is already installed on your system.

Then, you can directly run GRA using a command like this:

```shell
uv run --with='globus-registered-api' gra --help
```

You should see output that includes text like this:

```text
Globus Registered API Command Line Interface.
```

> [!NOTE]
>
> The installation methods above will make GRA available
> with the command name `gra`, which can then be run by name.
> In contrast, the ENTIRE `uv run --with='globus-registered-api' gra`
> must be typed each time you want to run the GRA application.
>
> This documentation will document invoking GRA with the command `gra`,
> so be sure to use the entire `uv run ...` line
> if you choose to run GRA without installing it.


## Log in

Once GRA is installed, you will need to log in. Use this command:

```shell
gra session whoami
```

A login URL will be printed to the console.
You may be able to click on the URL to open the URL in your browser.
If clicking on the URL doesn't open the browser,
you might need to hold the "CTRL" key on your keyboard while clicking.

You might also need to simply copy and paste the entire URL into the browser.

After logging in and consenting to GRA managing Registered APIs on your behalf,
you will be presented with an authorization code.
Copy and paste that code into the GRA prompt:

```shell
Enter the resulting Authorization Code here:
```

When you press enter, you should see your account identifier print on-screen.


## Next steps

* Continue the tutorial: [Create your first Registered API](create-a-registered-api.md)
* [🏠 Documentation home](../README.md)
