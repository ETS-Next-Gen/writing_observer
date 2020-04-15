import json

fp = open("log.json", "a")

def log_event(event):
    print(event)
    fp.write(json.dumps(event))
    fp.write("\n")
    fp.flush()
