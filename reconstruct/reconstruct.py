import json
import pandas

js = json.load(open("chunked3.json"))

document = "  "

def apply_changes(document, changes):
    for change_line in changes:
        #if 'mts' in change[0]:
        #    del change[0]['mts']
        #print(change_line)
        if isinstance(change_line, list):
            change = change_line[0]
        else:
            change = change_line

        # Insert
        if change['ty'] == "is":
            document = document[:change['ibi']]+change['s']+document[change['ibi']:]
        # Multiple changes clumped together
        elif change['ty'] == "mlti":
            #print(change)
            document = apply_changes(document, change['mts'])
        # Delete from si to ei
        elif change['ty'] == "ds":
            document = document[:change["si"]]+document[change["ei"]:]
        # This formats text. We can ignore this for now. 
        elif change['ty'] == "as":
            pass
            #print(change)
        else:
            raise Exception("Unknown change")
    return document

document = apply_changes(" ", js['changelog'])
print(document)
