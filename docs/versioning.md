# Versioning

The system follows [Semantic Versioning](https://semver.org/).

## Tracking versions

Each module should include a `VERSION` file the module's current version. The module should refer to this file in its setup configuration. Typically, this is done in the `setup.cfg` file like so:

```cfg
# setup.cfg
[metadata]
name = Module name
version = file:VERSION
```

## Bumping versions

We suggest using `bump-my-version`. Each module should include a `.bumpversion.toml` configuration file that tells `bump-my-version` how to update the version numbering.

To bump, use the following command

```bash
bump-my-version bump <major|minor|patch>
```

`bump-my-version` offers a `--dry-run` flag that will output the version changes to the console, but not make any changes. This is useful for debugging.

If a `.bumpversion.toml` does not exist, create one. Below are a set of baseline settings (recommended by `bump-my-version`) along with the necessary changes to write to the `VERSION` file. Note that a new commit will be made for each bump using this configuration via the `commit=true` setting.

```toml
# bump-my-version configuration
[tool.bumpversion]
current_version = "0.1.0"
parse = "(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)"
serialize = ["{major}.{minor}.{patch}"]
search = "{current_version}"
replace = "{new_version}"
regex = false
ignore_missing_version = false
ignore_missing_files = false
tag = false
sign_tags = false
tag_name = "v{new_version}"
tag_message = "Bump PACKAGE NAME version: {current_version} → {new_version}"
allow_dirty = false
commit = true
message = "Bump PACKAGE NAME version: {current_version} → {new_version}"
commit_args = ""
setup_hooks = []
pre_commit_hooks = []
post_commit_hooks = []

[[tool.bumpversion.files]]
filename = "VERSION"
```
