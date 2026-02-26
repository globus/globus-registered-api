[🏠 Documentation home](../README.md)
» [Reference](README.md)
» Shell completion

# Shell completion


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Table of contents

- [Linux/macOS](#linuxmacos)
  - [bash](#bash)
  - [zsh](#zsh)
  - [fish](#fish)
- [Windows](#windows)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Linux/macOS

The Globus Registered API CLI uses a Python framework,
[click](https://click.palletsprojects.com/en/stable/shell-completion/),
that supports shell completion.
By enabling shell completion, you can press `TAB` to see subcommands and options
while typing a `gra` command.
For example:

```console
$ gra <TAB> <TAB>
api      build    init     manage   publish  session

$ gra publish --<TAB> <TAB>
--target-alias  --yes           --help
```

At the time of writing, three shells are supported out-of-the-box:
bash, zsh, and fish.


### bash

Assuming that the Globus Registered API CLI is on the `$PATH`,
add this to `~/.bashrc`:

```shell
eval "$(_GRA_COMPLETE=bash_source gra)"
```


### zsh

Assuming that the Globus Registered API CLI is on the `$PATH`,
add this to `~/.zshrc`:

```shell
eval "$(_GRA_COMPLETE=zsh_source gra)"
```


### fish

Assuming that the Globus Registered API CLI is on the `$PATH`,
add this to `~/.config/fish/completions/gra.fish`:

```shell
_GRA_COMPLETE=fish_source gra | source
```


## Windows

At the time of writing, the CLI framework used by the Globus Registered API CLI
does not support command completion for PowerShell.
