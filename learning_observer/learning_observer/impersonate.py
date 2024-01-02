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
    '''Pretend to be a different user.

    TODO: currently only admins have unlimited access
    to this feature. In the future, we want to allow
    other types of users to use this.
    '''
    session = await aiohttp_session.get_session(request)
    requested_user_id = request.match_info['user_id']

    # TODO we should pull more of the users information from somewhere
    # and confirm we are allowed to become this user.
    session[IMPERSONATING_AS] = {'user_id': requested_user_id}
    return aiohttp.web.json_response({'message': f'Impersonating: {requested_user_id}'})


async def stop_impersonation(request):
    '''Stop pretending to be someone you're not.
    '''
    session = await aiohttp_session.get_session(request)
    if IMPERSONATING_AS in session:
        del session[IMPERSONATING_AS]
        return aiohttp.web.json_response({'message': 'Done impersonating user.'})
    return aiohttp.web.json_response({'message': 'Not impersonating anyone.'})
