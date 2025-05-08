# lti_sso.py
'''
Generic LTI 1.3 Single Sign-On handler for multiple providers.
Uses functional programming approach with aiohttp.
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

# TODO: Add proper logging configuration
# TODO: Implement persistent configuration storage
# TODO: Add rate limiting for JWKS requests
# TODO: Implement CSRF protection for state parameter

# ======================
# Configuration Setup
# ======================

_providers = {}
_jwks_cache = {}


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
        'redirect_uri': 'https://yourdomain.com/lti/canvas/launch',
        'private_key_path': './keys/canvas/private.pem'
    }
    '''
    provider_configs = []
    for config in provider_configs:
        provider_name = config['name']
        _providers[provider_name] = config

    # TODO: Load private keys at startup and keep in memory
    # TODO: Validate all provider configurations
    # TODO: Set up periodic JWKS cache refresh


# ======================
# Core Functionality
# ======================


async def get_jwks(provider):
    '''Get cached JWKS for a provider with async request support.'''
    if provider not in _jwks_cache:
        config = _providers.get(provider)
        if not config:
            raise web.HTTPBadRequest(text='Invalid provider')

        async with aiohttp.ClientSession() as session:
            async with session.get(config['jwks_url']) as response:
                _jwks_cache[provider] = await response.json()

    return _jwks_cache[provider]


def get_public_key(provider, kid):
    '''Extract public key from JWKS for a specific kid.'''
    jwks = _jwks_cache.get(provider, {})
    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    return None


async def verify_jwt(provider, token):
    '''Verify JWT using provider-specific configuration.'''
    config = _providers.get(provider)
    if not config:
        raise ValueError('Unknown provider')

    try:
        # Get unverified headers first to find kid
        unverified_headers = jwt.get_unverified_header(token)
        unverified_claims = jwt.decode(token, options={'verify_signature': False})
        kid = unverified_headers.get('kid')
        iss = unverified_claims.get('iss')
        aud = unverified_claims.get('aud')

        # Fetch JWKS if not in cache
        if provider not in _jwks_cache:
            await get_jwks(provider)

        public_key = get_public_key(provider, kid)
        if not public_key:
            raise jwt.exceptions.InvalidTokenError('Invalid key ID')

        return jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=aud,
            issuer=iss
        )
    except jwt.exceptions.PyJWTError as e:
        raise web.HTTPUnauthorized(text=f'JWT validation failed: {str(e)}')


async def generate_client_assertion(provider):
    '''Generate JWT client assertion for token exchange.'''
    config = _providers.get(provider)
    if not config:
        raise web.HTTPBadRequest(text='Invalid provider')

    try:
        with open(config['private_key_path'], 'r') as f:
            private_key = f.read()
            
        payload = {
            'iss': config['client_id'],
            'sub': config['client_id'],
            'aud': config['token_url'],
            'iat': int(time()),
            'exp': int(time()) + 300,
            'jti': str(uuid.uuid4())
        }
        return jwt.encode(payload, private_key, algorithm='RS256')
    except Exception as e:
        raise web.HTTPInternalServerError(
            text=f'Assertion generation failed: {str(e)}')


# ======================
# Request Handlers
# ======================


async def lti_handle_authorize(request):
    '''Initiate OIDC login flow for the provider.'''
    provider = request.match_info.get('provider')
    config = _providers.get(provider)
    if not config:
        return web.HTTPBadRequest(text='Invalid provider')

    data = await request.post()

    params = {
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

    # Store nonce and state in session
    session = await aiohttp_session.get_session()
    session['lti_state'] = params['state']
    session['lti_nonce'] = params['nonce']

    auth_url = f'{config["auth_url"]}?{urlencode(params)}'
    return web.HTTPFound(location=auth_url)


async def lti_handle_launch(request):
    '''Handle OIDC launch response from provider.'''
    provider = 'canvas'
    config = _providers.get(provider)
    if not config:
        return web.HTTPBadRequest(text='Invalid provider')

    data = await request.post()
    id_token = data.get('id_token')
    state = data.get('state')

    # Validate state
    session = await aiohttp_session.get_session(request)
    if session.get('lti_state') != state:
        return web.HTTPBadRequest(text='Invalid state parameter')

    try:
        # Verify JWT and extract claims
        claims = await verify_jwt(provider, id_token)

        # Validate nonce
        if claims.get('nonce') != session.get('lti_nonce'):
            return web.HTTPBadRequest(text='Invalid nonce')

        # Store LTI claims in session
        roles = claims.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
        instructor_check = 'http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor' in roles
        user = {
            constants.USER_ID: claims.get('sub'),
            'email': claims.get('email', ''),
            'name': claims.get('name', ''),
            'role': learning_observer.auth.ROLES.TEACHER if instructor_check else learning_observer.auth.ROLES.STUDENT,
            'authorized': instructor_check
            # TODO figure out backto. With google sso, we had a state we could store things in
            # 'back_to': request.query.get('state')
        }

        if user[constants.USER_ID] is None:
            return web.HTTPBadRequest(text='No user id found')

        await learning_observer.auth.utils.update_session_user_info(request, user)

        # Generate and exchange access token for future API calls
        client_assertion = await generate_client_assertion(provider)
        access_token = await _exchange_client_assertion_for_access_token(config, client_assertion)
        headers = {'Authorization': 'Bearer ' + access_token}
        session[constants.AUTH_HEADERS] = headers
        request[constants.AUTH_HEADERS] = headers
        print(session)
        return web.HTTPFound(location='/')

    except web.HTTPException as e:
        return e
    except Exception as e:
        return web.HTTPInternalServerError(text=str(e))


# ======================
# Helper Functions
# ======================


async def _exchange_client_assertion_for_access_token(config, client_assertion):
    token_url = config.get('token_endpoint')
    if not token_url:
        return web.HTTPInternalServerError(text='Missing token endpoint in provider config')

    # Request access token using client assertion
    async with aiohttp.ClientSession() as client_session:
        post_data = {
            'grant_type': 'client_credentials',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion': client_assertion,
            'scope': ' '.join([
                'https://purl.imsglobal.org/spec/lti-ags/scope/score',
                'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly'
            ])
        }
        async with client_session.post(token_url, data=post_data) as resp:
            if resp.status != 200:
                text = await resp.text()
                return web.HTTPBadRequest(text=f'Token request failed: {text}')

            token_data = await resp.json()
            access_token = token_data.get('access_token')
            if not access_token:
                return web.HTTPBadRequest(text='No access token in response')
    return access_token


# TODO: Implement token refresh mechanism
# TODO: Add error handler templates
# TODO: Implement NRPS and AGS service integrations
