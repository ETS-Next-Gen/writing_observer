# Serve Learning Observer as an LTI 1.3 tool

Learning Observer ships with an IMS LTI 1.3 implementation that relies on the platform's OpenID Connect (OIDC) handshake to authenticate users and obtain scoped API access tokens from the learning management system (LMS). Use this guide to register the tool in an LMS and connect it to a course shell.

## Prerequisites

* A deployment of Learning Observer reachable by the LMS (typically via HTTPS).
* An LMS that supports LTI 1.3 with dynamic registration or manual developer keys (e.g., Canvas or Schoology).
* Administrative access in that LMS to create a developer key / external tool.

## 1. Generate and share a signing key

Learning Observer signs client assertions with an RSA private key when it exchanges OIDC launch data for an LMS access token. Generate a keypair, store the private key somewhere on the application host, and upload the public key to the LMS when you create the developer key.

```bash
# create a 4096-bit RSA keypair
openssl genrsa -out secrets/lti-tool-private.pem 4096
openssl rsa -in secrets/lti-tool-private.pem -pubout > secrets/lti-tool-public.pem
```

Record the filesystem path to the private key; you'll reference it in the application configuration in the next step.

## 2. Configure `creds.yaml`

Enable the LTI provider in `learning_observer/creds.yaml` by adding an entry under `auth.lti.<provider>`. Each provider requires the LMS endpoints, the Learning Observer redirect URL, and the private key location. A Canvas example looks like this:

```yaml
auth:
  lti:
    sample-canvas:
      client_id: "10000000000000"
      auth_uri: "https://canvas.example.edu/api/lti/authorize_redirect"
      jwks_uri: "https://canvas.example.edu/api/lti/security/jwks"
      token_uri: "https://canvas.example.edu/login/oauth2/token"
      redirect_uri: "https://lo.example.edu/lti/sample-canvas/launch"
      private_key_path: "secrets/lti-tool-private.pem"
      api_domain: "https://canvas.example.edu"  # Canvas-specific
```

Set `redirect_uri` to the public URL that will receive the POST launch request (`/lti/<provider>/launch`). The login initiation URL for the LMS is the matching `/lti/<provider>/login` route.

Restart the application after updating configuration so the new provider registration is loaded.

## 3. Enable LMS API routes

Learning Observer only exposes the IMS Names & Roles (NRPS) and Assignment & Grade Service (AGS) proxy routes when the matching feature flag is turned on. Add the appropriate flag to `creds.yaml` so the application registers the routes during startup:

```yaml
feature_flags:
  canvas_routes: true          # Canvas NRPS/AGS proxy endpoints
  # schoology_routes: true     # Schoology NRPS/AGS proxy endpoints
```

## 4. Map the roster source with PMSS

LTI launches identify the LMS provider in the session so roster lookups can decide which backend to call. Create a PMSS overlay that maps the provider to the correct roster source (see [System settings](../concepts/system_settings.md) for more on PMSS). For Canvas, create a file such as `config/roster_source.pmss` alongside `creds.yaml` with the following contents:

```pmss
roster_data[provider="sample-canvas"] {
    source: sample-canvas;
}
```

If you support multiple LMS tenants, add additional selector blocks for their email domains or provider names and point them at `schoology`, `filesystem`, or any other supported roster backend.

## 5. Register the tool in the LMS

When you create the LTI developer key/external tool inside the LMS:

1. Supply the **OIDC login initiation URL** as `https://<your-domain>/lti/<provider>/login`.
2. Supply the **redirect/launch URL** as `https://<your-domain>/lti/<provider>/launch`.
3. Paste the **public key** generated earlier so the LMS can validate the signed client assertions.
4. Copy the LMS-issued **client ID** and the platform endpoints (authorize, JWKS, token) into `creds.yaml` if you have not done so already.

Publish the developer key and install the tool in the desired course/context. The LMS will send the context identifiers in the launch claims so Learning Observer can associate sessions with the right course.

## 6. Verify the launch

* Add the external tool link to a module or assignment inside the LMS course.
* Launch the tool from within the LMS. Learning Observer should redirect the browser to the LMS's authorize endpoint, validate the launch state and nonce, and then create a session for the user when the LMS returns.
* Successful launches land on the root of the application with LMS-specific authorization headers stored in the session for follow-up roster and grade sync operations.

If the launch fails, inspect the Learning Observer logs for messages beginning with `LTI Launch`—they include detailed context whenever state validation, token exchange, or JWT verification fails. Once the LMS recognizes the tool, you can remove or hide other authentication methods; Learning Observer will automatically expose the LTI login routes whenever `auth.lti` providers are configured.

## 7. Plan student identity mapping

LTI launch data only includes the learner's email address, while Writing Observer's Google Workspace integrations emit a Google-specific user identifier. To keep downstream reducers and dashboards working for LTI cohorts, plan to run the maintenance workflow that maps emails to Google IDs. Refer to the [Student Identity Mapping guide](../concepts/student_identity_mapping.md) for an overview of how the reducer and maintenance script cooperate and how to operate the sync in production.
