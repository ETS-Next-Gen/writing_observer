# lti_sso.py
'''
Generic LTI 1.3 Single Sign-On handler for multiple providers.
'''

import uuid
import jwt
import jwt.exceptions
import aiohttp
import aiohttp_session
from aiohttp import web
from time import time
from urllib.parse import urlencode

import learning_observer.auth.utils
import learning_observer.constants as constants
import learning_observer.prestartup

# TODO: Implement persistent configuration storage
# TODO: Add rate limiting for JWKS requests
# TODO: Implement CSRF protection for state parameter

# ======================
# Configuration Setup
# ======================

PROVIDERS = {}
JWKS_CACHE = {}


@learning_observer.prestartup.register_startup_check
def init_lti_sso():
    '''
    Initialize LTI SSO providers during application startup.

    Example config:
    {
        'name': 'canvas',
        'auth_url': 'https://canvas.instructure.com/api/lti/authorize_redirect',
        'jwks_url': 'https://canvas.instructure.com/api/lti/security/jwks',
        'token_url': 'https://canvas.instructure.com/login/oauth2/token',
        'client_id': 'YOUR_CLIENT_ID',
        'redirect_uri': 'https://yourdomain.com/lti/launch/canvas',
        'private_key_path': './keys/canvas/private.pem'
    }
    '''
    # TODO read the provider configs from settings somehow
    provider_configs = []
    for config in provider_configs:
        provider_name = config['name']
        PROVIDERS[provider_name] = config


# ======================
# JWKS Utilities
# ======================


async def fetch_jwks(config: dict) -> dict:
    '''Fetch JWKS from provider's endpoint'''
    async with aiohttp.ClientSession() as session:
        async with session.get(config['jwks_url']) as response:
            return await response.json()


async def get_jwks(provider: str) -> dict:
    '''Get cached JWKS or fetch fresh if not available'''
    if provider not in JWKS_CACHE:
        config = get_provider_config(provider)
        JWKS_CACHE[provider] = await fetch_jwks(config)
    return JWKS_CACHE[provider]


def find_jwk(jwks: dict, kid: str) -> dict:
    '''Find JWK by key ID'''
    return next((k for k in jwks.get('keys', []) if k.get('kid') == kid), None)


def get_public_key(provider: str, kid: str):
    '''Get RSA public key from JWKS'''
    jwks = JWKS_CACHE.get(provider, {})
    if jwk := find_jwk(jwks, kid):
        return jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
    return None


# ======================
# JWT Validation
# ======================


def get_unverified_claims(token: str) -> tuple[dict, dict]:
    '''Extract unverified headers and claims from JWT'''
    return (
        jwt.get_unverified_header(token),
        jwt.decode(token, options={'verify_signature': False})
    )


async def validate_jwt(provider: str, token: str) -> dict:
    '''Validate JWT signature and claims'''
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


def read_private_key(path: str) -> str:
    '''Read PEM-formatted private key from file'''
    with open(path, 'r') as f:
        return f.read()


def create_assertion_payload(client_id: str, token_url: str) -> dict:
    '''Create JWT payload for client assertion'''
    now = int(time())
    return {
        'iss': client_id,
        'sub': client_id,
        'aud': token_url,
        'iat': now,
        'exp': now + 300,
        'jti': str(uuid.uuid4())
    }


def generate_assertion(config: dict) -> str:
    '''Generate signed client assertion JWT'''
    private_key = read_private_key(config['private_key_path'])
    payload = create_assertion_payload(config['client_id'], config['token_url'])
    return jwt.encode(payload, private_key, algorithm='RS256')


# ======================
# OIDC Handlers
# ======================


def validate_oidc_state(session: dict, state: str) -> None:
    '''Validate OIDC state parameter matches session'''
    if session.get('lti_state') != state:
        raise web.HTTPBadRequest(text='Invalid state parameter')


def create_oidc_params(config: dict, data: dict) -> dict:
    '''Generate OIDC authorization request parameters'''
    return {
        'scope': 'openid',
        'response_type': 'id_token',
        'response_mode': 'form_post',
        'prompt': 'none',
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'nonce': str(uuid.uuid4()),
        'state': str(uuid.uuid4()),
        'login_hint': data.get('login_hint', ''),
        'lti_message_hint': data.get('lti_message_hint', '')
    }


async def handle_oidc_authorize(request: web.Request) -> web.Response:
    '''Initiate OIDC authorization flow.
    Process information and send it back to the LMS requesting it.

    This function is registered to route `/lti/login/{provider}`
    '''
    provider = request.match_info['provider']
    config = get_provider_config(provider)
    data = await request.post()

    params = create_oidc_params(config, data)
    session = await aiohttp_session.get_session(request)
    session.update({
        'lti_state': params['state'],
        'lti_nonce': params['nonce']
    })

    return web.HTTPFound(
        location=f"{config['auth_url']}?{urlencode(params)}"
    )


# ======================
# Launch Handler
# ======================


def create_user(claims: dict) -> dict:
    '''Create user session data from LTI claims'''
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


async def exchange_for_token(config: dict, assertion: str) -> str:
    '''Exchange client assertion for access token'''
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=config['token_url'],
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

    This function is registered to route `/lti/launch/{provider}`
    '''
    provider = request.match_info['provider']
    config = get_provider_config(provider)
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
        assertion = generate_assertion(config)
        access_token = await exchange_for_token(config, assertion)

        # Store auth headers
        headers = {'Authorization': f'Bearer {access_token}'}
        session[constants.AUTH_HEADERS] = headers
        request[constants.AUTH_HEADERS] = headers

        return web.HTTPFound(location='/')

    except (jwt.PyJWTError, KeyError) as e:
        raise web.HTTPUnauthorized(text=f'Authentication failed: {e}')


# ======================
# Helper Functions
# ======================


def get_provider_config(provider: str) -> dict:
    '''Get provider configuration with validation'''
    if config := PROVIDERS.get(provider):
        return config
    raise web.HTTPBadRequest(text=f'Invalid provider: {provider}')

# TODO: Implement token refresh mechanism
