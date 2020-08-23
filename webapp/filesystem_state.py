import hashlib
import os
import subprocess

extensions = [
    ".py",
    ".js",
    ".html",
    ".md"
]

filestring = """{filename}:
\thash:{hash}
\tst_mode:{st_mode}
\tst_size:{st_size}
\tst_atime:{st_atime}
\tst_mtime:{st_mtime}
\tst_ctime:{st_ctime}
"""

def filesystem_state():
    '''
    Make a snapshot of the file system. Return a json object. Best
    usage is to combine with `yaml.dump`, or `json.dump` with a
    specific indent. This is helpful for knowing which version was running.

    Snapshot contains list of Python, HTML, JSON, and Markdown files,
    together with their SHA hashes and modified times. It also
    contains a `git` hash of the current commit.

    This ought to be enough to confirm which version of the tool is
    running, and if we are running from a `git` commit (as we ought to
    in production) or if changes were made since git commited.
    '''
    file_info = {}
    for root, dirs, files in os.walk("."):
        for name in files:
            for extension in extensions:
                if name.endswith(extension):
                    filename = os.path.join(root, name)
                    stat = os.stat(filename)
                    file_info[filename] = {
                        "hash": hashlib.sha3_512(open(filename, "rb").read()).hexdigest(),
                        "st_mode": stat.st_mode,
                        "st_size": stat.st_size,
                        "st_atime": stat.st_atime,
                        "st_mtime": stat.st_mtime,
                        "st_ctime": stat.st_ctime
                    }
    file_info['::git-head::'] = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    return file_info

if __name__ == '__main__':
    import yaml
    print(yaml.dump(filesystem_state()))
