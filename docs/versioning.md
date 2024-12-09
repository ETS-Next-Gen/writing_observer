# Versioning

## Tracking versions

Each module should include a `VERSION` file the module's current version. The module should refer to this file in its setup configuration. Typically, this is done in the `setup.cfg` file like so:

```cfg
# setup.cfg
[metadata]
name = Module name
version = file:VERSION
```

## Bumping versions

Versions are automatically handled by `git hooks`. Each time a commit is about to be made, we update the appropriate VERSION files with `%Y-%m-%d-%H:%M:%S.%3N-shortCommitHash-branchName`.
