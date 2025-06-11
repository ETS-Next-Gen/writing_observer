import pmss
import re

import learning_observer.kvs
import learning_observer.constants as constants
import learning_observer.settings as settings

from . import util

pmss.register_field(
    name='api_domain',
    type=pmss.pmsstypes.TYPES.string,
    description='Domain of the api calls',
    required=True
)


def setup_canvas_provider(provider):
    # TODO pull the base url from settings based on provider
    base_url = settings.pmss_settings.api_domain(types=['auth', 'lti', provider])

    ENDPOINTS = list(map(lambda x: util.Endpoint(*x, api_name=provider), [
        ('course_list', base_url + '/api/lti/courses/{courseId}/names_and_roles'),
        ('course_roster', base_url + '/api/lti/courses/{courseId}/names_and_roles'),
        ('course_lineitems', base_url + '/api/lti/courses/{courseId}/line_items'),
    ]))

    register_cleaner = util.make_cleaner_registrar(ENDPOINTS)

    def register_canvas_endpoints(app):
        if not settings.feature_flag('canvas_routes'):
            return

        # Create the API routes and get back the functions
        return util.register_endpoints(
            app=app,
            endpoints=ENDPOINTS,
            api_name=provider,
            feature_flag_name='canvas_routes'
        )

    def _extract_course_id_from_url(url):
        if match := re.search(r'/courses/(\d+)/names_and_role', url):
            return match.group(1)
        return None

    @register_cleaner('course_list', 'courses')
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

    async def _lookup_gid_by_email(email):
        kvs = learning_observer.kvs.KVS()
        key = f'email-studentID-mapping:{email}'
        id = await kvs[key]
        if id:
            return f'gid-{id}'
        return None

    async def _process_canvas_user_for_system(member):
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
    async def clean_course_roster(canvas_json):
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
            user = await _process_canvas_user_for_system(m)
            if user is not None:
                users.append(user)

        return users

    @register_cleaner('course_lineitems', 'assignments') 
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

    return register_canvas_endpoints
