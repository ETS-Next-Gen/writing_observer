'''
This is a remote script for random `git` operations (e.g. running
on machines in the Learning Observer flock).

This is a bit awkward, but we maintain:

- Public `git` repositories in `/home/ubuntu/`
- Private `git` repositories in `/home/ubuntu/baregit` cloned into
  `/home/ubuntu`

The reason for this design is:

- Pushing a nonpublic repo to a remote server is a bit awkward. Versions
  of `git` in current distros do *not* support `push`ing into a non-bare
  repo (although this functionaly was added to bleeding edge git). If 
  we're pushing, we want to push into a bare repo
- For use (e.g. for 

We would like to do this (relatively) statelessly, so that if a repo
exists, we can do an update. If it's up-to-date, we can do nothing. If
it's not there, we create it.

As of this writing, this is not fully tested. We're going to test more
fully by finishing the side from where we're orchestrating.
'''

import os
import os.path

from invoke import task


WORKING_REPO_PATH='/home/ubuntu/'
BARE_REPO_PATH='/home/ubuntu/baregit/'

# If we don't have a path for bare repos, create it.
os.system("mkdir -p "+BARE_REPO_PATH)


def gitpath_to_name(packagepath):
    '''
    Convert a git path to the name of the repo. For example:

    `https://github.com/ETS-Next-Gen/writing_observer.git` ==> `writing_observer`
    '''
    package = os.path.split(packagepath)[1]
    if package.endswith(".git"):
        return package[:-4]
    else:
        return package


def working_repopath(repo=""):
    '''
    Switch to the path where *working* `git` repo is located. E.g. one
    with a working tree, if it exists.
    '''
    path = os.path.join(WORKING_REPO_PATH, repo)
    if os.path.exists(path):
        os.chdir(path)
        return path
    return False


def bare_repopath(repo=""):
    '''
    Switch to the path where *bare* `git` repo is located. E.g. one
    without a working tree, for pushing and pulling.
    '''
    path = os.path.join(BARE_REPO_PATH, repo)
    if os.path.exists(path):
        os.chdir(path)
        return path
    return False


@task
def branch(c, repo, branch):
    '''
    Switch to a branch in a repo.
    '''
    print("Going to to: ", working_repopath(repo))
    os.system("git checkout "+branch)


@task
def init(c, repo):
    '''
    Create a new bare repo, if one does not exist already.

    Otherwise, continue on silently.

    This is for force pushes of remote repos.
    '''
    path = bare_repopath(repo)
    if not path:
        bare_repopath()
        os.system("git --bare init "+repo)
    print(bare_repopath(repo))


@task
def cloneupdate(c, repopath):
    '''
    Clone a remote repo.
    '''
    working_repopath()
    if not working_repopath(gitpath_to_name(repopath)):
        print("Cloning...")
        os.system("git clone "+repopath)
        working_repopath(gitpath_to_name(repopath))

    print("Updating all branches")
    os.system("git fetch --all")

@task
def cloneupdatelocal(c, repo):
    clone_update(bare_repopath(repo))


@task
def pull(c, repo):
    '''
    Update a repo to the latest version.
    '''
    path = working_repopath(repo)
    os.system("git pull --all")
    return path
