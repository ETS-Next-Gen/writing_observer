import datetime
import inspect
import json

mainlog = open("logs/main_log.json", "ab", 0)
files = {}


def log_event(event, filename=None, preencoded=False, timestamp=False):
    if filename is None:
        fp = mainlog
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


def debug_log(text):
    '''
    Helper function to help us trace our code.

    We print a time stamp, a stack trace, and a /short/ summary of
    what's going on.

    This is not intended for programmatic debugging. We do change
    format regularly (and you should feel free to do so too -- for
    example, on narrower terminals, a `\n\t` can help)
    '''
    stack = inspect.stack()
    stack_trace = "{s1}/{s2}/{s3}".format(
        s1=stack[1].function,
        s2=stack[2].function,
        s3=stack[3].function,
    )

    message = "{time}: {st:60}\t{body}".format(
        time=datetime.datetime.utcnow().isoformat(),
        st=stack_trace,
        body=text
    )
    print(message)
