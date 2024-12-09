# Versioning

## Tracking Versions

Each module should include a `VERSION` file to specify the module's current version. This version is referenced in the module's setup configuration. Typically, this is done in the `setup.cfg` file as follows:

```cfg
# setup.cfg
[metadata]
name = Module name
version = file:VERSION
```

## Bumping Versions

Versioning is automatically managed using a Git pre-commit hook. Before each commit is made, the appropriate `VERSION` files are updated with a timestamped format that includes the following details:

```sh
%Y-%m-%d-%H:%M:%S.%3N-shortCommitHash-branchName
```

A example version string might look like this:

```sh
2024-12-09-15:45:32.123-abc123-main
```

## Setting Up the Pre-Commit Hook

To enable automatic version bumping, use the `install-pre-commit-hook` command provided in the `Makefile`. This command handles copying the pre-commit hook script into the appropriate location and making it executable. Run the following command:

```bash
make install-pre-commit-hook
```

With this setup, every commit will automatically update the version for you.

## Notes

- Ensure that `setup.cfg` properly references the `VERSION` file to avoid version mismatches.
- Avoid manually editing the `VERSION` file; rely on the pre-commit hook for consistency.
