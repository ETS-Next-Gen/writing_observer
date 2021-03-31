'''
We will need to support IDs from multiple systems. These are helper
functions to convert IDs. For example, we would convert a Google ID
like `72635729500910017892163494291` to
`gc-72635729500910017892163494291`. In the process, we also
double-check to make sure these are well-formed (in the above case, by
converting to int and back).
'''


def google_id_to_user_id(google_id):
    '''
    Convert a Google ID like:
    `72635729500910017892163494291`
    to:
    `gc-72635729500910017892163494291`
    '''
    try:
        return "gc-" + str(int(google_id))
    except ValueError:
        print("Error handling:", google_id)
        raise
