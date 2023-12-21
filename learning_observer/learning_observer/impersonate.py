'''
This module is used for handling the ability to mask
yourself as other users on the system.

This is prototype code.
'''
import aiohttp
import aiohttp_session

import learning_observer.auth


@learning_observer.auth.admin
async def start_impersonation(request):
    session = await aiohttp_session.get_session(request)
    requested_user_id = request.match_info['user_id']

    session['original_user_id'] = session['user']['user_id']
    session['user']['user_id'] = requested_user_id
    return aiohttp.web.Response(text=f'Masking as a new user: {requested_user_id}')


async def stop_impersonation(request):
    session = await aiohttp_session.get_session(request)
    if 'original_user_id' in session:
        session['user']['user_id'] = session['original_user_id']
        del session['original_user_id']
        return aiohttp.web.Response(text='Done masking user')
    return aiohttp.web.Response(text='Not impersonating anyone.')
