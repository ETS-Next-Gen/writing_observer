import datetime
import inspect
import json

mainlog = open("logs/main_log.json", "ab", 0)
files = {}

def log_event(event, filename=None, preencoded=False, timestamp=False):
    if filename is None:
        fp = mainlog;
    elif filename in files:
        return files[filename]
    else:
        fp = open("logs/" + filename + ".log", "ab", 0)
        files[filename] = fp

    if not preencoded:
        event = json.dumps(event, sort_keys=True)
    fp.write(event.encode('utf-8'))
    if timestamp:
        fp.write("\t".encode('utf-8'))
        fp.write(datetime.datetime.utcnow().isoformat().encode('utf-8'))
    fp.write("\n".encode('utf-8'))
    fp.flush()
