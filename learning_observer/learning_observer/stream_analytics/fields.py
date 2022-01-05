import enum
import functools

@functools.total_ordering
class EventField:
    '''
    This is a field type used for extracting a particular element from an event.
    '''
    def __init__(self, event):
        self.event = event

    def __hash__(self):
        return hash(self.event)

    def name(self):
        return("EventField."+self.event)

    def __str__(self):
        return self.name()

    def __repr__(self):
        return "<{name}>".format(name=self.name())

    def __eq__(self, other):
        if not isinstance(other, EventField):
            return False

        return self.event == other.event

    def __lt__(self, other):
        if not isinstance(other, EventField):
            raise TypeError("< not supported between instances of 'EventField' and other types")

        return self.event < other.event

KeyStateType = enum.Enum("KeyStateType", "INTERNAL EXTERNAL")

# This is a set of fields which we use to index reducers. For example,
# if we'd like to know how many students accessed a specific Google
# Doc, we might create a RESOURCE key (which would receive events for
# all students accessing that resource). If we'd like to keep track of
# a students' work in a particular Google Doc, we'd create a
# STUDENT/RESOURCE key.
#
# At some point, this shouldn't be hardcoded
#
# We'd also like a better way to think of the hierarchy of assignments than ITEM/ASSIGNMENT
KeyFields = [
    "STUDENT",    # A single student
    "CLASS",      # A group of students. Typically, one class roster in Google Classroom
    "RESOURCE"    # E.g. One Google Doc
#   "ASSIGNMENT"  # E.g. A collection of Google Docs (e.g. notes, outline, draft)
#   "TEACHER"     #
#    ...          # ... and so on.
]

KeyField = enum.Enum("KeyField", " ".join(KeyFields))

class Scope(frozenset):
    pass
