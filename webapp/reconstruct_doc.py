'''
This can reconstruct a Google Doc from Google's JSON requests. It
is based on the reverse-engineering by James Somers in his blog
post about the Traceback extension. The code is, obviously, all
new.

See: `http://features.jsomers.net/how-i-reverse-engineered-google-docs/`
'''

import json

class google_text(object):
    '''
    We encapsulate a string object to support a Google Doc snapshot at a
    point in time. Right now, this adds cursor position. In the future,
    we might annotate formatting and similar properties.
    '''
    def __new__(cls):
        o = object.__new__(cls)
        o._text = ""
        o._position = 0
        o._deane = []
        return o

    def from_json(cls, json):
        o = google_text.__new__()
        o._text = json['text']
        o._position = json.get('position', 0)
        o._deane = json.get('deane', [])

    def update(self, text):
        self._text = text

    def len(self):
        return len(self._text)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, p):
        self._deane.append([len(self._text), p])
        self._position = p

    @property
    def deane(self):
        return self._deane

    def __str__(self):
        return self._text

    @property
    def json(self):
        return {
            'text': self._text,
            'position': self._position,
            'deane': self._deane
        }

def command_list(doc, commands):
    '''
    This will process a list of commands. It is helpful either when
    loading the history of a new doc, or in updating a document from
    new `save` requests.
    '''
    for item in commands:
        doc = dispatch[item['ty']](doc, **item)
    return doc


def multi(doc, mts, ty):
    '''
    Handles a batch of commands.

    `mts` is the list of commands
    `ty` is always `mlti`
    '''
    doc = command_list(doc, mts)
    return doc


def insert(doc, ty, ibi, s):
    '''
    Insert new text.
    * `ty` is always `is`
    * `ibi` is where the insert happens
    * `s` is the string to insert
    '''
    doc.update("{start}{insert}{end}".format(
        start=doc._text[0:ibi-1],
        insert=s,
        end=doc._text[ibi-1:]
    ))

    doc.position = ibi+len(s)

    return doc


def delete(doc, ty, si, ei):
    '''
    Delete text.
    * `ty` is always `ds`
    * `si` is the index of the start of deletion
    * `ei` is the end
    '''
    doc.update("{start}{end}".format(
        start=doc._text[0:si-1],
        end=doc._text[ei:]
    ))

    doc.position = si

    return doc


def alter(doc, si, ei, st, sm, ty):
    '''
    Alter commands change formatting.

    We ignore these for now.
    '''
    return doc

def null(doc, **kwargs):
    '''
    Do nothing. Google sometimes makes null requests. There are also
    requests we don't know how to process.

    I'm not quite sure what these are. The command is not JavaScript's
    `null` but the string `'null'`
    '''
    return doc


# This dictionary maps the `ty` parameter to the function which
# handles data of that type.
dispatch = {
    'ae': null,    ## TODO: `ae,``ue,` `de,` and `te` need to be reverse-engineered. These happens if we e.g. make a new bullet list, or add an image.
    'ue': null,
    'de': null,
    'te': null,
    'as': alter,
    'ds': delete,
    'is': insert,
    'mlti': multi,
    'null': null
}

if __name__ == '__main__':
    google_json = json.load(open("sample3.json"))
    docs_history = google_json['client']['history']['changelog']
    docs_history_short = [t[0] for t in docs_history]
    doc = google_text()
    doc = command_list(doc, docs_history_short)
    print(doc)
    print(doc.position)
    print(doc.deane)
