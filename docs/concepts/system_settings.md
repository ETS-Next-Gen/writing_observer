# System settings

Learning Observer depends on a single source of truth for everything from
server ports to which pieces of modules are enabled.  We rely on the
[PMSS](https://github.com/ETS-Next-Gen/pmss) registry because it gives us a
predictable, type-checked way to describe those concerns once and reuse them
across the whole stack.  This article explains why the settings layer exists,
how `creds.yaml` fits into the picture, and why we support cascading
``*.pmss`` files that behave a bit like CSS for configuration.

To view all settings and what they do, checkout the [System Settings Reference](../reference/system_settings.md).

## Why centralize configuration?

* **Shared vocabulary.** Modules, reducers, and integrations all speak the same
  language when they ask for `hostname`, `redis_connection.port`, or
  `modules.writing_observer.use_nlp`.  PMSS enforces the field definitions so we
  can freely move code between services without wondering what the knobs are
  called.
* **Type safety and validation.** Every field is registered with a type and
  optional parser.  PMSS refuses to start if a value is missing or malformed,
  surfacing errors during boot instead of in the middle of a request.
* **Operational portability.** Teams deploy Learning Observer to wildly
  different environments.  A single registry allows a site to describe network
  boundaries, third-party credentials, or feature flags in one place and keep
  those choices under version control.

## The role of `creds.yaml`

Most installations load configuration from `creds.yaml`.  When the process
starts, `learning_observer.settings` initializes PMSS with a
`YAMLFileRuleset`, parses that file, and registers the run mode and other core
fields.  The YAML mirrors the namespace hierarchy, so options live exactly where
operators expect to see them:

```yaml
server:
  port: 5000
modules:
  writing_observer:
    use_nlp: true
```

`creds.yaml` gives us a stable default: it travels with the deployment, can be
checked into private infrastructure repositories, and is easy to audit during
reviews.  Even when we introduce additional sources, the YAML baseline remains
the anchor that documents the "intent" of the environment.

## Cascading ``*.pmss`` overlays

While one file covers global defaults, we often need tweaks that depend on
**who** is asking for data or **where** a request originates.  PMSS supports
multiple rule sets, so we extend the base YAML with optional ``*.pmss``
overlays.  Each overlay is a small PMSS file whose contents look just like the
YAML fragment they augment, but they add selectors that encode *specificity*.

Think of these selectors like CSS.  We start with the low-specificity default
rule and then layer on increasingly precise matches:

```pmss
roster_data {
    source: all;
}

roster_data[domain="learning-observer.org"] {
    source: google;
}
```

When `learning_observer/learning_observer/rosters.py` asks for `roster_data`
it supplies attributes such as the caller's email domain or provider.  PMSS
walks the rule set, finds the most specific block that matches the request, and
returns that value.  In the example above a teacher from
`learning-observer.org` would receive the `google` roster source, while any
other user would keep the global `all` default.  Additional selectors can layer
on top for providers, schools, or classrooms with each more specific rule
overriding the broader ones.

At runtime we still assemble a deterministic cascade:

1. Load the global `creds.yaml` defaults.
2. Apply any environment overlays (for example, a `district.pmss` file that
   swaps OAuth credentials for that customer).
3. Resolve request-scoped overlays that match the supplied selectors, letting
   the most specific rule win.

PMSS tracks the provenance of each value so developers can inspect which file
supplied the final answer when troubleshooting.  Because overlays reuse the
same registered fields, we retain all of the type checking that protects the
base configuration.

## How code consumes the cascade

Once the cascade is assembled, code does not care whether a value came from the
YAML baseline or an overlay.  Components call
`learning_observer.settings.pmss_settings.<field>()` (optionally via
`module_setting()` helpers) and PMSS resolves the field using the active rule
stack.  That means a request handled for an instructor can pick up
instructor-specific defaults while a system job, using the same accessor, still
observes the site-wide configuration.

## Extending the system settings surface

Adding a new capability follows a consistent pattern:

1. Register the field with PMSS, giving it a name, type, description, and
   default if appropriate.
2. Update `creds.yaml` (or the reference documentation) to teach operators what
   the new setting does.
3. Optionally create overlay files where the value should vary by tenant, user,
   or integration partner.

By keeping configuration declarative and cascading, we get the flexibility to
serve many partners without branching the codebase, all while preserving the
predictability administrators expect from a single system settings registry.
