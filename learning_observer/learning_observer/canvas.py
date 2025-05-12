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


@register_cleaner("course_list", "courses")
def clean_course_list(canvas_json):
    '''
    The LTI integration Canvas uses for auth occurs on a
    course by course level. This cleaner wraps the current
    course in a list.
    '''
    # TODO we need to clean this code up
    cleaned = [canvas_json]
    return cleaned


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
    for member in members:
        # Map Canvas user ID to internal user ID format
        canvas_id = member.get('user_id')
        if canvas_id:
            local_id = f"canvas-{canvas_id}"
            member[constants.USER_ID] = local_id

            # Add external ID reference
            if 'email' not in member:
                member['email'] = ''

    return members


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
