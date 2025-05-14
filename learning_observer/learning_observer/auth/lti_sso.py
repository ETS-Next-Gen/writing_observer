'''
Generic LTI 1.3 Single Sign-On handler for multiple providers.

Implements LTI 1.3's OpenID Connect (OIDC) authentication handshake.
OIDC establishes a secure SSO channel between Learning Management
Systems (LMS) and our tool. This allows the LMS to install our
application under specific contexts (courses).

The workflow is split across 2 functions

`handle_oidc_authorize`
1. The LMS sends request for OIDC parameters to this endpoint
2. We create parameters with metadata and send back

`handle_oidc_launch`
3. If authorized, the LMS sends back encrypted data to this endpoint
4. We decrypt, to get information about the user
5. We verify ourselves against the LMS to generate an auth token
6. User and auth information is stored in the session
'''

import aiohttp
import aiohttp_session
import jwt
import pmss
import time
import uuid
from aiohttp import web
from urllib.parse import urlencode

import learning_observer.auth.utils
import learning_observer.constants as constants
import learning_observer.settings

'''
Items in settings should look like
{
    'auth_uri': 'https://canvas.instructure.com/api/lti/authorize_redirect',
    'jwks_uri': 'https://canvas.instructure.com/api/lti/security/jwks',
    'token_uri': 'https://canvas.instructure.com/login/oauth2/token',
    'client_id': 'YOUR_CLIENT_ID',
    'redirect_uri': 'https://yourdomain.com/lti/canvas/launch',
    'private_key_path': './keys/canvas/private.pem'
}
'''
pmss.register_field(
    name='redirect_uri',
    type=pmss.pmsstypes.TYPES.string,
    description='Where to redirect a user after successful OAuth login',
    required=True
)
pmss.register_field(
    name='private_key_path',
    type=pmss.pmsstypes.TYPES.string,
    description='Path to where private key is stored',
    required=True
)

# TODO: Implement persistent configuration storage
# TODO: Add rate limiting for JWKS requests
# TODO: Implement CSRF protection for state parameter

# ===============================
# JWKS/JWT Validation Utilities
# ===============================
# The JSON Web Key Sets (JWKS) is used for verifying
# JSON Web Tokens (JWT) that were issued and signed.

# Validates LTI launch JWTs by:
# 1. Fetching the provider's JWKS (get_jwks),
# 2. Identifying the correct key via the token's unverified header (find_jwk),
# 3. Converting the JWK to an RSA public key (get_public_key), and
# 4. Verifying the token's signature/claims (validate_jwt). Handles key rotation
# via dynamic JWKS updates and enforces LTI 1.3 security requirements including
# expiration, issuer validation, and message integrity checks.

JWKS_CACHE = {}


async def get_jwks(provider: str) -> dict:
    '''Get the specified JWKS
    This fetches and caches JWKS from an external service.
    '''
    jwks_uri = learning_observer.settings.pmss_settings.jwks_uri(types=['auth', 'lti', provider])

    if provider not in JWKS_CACHE:
        async with aiohttp.ClientSession() as session:
            async with session.get(jwks_uri) as response:
                JWKS_CACHE[provider] = await response.json()
    return JWKS_CACHE[provider]


def find_jwk(jwks: dict, kid: str) -> dict:
    '''Extracts JWK by key ID'''
    return next((k for k in jwks.get('keys', []) if k.get('kid') == kid), None)


def get_public_key(provider: str, kid: str):
    '''Get RSA public key from our JWKS to verify token signature
    '''
    jwks = JWKS_CACHE.get(provider, {})
    if jwk := find_jwk(jwks, kid):
        return jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
    return None


def get_unverified_claims(token: str) -> tuple[dict, dict]:
    '''Extract unverified headers and claims from JWT
    We need to extract some information from the token so
    we can know the `kid`, `aud`, and `iss`.
    '''
    return (
        jwt.get_unverified_header(token),
        jwt.decode(token, options={'verify_signature': False})
    )


async def validate_jwt(provider: str, token: str) -> dict:
    '''Decode JWT token
    This uses the provider's public key to decode the token
    provided by the LMS to our launch endpoint.
    '''
    headers, claims = get_unverified_claims(token)

    await get_jwks(provider)  # Ensure JWKS are cached
    if not (public_key := get_public_key(provider, headers.get('kid'))):
        raise jwt.exceptions.InvalidTokenError('Invalid key ID')

    return jwt.decode(
        token,
        public_key,
        algorithms=['RS256'],
        audience=claims.get('aud'),
        issuer=claims.get('iss')
    )


# ======================
# Client Assertion
# ======================
# Generates OAuth 2.0 client assertion JWTs for secure authentication with LTI
# platforms. Uses RSA-SHA256 to sign claims containing client identity (iss/sub),
# token endpoint (aud), timestamp controls (iat/exp), and unique JTI.


def read_private_key(path: str) -> str:
    '''Read PEM-formatted private key from file'''
    return open(path, 'r').read()


def generate_assertion(provider) -> str:
    '''Generate signed client assertion JWT'''
    private_key_path = learning_observer.settings.pmss_settings.private_key_path(types=['auth', 'lti', provider])
    private_key = read_private_key(private_key_path)

    now = time.time()
    client_id = learning_observer.settings.pmss_settings.client_id(types=['auth', 'lti', provider])
    token_uri = learning_observer.settings.pmss_settings.token_uri(types=['auth', 'lti', provider])

    # Note the client is both the issuer and subject since
    # it is proving its own identity
    payload = {
        'iss': client_id,   # issuer
        'sub': client_id,   # subject
        'aud': token_uri,   # audience
        'iat': now,         # JWT issued at
        'exp': now + 300,   # JWT expiration
        'jti': str(uuid.uuid4()) # JWT ID
    }
    return jwt.encode(payload, private_key, algorithm='RS256')


# ======================
# OIDC Authorization Flow
# ======================
# Implements LTI 1.3's OpenID Connect (OIDC) authentication handshake.
# OIDC establishes a secure SSO channel between Learning Management
# Systems (LMS) and our tool.

# ======================
# OIDC Login Handler
# ======================
# Process the request from the LMS for OIDC parameters. Then
# send the parameters back to the LMS.


def create_oidc_params(provider, data: dict) -> dict:
    '''Generate OIDC authorization request parameters'''
    return {
        'scope': 'openid',
        'response_type': 'id_token',
        'response_mode': 'form_post',
        'prompt': 'none',
        'client_id': learning_observer.settings.pmss_settings.client_id(types=['auth', 'lti', provider]),
        'redirect_uri': learning_observer.settings.pmss_settings.redirect_uri(types=['auth', 'lti', provider]),
        # help confirm state with future responses
        'nonce': str(uuid.uuid4()),
        'state': str(uuid.uuid4()),
        # hints provided by LMS
        'login_hint': data.get('login_hint', ''),
        'lti_message_hint': data.get('lti_message_hint', '')
    }


async def handle_oidc_authorize(request: web.Request) -> web.Response:
    '''Initiate OIDC authorization flow.
    Create OIDC request parameters and send them to the
    LMS to verify.

    This function is registered to route `/lti/{provider}/login`
    '''
    provider = request.match_info['provider']
    data = await request.post()

    params = create_oidc_params(provider, data)
    session = await aiohttp_session.get_session(request)
    session.update({
        'lti_state': params['state'],
        'lti_nonce': params['nonce']
    })
    redirect_base_url = learning_observer.settings.pmss_settings.auth_uri(types=['auth', 'lti', provider])
    return web.HTTPFound(
        location=f"{redirect_base_url}?{urlencode(params)}"
    )


# ======================
# OIDC Launch Handler
# ======================
# Process request from LMS after they've verified who we are.
# We store the user and their auth token in the session.


def validate_oidc_state(session: dict, state: str) -> None:
    '''Validate OIDC state parameter matches session'''
    if session.get('lti_state') != state:
        raise web.HTTPBadRequest(text='Invalid state parameter')


def create_user(claims: dict) -> dict:
    '''Create user session data from LTI claims
    The created user is consistent with the rest of LO.
    '''
    roles = claims.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
    is_instructor = 'http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor' in roles
    return {
        constants.USER_ID: claims['sub'],
        'email': claims.get('email'),
        'name': claims.get('given_name'),
        'family_name': claims.get('family_name', ''),
        'picture': claims.get('picture', ''),
        'role': learning_observer.auth.ROLES.TEACHER if is_instructor else learning_observer.auth.ROLES.STUDENT,
        'authorized': is_instructor
        # TODO figure out backto. With google sso, we had a state we could store things in
        # 'back_to': request.query.get('state')
    }


async def exchange_for_token(provider, assertion: str) -> str:
    '''Exchange client assertion for access token'''
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=learning_observer.settings.pmss_settings.token_uri(types=['auth', 'lti', provider]),
            data={
                'grant_type': 'client_credentials',
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': assertion,
                'scope': ' '.join([
                    # Can retrieve user data associated with the context the tool is installed in
                    'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly',
                    # TODO not sure which of these we want for assignments
                    # Can view assignment data in the gradebook associated with the tool
                    'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly',
                    # Can create and update submission results for assignments associated with the tool
                    'https://purl.imsglobal.org/spec/lti-ags/scope/score',
                ])
            }
        ) as response:
            if response.status != 200:
                raise web.HTTPBadRequest(text=await response.text())
            return (await response.json())['access_token']


async def handle_oidc_launch(request: web.Request) -> web.Response:
    '''Process OIDC launch response
    After the LMS server confirms our identity, it sends information
    about the user to this endpoint. We exchange that information for
    an API token and store it in the user's session. This token is
    used later for getting the roster/assignments/etc.

    This function is registered to route `/lti/{provider}/launch`
    '''
    provider = request.match_info['provider']
    data = await request.post()

    try:
        # Validate OIDC response
        session = await aiohttp_session.get_session(request)
        validate_oidc_state(session, data.get('state'))

        # Verify and decode JWT
        claims = await validate_jwt(provider, data.get('id_token'))
        if claims['nonce'] != session.get('lti_nonce'):
            raise web.HTTPBadRequest(text='Invalid nonce')

        # Create user session
        user_info = create_user(claims)
        await learning_observer.auth.utils.update_session_user_info(request, user_info)

        # Exchange for access token
        assertion = generate_assertion(provider)
        access_token = await exchange_for_token(provider, assertion)

        # Store auth headers
        headers = {'Authorization': f'Bearer {access_token}'}
        session[constants.AUTH_HEADERS] = headers
        request[constants.AUTH_HEADERS] = headers

        return web.HTTPFound(location='/')

    except (jwt.PyJWTError, KeyError) as e:
        raise web.HTTPUnauthorized(text=f'Authentication failed: {e}')
