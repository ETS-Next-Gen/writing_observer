import re

import learning_observer.constants as constants
import learning_observer.settings as settings

from learning_observer.external_apis import Endpoint, initialize_and_register_routes, register_cleaner_factory

ENDPOINTS = list(map(lambda x: Endpoint(*x, api_name='canvas'), [
    # TODO we need to figure out the base of this url
    ("course_list", "TODO figure this ou"),
    ("course_roster", "/api/lti/courses/{courseId}/names_and_role"),
    ("course_lineitems", "/api/lti/courses/{courseId}/line_items"),
]))

register_cleaner = register_cleaner_factory(ENDPOINTS)


def initialize_and_register_canvas_routes(app):
    if not settings.feature_flag('canvas_routes'):
        return

    # Create the API routes and get back the functions
    global_functions = initialize_and_register_routes(
        app=app,
        endpoints=ENDPOINTS,
        api_name='canvas',
        feature_flag_name='canvas_routes'
    )

    # Add the functions to the module's global namespace
    globals().update(global_functions)


def _extract_course_id_from_url(url):
    if match := re.search(r'/courses/(\d+)/names_and_role', url):
        return match.group(1)
    return None


@register_cleaner("course_list", "courses")
def clean_course_list(canvas_json):
    '''
    The LTI integration Canvas uses for auth occurs on a
    course by course level. This cleaner wraps the current
    course in a list.
    '''
    context = canvas_json.get('context', {})
    if not (id := _extract_course_id_from_url(canvas_json.get('id', ''))):
        raise ValueError('Canvas json did not provide a parsable id')
    course = {
        'id': id,
        'name': context.get('label'),
        'title': context.get('title'),
        'lti_id': context.get('id')
    }
    cleaned = [course]
    return cleaned


def _process_canvas_user_for_system(member):
    # Skip if no canvas id
    canvas_id = member.get('user_id')
    if not canvas_id: return None

    # Skip non students
    is_student = 'http://purl.imsglobal.org/vocab/lis/v2/membership#Learner' in member.get('roles', [])
    if not is_student: return None

    # Create user for our system
    # TODO map email to google id and use instead of this local id
    local_id = f'canvas-{canvas_id}'
    member[constants.USER_ID] = local_id
    user = {
        'profile': {
            'name': {
                'given_name': member.get('given_name'),
                'family_name': member.get('family_name'),
                'full_name': member.get('name')
            },
            'email': member.get('email'),
            'photo_url': member.get('picture')
        },
        constants.USER_ID: local_id,
        # TODO is this needed? Other rosters include it
        # 'course_id': course_id
    }
    return user


@register_cleaner("course_roster", "roster")
def clean_course_roster(canvas_json):
    '''
    Retrieve and clean the roster for a Canvas course, alphabetically sorted

    Conforms to LTI NRPS v2 response format
    https://www.imsglobal.org/spec/lti-nrps/v2p0
    '''
    members = canvas_json.get('members', [])
    members.sort(
        key=lambda x: x.get('name', 'ZZ'),
    )
    # Process each student record
    users = []
    for m in members:
        user = _process_canvas_user_for_system(m)
        if user is not None:
            users.append(user)

    return users


@register_cleaner("course_lineitems", "assignments") 
def clean_course_assignments(canvas_json):
    '''
    Clean course line items (assignments) from Canvas

    Conforms to LTI AGS response format
    https://www.imsglobal.org/spec/lti-ags/v2p0
    '''
    line_items = canvas_json
    if not isinstance(line_items, list):
        # If it's not already a list, check for lineItems property that might contain the list
        line_items = canvas_json.get('lineItems', [])

    # Sort by due date if available, otherwise by title
    line_items.sort(
        key=lambda x: x.get('endDateTime', x.get('label', 'ZZ')),
    )
    return line_items
