# Releasing new versions

Follow this process to release new versions of the GRA CLI.

> [!NOTE]
>
> This process depends on the following tools:
>
> * bash
> * git
> * GitHub CLI
> * just
> * pandoc
> * Poetry
> * twine


## STEP 1: Prep the release branch

Choose a new version number and run this command,
substituting the version number for the word "VERSION".

```shell
just r1-prep-release "VERSION"
```


## STEP 2: Review the CHANGELOG

Review the CHANGELOG for readability, flow, and consistency.
If changes are made, use this command to commit the changes:

```shell
just r2-amend-changelog
```


## STEP 3: Create the release PR

```shell
just r3-create-pr
```

Wait for the release PR to merge.


## STEP 4: Publish

After the release PR merges, run this command:

```shell
just r4-publish
```


## STEP 5: Merge back to main

```shell
just r5-merge-back
```
