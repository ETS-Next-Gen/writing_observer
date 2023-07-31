# Config (creds.yaml)

The Learning Observer project can be configured on a per-system basis using a configuration file. This configuration file is essential for setting various options such as the environment mode (development or production), authentication, and module-specific settings.

## Settings

The settings are loaded in via the `learning_observer/learning_observer/settings.py` file. You see them referred to in the code with

```python
import learning_observer.settings
item = learning_observer.settings.settings['kvs']
```

### Hostname and Protocol

The `hostname` and `protocol` sections define the address and protocol used for accessing the Learning Observer application.

- `hostname`: The address of the application server.
- `protocol`: The protocol used for communication (http or https).

Example:

```yaml
hostname: localhost:8888
protocol: http
```

### XMPP

The `xmpp` section defines the credentials and configurations for XMPP connections, including sinks, sources, and stream components.

- `sink`: Configuration for XMPP sinks that receive messages.
  - `jid`: The Jabber ID for the sink.
  - `password`: The password for the sink.
- `source`: Configuration for XMPP sources that send messages.
  - `jid`: The Jabber ID for the source.
  - `password`: The password for the source.
- `stream`: Configuration for XMPP streams used for debugging.
  - `jid`: The Jabber ID for the stream.
  - `password`: The password for the stream.

Example:

```yaml
xmpp:
  sink:
    jid: sink@localhost
    password: {xmpp-sink-password}
  source:
    jid: source@localhost
    password: {xmpp-source-password}
  stream:
    jid: stream@localhost
    password: {xmpp-stream-password}
```

### Authentication

The `auth` section is responsible for configuring various authentication methods.

- `google_oauth`: Configuration for Google OAuth authentication.
  - `web`: A sub-configuration containing Google OAuth settings.
    - `client_id`: The Google OAuth client ID.
    - `project_id`: The Google OAuth project ID.
    - `auth_uri`: The Google OAuth authorization URI.
    - `token_uri`: The Google OAuth token URI.
    - `auth_provider_x509_cert_url`: The Google OAuth provider x509 certificate URL.
    - `client_secret`: The Google OAuth client secret.
    - `javascript_origins`: The list of allowed JavaScript origins.
- `password_file`: The path to the password file used for authentication, created using the `lo_passwd.py` script.
- `http_basic_auth`: Configuration for HTTP basic authentication.
  - `mode`: The mode of HTTP basic authentication, either 'nginx' or 'password-file'.
  - `password_file`: The path to the password file used for authentication, or 'null' if authentication is done by nginx.

Example:

```yaml
auth:
  google_oauth:
    web:
      client_id: {google-oauth-client-id}
      project_id: {google-oauth-project-id}
      auth_uri: https://accounts.google.com/o/oauth2/auth
      token_uri: https://oauth2.googleapis.com/token
      auth_provider_x509_cert_url: https://www.googleapis.com/oauth2/v1/certs
      client_secret: {google-client-secret}
      javascript_origins: ["{url}"]
  password_file: passwd.lo
  http_basic_auth:
    mode: remove-this
    password_file: passwd.lo
```

### PubSub

The `pubsub` section configures the pubsub system type used for the application.

- `type`: The type of pubsub system, either 'stub' for in-memory debugging or 'redis' for small-scale production.

Example:

```yaml
pubsub:
  type: stub
```

I apologize for that. Here are the remaining sections:

### KVS

The `kvs` section configures the key-value store used in the application.

- `default`: The default configuration for the key-value store.
  - `type`: The type of key-value store, such as 'stub', 'redis', or 'redis_ephemeral'.
  - `expiry`: The expiry time for objects in the key-value store (in seconds).

Example:

```yaml
kvs:
  default:
    type: stub
    expiry: 6000
```

### Roster Data

The `roster_data` section configures the source of roster data.

- `source`: The source of roster data, such as 'filesystem', 'google_api', 'all', or 'test'.

Example:

```yaml
roster_data:
  source: filesystem
```

### AIO

The `aio` section configures user session settings.

- `session_secret`: The unique secret key for your deployment.
- `session_max_age`: The maximum age of a session, in seconds.

Example:

```yaml
aio:
  session_secret: {unique-aio-session-key}
  session_max_age: 3600
```

### Config

The `config` section configures the run mode and debug settings.

- `run_mode`: The run mode, either 'dev' or 'deploy'.
- `debug`: A list of debug options, such as "tracemalloc".

Example:

```yaml
config:
  run_mode: dev
  debug: []
```

### Logging

The `logging` section configures the logging settings.

- `debug_log_level`: The log level, either 'NONE', 'SIMPLE', or 'EXTENDED'.
- `debug_log_destinations`: A list of log destinations, such as 'CONSOLE' and 'FILE'.

Example:

```yaml
logging:
  debug_log_level: SIMPLE
  debug_log_destinations:
    - CONSOLE
    - FILE
```

### Theme

The `theme` section configures the appearance and messages of the application.

- `server_name`: The name of the server.
- `front_page_pitch`: The message displayed on the front page.
- `logo_big`: The URL of the logo.

Example:

```yaml
theme:
  server_name: Learning Observer
  front_page_pitch: Learning Observer is an experimental dashboard. If you'd like to be part of the experiment, please contact us. If you're already part of the experiment, log in!
  logo_big: /static/media/logo-clean.jpg
```

### Event Auth

The `event_auth` section configures authentication settings for events.

- `local_storage`: Configuration for local storage authentication.
  - `userfile`: The file containing user information.
  - `allow_guest`: A boolean indicating whether guest access is allowed.
- `chromebook`: (optional) Configuration for Chromebook authentication.
  - `allow_guest`: A boolean indicating whether guest access is allowed on Chromebooks.

Example:

```yaml
event_auth:
  local_storage:
    userfile: students.yaml
    allow_guest: true
```

### Feature Flags

The `feature_flags` section allows you to enable or disable specific features in development.
 A dictionary with the feature names as keys and boolean values to indicate whether the feature is enabled or disabled.

Example:

```yaml
feature_flags: {}
```

### Server

The `server` section configures the server settings.

- `port`: The port number on which the server will listen.

Example:

```yaml
server:
  port: 8888
```

### Modules

The `modules` section configures the settings for each module installed on the system. Different systems may define different items depending on which modules they wish to have installed on their system. An error will be raised if an expected setting is missing from a given module. Here is an example for the `writing_observer` module.

- `writing_observer`: Settings specific to the Writing Observer module.
  - `use_nlp`: A boolean indicating whether to use natural language processing or a stub function. (default: `false`)
  - `use_google_documents`: A boolean indicating whether to use Google Documents. (default: `false`)
  - `languagetool_port`: The port the LanguageTool server is running on (default: `8081`)
  - `languagetool_host`: The host the LanguageTool server is running on (default: `localhost`)
  - `use_languagetool`: A boolean indicating whether to use LanguageTool or a stub function. (default: `false`)

Example:

```yaml
modules:
  writing_observer:
    use_nlp: true
    use_google_documents: false
    languagetool_port: 8081
    use_languagetool: true
```

Note: This is just an example of how to configure the settings for a specific module. Each module may have its own unique settings, and you should consult the module's documentation for information on which settings are required and how they should be configured.
