'''
This can reconstruct a Google Doc from Google's JSON requests. It
is based on the reverse-engineering by James Somers in his blog
post about the Traceback extension. The code is, obviously, all
new.

See: `http://features.jsomers.net/how-i-reverse-engineered-google-docs/`
'''

import json


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
    doc = "{start}{insert}{end}".format(
        start=doc[0:ibi-1],
        insert=s,
        end=doc[ibi:]
    )
    return doc


def delete(doc, ty, si, ei):
    '''
    Delete text.
    * `ty` is always `ds`
    * `si` is the index of the start of deletion
    * `ei` is the end
    '''
    doc = "{start}{end}".format(
        start=doc[0:si],
        end=doc[ei:])
    return doc


def alter(doc, si, ei, st, sm, ty):
    '''
    Alter commands change formatting.

    We ignore these for now.
    '''
    return doc


# This dictionary maps the `ty` parameter to the function which
# handles data of that type.
dispatch = {
    'is': insert,
    'ds': delete,
    'as': alter,
    'mlti': multi
}

if __name__ == '__main__':
    google_json = json.load(open("sample3.json"))
    docs_history = google_json['client']['history']['changelog']
    docs_history_short = [t[0] for t in docs_history]
    doc = ""
    doc = command_list(doc, docs_history_short)
    print(doc)
