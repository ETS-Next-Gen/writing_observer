import learning_observer.constants as constants
import learning_observer.kvs
import learning_observer.settings as settings

from . import util

API = 'schoology'

ENDPOINTS = list(map(lambda x: util.Endpoint(*x, api_name=API), [
    ('course_list', 'https://api.schoology.com/v1/users/{id}/sections'),
    ('course_roster', 'https://api.schoology.com/v1/sections/{courseId}/enrollments'),
    ('course_assignments', 'https://api.schoology.com/v1/sections/{courseId}/assignments'),
]))

register_cleaner = util.make_cleaner_registrar(ENDPOINTS)


def register_endpoints(app):
    '''
    '''
    if not settings.feature_flag('schoology_routes'):
        return

    return util.register_endpoints(
        app=app,
        endpoints=ENDPOINTS,
        api_name=API,
        feature_flag_name='schoology_routes'
    )


@register_cleaner('course_list', 'courses')
def clean_course_list(schoology_json):
    '''
    The LTI integration Schoology uses for auth occurs on a
    course by course level. This cleaner wraps the current
    course in a list.
    '''
    print('clean_course_list', schoology_json)
    return


# TODO this already exists in a different place - it should live in only one place
async def _lookup_gid_by_email(email):
    kvs = learning_observer.kvs.KVS()
    key = f'email-studentID-mapping:{email}'
    id = await kvs[key]
    if id:
        return f'gid-{id}'
    return None


async def _process_schoology_user_for_system(member):
    # Skip if no canvas id
    canvas_id = member.get('user_id')
    if not canvas_id: return None

    # Skip non students
    is_student = 'http://purl.imsglobal.org/vocab/lis/v2/membership#Learner' in member.get('roles', [])
    if not is_student: return None

    # Create user for our system
    email = member.get('email')
    local_id = await _lookup_gid_by_email(email)
    if not local_id:
        local_id = f'canvas-{canvas_id}'

    member[constants.USER_ID] = local_id
    user = {
        'profile': {
            'name': {
                'given_name': member.get('given_name'),
                'family_name': member.get('family_name'),
                'full_name': member.get('name')
            },
            'email_address': email,
            'photo_url': member.get('picture')
        },
        constants.USER_ID: local_id,
        # TODO is this needed? Other roster functions in LO include it
        # 'course_id': course_id
    }
    return user


@register_cleaner('course_roster', 'roster')
async def clean_course_roster(schoology_json):
    '''
    Retrieve and clean the roster for a Canvas course, alphabetically sorted

    Conforms to LTI NRPS v2 response format
    https://www.imsglobal.org/spec/lti-nrps/v2p0
    '''
    print('clean_course_roster', schoology_json)
    return
    # Process each student record
    # for m in members:
        # user = await _process_schoology_user_for_system(m)


@register_cleaner('course_assignments', 'assignments') 
def clean_course_assignments(schoology_json):
    '''
    Clean course line items (assignments) from Schoology

    Conforms to LTI AGS response format
    https://www.imsglobal.org/spec/lti-ags/v2p0
    '''
    print('clean_course_assignments', schoology_json)
    return
