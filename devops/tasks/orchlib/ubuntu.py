'''
These are scripts for preparing an Ubuntu 20.04 machine to run the
Learning Observer
'''

import orchlib.fabric_flock
import orchlib.config

ssh_pool = None


def run_script(scriptfile):
    '''
    
    '''
    global ssh_pool
    if ssh_pool is None:
        ssh_pool = orchlib.fabric_flock.machine_pool()
    script = open("scripts/{fn}.fab".format(fn=scriptfile)).read()
    def run(pool = ssh_pool):
        group = orchlib.fabric_flock.group_from_poolstring(pool)

        for line in ['hostname'] + script.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != "#":
                print(line)
                group.run(line)
    return run

update = run_script("update")
baseline_packages = run_script("baseline_packages")
python_venv = run_script("python_venv")


def reboot():
    '''
    Run the reboot script. We expect an exception since the remote machine
    reboots while Fabric is connected.
    '''
    try:
        run_script(REBOOT)
    except fabric.exceptions.GroupException:
        pass

def provision(ip):
    group = fabric.SerialGroup(
        ip,
        user=creds['user'],
        connect_kwargs={"key_filename": creds['key_filename']}
    )
    update()
    baseline_packages()
    python_venv()
    reboot()

if __name__=='__main__':
    provision()
