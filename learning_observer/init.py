'''
This file mostly confirms we have prerequisites for the system to work.

We create a logs directory, grab 3rd party libraries, etc.
'''

import hashlib
import os
import os.path
import shutil
import sys

import paths

# These are directories we'd like created on startup. At the moment,
# they're for different types of log files.
directories = {
    'logs': {'path': paths.logs()},
    'startup logs': {'path': paths.logs('startup')},
    'AJAX logs': {'path': paths.logs('ajax')}
}

for d in directories:
    dirpath = directories[d]['path']
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
        print("Made {dirname} directory in {dirpath}".format(
            dirname=d,
            dirpath=dirpath
        ))

if not os.path.exists(paths.data("teachers.yaml")):
    shutil.copyfile(
        paths.data("teachers.yaml.template"),
        paths.data("teachers.yaml")
    )
    print("Created a blank teachers file: static_data/teachers.yaml\n"
          "Populate it with teacher accounts.")

if not os.path.exists(paths.config_file()):
    print("""
    Copy creds.yaml.sample into the top-level directory:

    cp creds.yaml.sample ../creds.yaml

    Fill in the missing fields.
    """)
    sys.exit(-1)

if not os.path.exists(paths.third_party()):
    os.mkdir(paths.third_party())


# Download any missing third-party files, and confirm their integrity.
# We download only if the file doesn't exist, but confirm integrity in
for name, url, sha in [
    ("require.js", "https://requirejs.org/docs/release/2.3.6/comments/require.js",
     "d1e7687c1b2990966131bc25a761f03d6de83115512c9ce85d72e4b9819fb873"
     "3463fa0d93ca31e2e42ebee6e425d811e3420a788a0fc95f745aa349e3b01901"),
    ("text.js",  # Use text files with require.js
     "https://raw.githubusercontent.com/requirejs/text/3f9d4c19b3a1a3c6f35650c5788cbea1db93197a/text.js",
     "fb8974f1633f261f77220329c7070ff214241ebd33a1434f2738572608efc8eb"
     "6699961734285e9500bbbd60990794883981fb113319503208822e6706bca0b8"),
    ("r.js",  # require.js bundler/optimizer
     "https://requirejs.org/docs/release/2.3.6/r.js",
     "52300a8371df306f45e981fd224b10cc586365d5637a19a24e710a2fa566f884"
     "50b8a3920e7af47ba7197ffefa707a179bc82a407f05c08508248e6b5084f457"),
    ("bulma.min.css",
     "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.0/css/bulma.min.css",
     "ec7342883fdb6fbd4db80d7b44938951c3903d2132fc3e4bf7363c6e6dc5295a"
     "478c930856177ac6257c32e1d1e10a4132c6c51d194b3174dc670ab8d116b362"),
    ("fontawesome.js",  # Icons
     "https://use.fontawesome.com/releases/v5.3.1/js/all.js -O fontawesome.js",
     "83e7b36f1545d5abe63bea9cd3505596998aea272dd05dee624b9a2c72f966261"
     "8d4bff6e51fafa25d41cb59bd97f3ebd72fd94ebd09a52c17c4c23fdca3962b"),
    ("showdown.js",  # Markdown interpreter
     "https://rawgit.com/showdownjs/showdown/1.9.1/dist/showdown.js",
     "4fe14f17c2a1d0275d44e06d7e68d2b177779196c6d0c562d082eb5435eec4e71"
     "0a625be524767aef3d9a1f6a5b88f912ddd71821f4a9df12ff7dd66d6fbb3c9"),
    ("showdown.js.map",
     "https://rawgit.com/showdownjs/showdown/1.9.1/dist/showdown.js.map",
     "74690aa3cea07fd075942ba9e98cf7297752994b93930acb3a1baa2d3042a62b5"
     "523d3da83177f63e6c02fe2a09c8414af9e1774dad892a303e15a86dbeb29ba"),
    ("mustache.min.js",  # Templating language
     "http://cdnjs.cloudflare.com/ajax/libs/mustache.js/3.1.0/mustache.min.js",
     "e7c446dc9ac2da9396cf401774efd9bd063d25920343eaed7bee9ad878840e846"
     "d48204d62755aede6f51ae6f169dcc9455f45c1b86ba1b42980ccf8f241af25"),
    ("d3.v5.min.js",  # General framework
     "https://d3js.org/d3.v5.min.js",
     "466fe57816d719048885357cccc91a082d8e5d3796f227f88a988bf36a5c2ceb7"
     "a4d25842f5f3c327a0151d682e648cd9623bfdcc7a18a70ac05cfd0ec434463"),
    ("bulma-tooltip-min.css",  # Tooltips for UX
     "https://cdn.jsdelivr.net/npm/@creativebulma/bulma-tooltip@1.2.0/dist/bulma-tooltip.min.css",
     "fc37b25fa75664a6aa91627a7b1298a09025c136085f99ba31b1861f073a0696c"
     "4756cb156531ccf5c630154d66f3059b6b589617bd6bd711ef665079f879405")]:
    filename = paths.third_party(name)
    if not os.path.exists(filename):
        os.system("wget {url} -O {filename} 2> /dev/null".format(
            url=url,
            filename=filename
        ))
        print("Downloaded {name}".format(name=name))
    shahash = hashlib.sha3_512(open(filename, "rb").read()).hexdigest()
    if shahash == sha:
        pass
        # print("File integrity of {name} confirmed!".format(name=filename))
    else:
        print("Incorrect SHA hash. Something odd is going on. DO NOT IGNORE THIS ERROR/WARNING")
        print()
        print("Expected SHA: " + sha)
        print("Actual SHA: " + shahash)
        print()
        print("We download 3rd party libraries from the Internet. This error means that ones of")
        print("these files changed. This may indicate a man-in-the-middle attack, that a CDN has")
        print("been compromised, or more prosaically, that one of the files had something like")
        print("a security fix backported. In either way, VERIFY what happened before moving on.")
        print("If unsure, please consult with a security expert.")
        print()
        print("This error should never happen unless someone is under attack (or there is a")
        print("serious bug).")
        # Do we want to os.unlink(filename) or just terminate?
        # Probably just terminate, so we can debug.
        sys.exit(-1)
        print()
