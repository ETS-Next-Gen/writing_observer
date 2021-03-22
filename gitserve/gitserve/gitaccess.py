'''This is a small library to allow us to browse git repos.

Next steps:

* It's a little bit over-conservative in terms of sanitizing parameters
  to git. We should be more precise so we allow more filenames and branch
  names.
* We should really browse the git repo directly, without subprocess. I
  mean, really?
* Perhaps add more git commands?
'''

import pathvalidate
import string
import subprocess
import sys


def sanitize(fn):
    '''
    We'll be overly-conservative. We don't want security exploits. At
    some point, this should be made more narrow, but since we're calling
    into shell code in this version, we're super-careful
    '''
    valid_characters = "-_/."+string.ascii_letters+string.digits
    nfn = "".join(c for c in fn if c in valid_characters)
    nfn = pathvalidate.sanitize_filepath(nfn, platform='Linux', normalize=True)
    if nfn.startswith("/"):
        raise ValueError("Suspicious operation: String starts with /")
    if nfn.startswith("-"):
        raise ValueError("Suspicious operation: String starts with -")
    if ".." in nfn:
        raise ValueError("Suspicious operation: String contains ..")
    if nfn != fn:
        raise ValueError("Suspicious operation: Sanitized string does not equal original string")
    return nfn


class gitrepo:
    def __init__(self, gitdir):
        self.gitdir = gitdir

    def branches(self):
        '''
        Return a list of all local branches in the repo
        '''
        branches = subprocess.check_output(
            "git --git-dir={gitdir}/.git branch".format(
                gitdir=self.gitdir
            ), shell=True
        ).decode('utf-8')
        branches = branches.split('\n')
        branches = [b.replace('*', '').strip() for b in branches]
        branches = [b for b in branches if b != '']
        return branches

    def show(self, branch, filename):
        '''
        Return the contents of a file in the repo
        '''
        sanitized_branch = sanitize(branch) 
        sanitized_filename = sanitize(filename)
        if branch not in self.branches():
            raise ValueError("No such branch")
        data = subprocess.check_output(
            "git --git-dir={gitdir}/.git show {branch}:{filename}".format(
                gitdir=self.gitdir,
                branch=sanitized_branch,
                filename=sanitized_filename
            ), shell=True
        ).decode('utf-8')
        return data

    def rev_hash(self, branch):
        '''
        Return the git hash of a branch.
        '''
        sanitized_branch = sanitize(branch)
        data = subprocess.check_output(
            "git --git-dir={gitdir}/.git rev-parse {branch}".format(
                gitdir=self.gitdir,
                branch=sanitized_branch
            ),
            shell=True
        ).decode('utf-8').strip()
        if all(c in string.hexdigits for c in data):
            return data.strip()
        else:
            raise ValueError("Not a valid branch / hash")

if(__name__ == "__main__"):
    '''
    Simple test case. Show README.md from a repo specified on the command line.
    '''
    repo = gitrepo(sys.argv[1])
    branches = repo.branches()
    print(branches)
    print(repo.show(branches[-1], 'README.md'))
    print(repo.rev_hash(branches[-1]))
