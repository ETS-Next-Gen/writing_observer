from invoke import task

import csv
import sys
import os

import orchlib.aws
import orchlib.config
import orchlib.fabric_flock
import orchlib.templates
import orchlib.ubuntu


@task
def list(c):
    '''
    Give a human-friendly listing of all provisioned machines
    '''
    for instance in orchlib.aws.list_instances():
        print("{:21} {:21} {:16} {}".format(
            instance['InstanceId'],
            instance['Tags']['Name'],
            instance['PublicIpAddress'],
            instance['Tags'].get("use", "")
        ))


@task
def provision(c, machine_name):
    '''
    Set up a baseline image with all the packages needed for
    Learning Observer. Note that this will **not** configure
    the machine.
    '''
    print("Provisioning...")
    machine_info = orchlib.aws.create_instance(machine_name)
    print("Updating...")
    ip = machine_info.public_ip_address
    print("DNS....")
    orchlib.aws.register_dns(machine_name, "learning-observer.org", ip)
    print("IP", ip)
    orchlib.ubuntu.update(ip)
    print("Baseline...")
    orchlib.ubuntu.baseline_packages(ip)
    print("Venv...")
    orchlib.ubuntu.python_venv(ip)


@task
def update(c):
    '''
    Update all machines with the latest systems updates and security
    patches
    '''
    addresses = [i['PublicIpAddress'] for i in orchlib.aws.list_instances()]
    orchlib.ubuntu.run_script("update")(" ".join(addresses))


@task
def terminate(c, machine_name):
    '''
    Shut down a machine.
    '''
    a = input("Are you sure? ")
    if a.strip().lower() not in ['y', 'yes']:
        sys.exit(-1)
    orchlib.aws.terminate_instances(machine_name)


@task
def connect(c, machine_name):
    '''
    `ssh` to a machine
    '''
    os.system("ssh -i {key} ubuntu@{machine_name}".format(
        key=orchlib.config.creds['key_filename'],
        machine_name = machine_name+".learning-observer.org"
    ))


@task
def configure(c, machine_name):
    '''
    Configure a machine
    '''
    group = orchlib.aws.name_to_group(machine_name)

    # In most cases, these would correspond to static sites, or
    # Learning Observer modules
    print("Grabbing git packages")
    for package in orchlib.config.config_lines(machine_name, "-git"):
        group.run("git clone {package}".format(
            package=package
        ))

    print("Installing Python packages")
    for package in orchlib.config.config_lines(machine_name, "-pip"):
        group.run("source ~/.profile; pip install {package}".format(
            package=package
        ))

    template_config = {
        "nginx_root_options": "",
        "hostname": machine_name
    }

    print("Uploading files")
    for [local_file, owner, perms, remote_file, description] in csv.reader(open("config/uploads.csv")):
        print("Uploading: ", description)
        orchlib.templates.upload(
            group=group,
            machine_name=machine_name,
            filename=local_file,
            remote_filename=remote_file.format(**template_config),
            config=template_config,
            username=owner,
            permissions=perms
        )

    for command in open("config/postuploads").readlines():
        group.run(command.format(**template_config).strip())
    

@task
def certbot(c, machine_name):
    '''
    This sets up SSL. Note that:
    - SSL will generally NOT work until everything else is set up
    - This change nginx config. You don't want to override config
      files later.
    - This is untested :)
    '''
    group = orchlib.aws.name_to_group(machine_name)
    group.run("sudo certbot -n --nginx --agree-tos --email {email}".format(
        email=config.creds['email']
    ))
