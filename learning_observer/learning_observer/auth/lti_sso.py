# lti_sso.py
"""
Generic LTI 1.3 Single Sign-On handler for multiple providers.
Uses functional programming approach with aiohttp.
"""

import uuid
import jwt
import aiohttp
from aiohttp import web
from time import time
from urllib.parse import urlencode
from jwt.exceptions import JWTException

import learning_observer.auth.utils
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


# TODO add startup decorator and remove default CONFIGS
@learning_observer.prestartup.register_init_function
async def init_lti_sso(app, provider_configs):
    """
    Initialize LTI SSO providers during application startup.

    Args:
        app: aiohttp web application
        provider_configs: List of dictionaries with provider configurations

    Example config:
    {
        "name": "canvas",
        "auth_url": "https://canvas.instructure.com/api/lti/authorize_redirect",
        "jwks_url": "https://canvas.instructure.com/api/lti/security/jwks",
        "token_url": "https://canvas.instructure.com/login/oauth2/token",
        "client_id": "YOUR_CLIENT_ID",
        "issuer": "https://canvas.instructure.com",
        "redirect_uri": "https://yourdomain.com/lti/canvas/launch",
        "private_key_path": "./keys/canvas/private.pem"
    }
    """
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
    """Get cached JWKS for a provider with async request support."""
    if provider not in _jwks_cache:
        config = _providers.get(provider)
        if not config:
            raise web.HTTPBadRequest(text="Invalid provider")

        async with aiohttp.ClientSession() as session:
            async with session.get(config['jwks_url']) as response:
                _jwks_cache[provider] = await response.json()

    return _jwks_cache[provider]


def get_public_key(provider, kid):
    """Extract public key from JWKS for a specific kid."""
    jwks = _jwks_cache.get(provider, {})
    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    return None


async def verify_jwt(provider, token):
    """Verify JWT using provider-specific configuration."""
    config = _providers.get(provider)
    if not config:
        raise ValueError("Unknown provider")

    try:
        # Get unverified headers first to find kid
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get('kid')

        # Fetch JWKS if not in cache
        if provider not in _jwks_cache:
            await get_jwks(provider)

        public_key = get_public_key(provider, kid)
        if not public_key:
            raise InvalidTokenError("Invalid key ID")

        return jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=config['client_id'],
            issuer=config['issuer']
        )
    except JWTException as e:
        raise web.HTTPUnauthorized(text=f"JWT validation failed: {str(e)}")


async def generate_client_assertion(provider):
    """Generate JWT client assertion for token exchange."""
    config = _providers.get(provider)
    if not config:
        raise web.HTTPBadRequest(text="Invalid provider")

    try:
        with open(config['private_key_path'], "r") as f:
            private_key = f.read()
            
        payload = {
            "iss": config['client_id'],
            "sub": config['client_id'],
            "aud": config['token_url'],
            "iat": int(time()),
            "exp": int(time()) + 300,
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, private_key, algorithm='RS256')
    except Exception as e:
        raise web.HTTPInternalServerError(
            text=f"Assertion generation failed: {str(e)}")


# ======================
# Request Handlers
# ======================


async def lti_handle_authorize(request):
    """Initiate OIDC login flow for the provider."""
    provider = request.match_info.get('provider')
    print('auth provider', provider)
    config = _providers.get(provider)
    print('auth config', config)
    if not config:
        return web.HTTPBadRequest(text="Invalid provider")

    params = {
        'scope': 'openid',
        'response_type': 'id_token',
        'response_mode': 'form_post',
        'prompt': 'none',
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'nonce': str(uuid.uuid4()),
        'state': str(uuid.uuid4()),
        'login_hint': await _get_login_hint(request),
        'lti_message_hint': await _get_lti_hint(request)
    }

    # Store nonce and state in session
    session = request.session
    session['lti_state'] = params['state']
    session['lti_nonce'] = params['nonce']

    auth_url = f"{config['auth_url']}?{urlencode(params)}"
    return web.HTTPFound(location=auth_url)


async def lti_handle_launch(request):
    """Handle OIDC launch response from provider."""
    provider = 'canvas'
    print('launch provider', provider)
    config = _providers.get(provider)
    print('launch config', config)
    if not config:
        return web.HTTPBadRequest(text="Invalid provider")

    data = await request.post()
    id_token = data.get('id_token')
    state = data.get('state')

    # Validate state
    session = await learning_observer.auth.utils.get_session(request)
    if session.get('lti_state') != state:
        return web.HTTPBadRequest(text="Invalid state parameter")

    try:
        # Verify JWT and extract claims
        claims = await verify_jwt(provider, id_token)

        # Validate nonce
        if claims.get('nonce') != session.get('lti_nonce'):
            return web.HTTPBadRequest(text="Invalid nonce")

        # Store LTI claims in session
        session['lti_user'] = {
            'id': claims.get('sub'),
            'name': claims.get('name', ''),
            'email': claims.get('email', ''),
            'roles': claims.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
        }

        # Store context information
        session['lti_context'] = claims.get(
            'https://purl.imsglobal.org/spec/lti/claim/context', {})

        # Generate and store access token for future API calls
        client_assertion = await generate_client_assertion(provider)
        session['lti_token'] = client_assertion  # TODO: Implement proper token storage

        return web.HTTPFound(location='/dashboard')

    except web.HTTPException as e:
        return e
    except Exception as e:
        return web.HTTPInternalServerError(text=str(e))


# ======================
# Helper Functions
# ======================


async def _get_login_hint(request):
    """Extract login hint from request parameters."""
    # TODO: Implement provider-specific login hint extraction
    return request.query.get('login_hint', '')


async def _get_lti_hint(request):
    """Extract LTI message hint from request parameters."""
    # TODO: Implement provider-specific message hint handling
    return request.query.get('lti_message_hint', '')


# TODO: Implement token refresh mechanism
# TODO: Add error handler templates
# TODO: Implement NRPS and AGS service integrations
