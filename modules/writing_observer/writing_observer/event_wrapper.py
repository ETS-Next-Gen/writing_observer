"""
event_wrapper.py
Collin F. Lynch
2022

A big part of this project is wrapping up google doc events.
In doing that we are reverse-engineering some of the elements 
particularly the event types.  This code provides some basic
wrappers for event types to simplify extraction of key elements
and to simplify event recognition.  

Over time this will likely expand and will need to adapt to keep 
up with any changes in the event structure.  For now it is just 
a thin abstraction layer on a few of the pieces.
"""


# Imports
# --------------------------------
import json



# Basic class tests
# -------------------------------
def is_visibility_eventp(event):
    """
    Given an event return true if it is a visibility 
    event which indicates changing the doc shown or 
    active.

    Here we look for an event with 'client' 
    containing the field 'event_type' of 
    'visibility'
    """
    Event_Type = event.get('client', {}).get('event', None)
    return(Event_Type == 'visibility')


def is_keystroke_eventp(event):
    """
    Given an event return true if it is a keystroke 
    event which indicates changing the doc shown or 
    active.

    Here we look for an event with 'client' 
    containing the field 'event_type' of 
    'keystroke'
    """
    Event_Type = event.get('client', {}).get('event', None)
    return(Event_Type == 'visibility')



# ---------------------------------------
# Extraction Methods

def get_doc_id(event):
    """
    Some of the event types (e.g. 'google_docs_save') have 
    a 'doc_id' which provides a link to the google document.
    Others, notably the 'visibility' and 'keystroke' events
    do not have doc_id but do have a link to an 'object'
    field which in turn contains an 'id' field linking to 
    the google doc along with other features such as the 
    title.  

    This method provides a simple abstraction that returns 
    the 'doc_id' value if it exists or returns the 'id' from
    the 'object' field if this is a 'visibility' or 'keystroke'
    event.
    """

    # Handle standard Doc_ID cases first.
    Doc_ID = event.get('client', {}).get('doc_id', None)
    if (Doc_ID != None): return(Doc_ID)

    # Handle cases where the object is encoded.  For
    # safety we only do this for cases where it is a
    # keystroke or visibility item.
    if (is_keystroke_eventp(event)
        or is_visibility_eventp(event)):

        Doc_ID = event.get('client', {}).get('object', {}).get('id', None)
        return(Doc_ID)

    # As a bottom out case we just return None.
    
