'''
This module is used for handling the ability to mask
yourself as other users on the system.

This is prototype code.
'''
import aiohttp
import aiohttp_session

import learning_observer.auth

IMPERSONATING_AS = 'impersonating_as'


@learning_observer.auth.admin
async def start_impersonation(request):
    session = await aiohttp_session.get_session(request)
    requested_user_id = request.match_info['user_id']

    # TODO we should pull more of the users information from somewhere
    session[IMPERSONATING_AS] = {'user_id': requested_user_id}
    return aiohttp.web.Response(text=f'Impersonating: {requested_user_id}')


async def stop_impersonation(request):
    session = await aiohttp_session.get_session(request)
    if IMPERSONATING_AS in session:
        del session[IMPERSONATING_AS]
        return aiohttp.web.Response(text='Done impersonating user.')
    return aiohttp.web.Response(text='Not impersonating anyone.')
