import os

import orchlib.config

import remote_scripts.gitpaths


# Working command: GIT_SSH_COMMAND="ssh -i KEY.pem" git --git-dir=/tmp/foo/.git push -f --mirror ssh://ubuntu@SOME_SERVER/home/ubuntu/baregit/foo


# This command will forcefully push a local repo to a remote server
GIT_PUSH ='''
GIT_SSH_COMMAND="ssh -i {key}" git 
    --git-dir={localrepo} 
    push -f
    ssh://ubuntu@{mn}.learning-observer.org/home/ubuntu/baregit/{reponame}
'''.strip().replace('\n', '')


def force_push(machine, localrepo):
    print("LOCAL REPO: ", localrepo)
    command = GIT_PUSH.format(
        mn=machine,
        key=orchlib.config.creds['key_filename'],
        localrepo=localrepo,
        reponame=remote_scripts.gitpaths.gitpath_to_name(localrepo)
    )
    print(command)
    os.system(command)


def remote_invoke(group, command):
    remote_command = "cd writing_observer/devops/remote_scripts; inv {command}".format(command=command)
    print(remote_command)
    group.run(remote_command)


def update(group, machine_name):
    # In most cases, these would correspond to static sites, or
    # Learning Observer modules
    print("Grabbing public git packages")
    for package in orchlib.config.config_lines(machine_name, "gitclone"):
        remote_invoke(group, "cloneupdate {package}".format(package=package))
    print("Pushing private git packages")

    # We can only push to bare repos. 
    for package in orchlib.config.config_lines(machine_name, "gitpush"):
        remote_invoke(group, "init {package}".format(package=package))
        force_push(machine_name, package)
        remote_invoke(group, "cloneupdatelocal {package}".format(package=package))
