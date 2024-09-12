'''
These are scripts for preparing an Ubuntu 20.04 machine to run the
Learning Observer
'''

import fabric.exceptions

import orchlib.fabric_flock
import orchlib.config
import tempfile
import os

def run_script(scriptfile):
    '''
    Helper which executes a series of commands on set of machines
    '''
    print("------------------------------------------")
    
    # Read the script file
    script_path = "scripts/{fn}.fab".format(fn=scriptfile)
    print("Running script: ", script_path)
    try:
        with open(script_path, 'r') as file:
            script = file.read()
    except FileNotFoundError:
        print(f"Script file not found: {script_path}")
        return
    except Exception as e:
        print(f"Error reading script file: {e}")
        return

    def run(*machines):
        group = orchlib.fabric_flock.machine_group(*machines)
        i = 0
        for line in ['hostname'] + script.split("\n"):
            line = line.strip()
            i = i + 1
            if len(line) > 0 and line[0] != "#":
                group.run(line)
    print("------------------------------------------")
    return run

update = run_script("update")
baseline_packages = run_script("baseline_packages")
python_venv = run_script("python_venv")

def install_git_repos(ip):
    
    git_username = orchlib.config.creds.get('git_username')
    git_pac = orchlib.config.creds.get('git_pac')
    openai_url = orchlib.config.creds.get('openai_url')
    openai_deployment_id = orchlib.config.creds.get('openai_deployment_id')
    openai_api_key = orchlib.config.creds.get('openai_api_key')

    if not git_username or not git_pac or not openai_url or not openai_deployment_id or not openai_api_key:
        raise ValueError("Git/OpenAI credentials are not available in the config")
    
    # Path to the baseline_packages.fab file
    fab_file_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'git_repos.fab')

    # Read the content of the baseline_packages.fab file
    with open(fab_file_path, 'r') as file:
        content = file.read()

    # Replace placeholders with actual credentials
    content = content.replace('{git_username}', git_username)
    content = content.replace('{git_pac}', git_pac)
    content = content.replace('{openai_url}', openai_url)
    content = content.replace('{openai_deployment_id}', openai_deployment_id)
    content = content.replace('{openai_api_key}', openai_api_key)

    # Write the updated content to a temporary file
    temp_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.fab', dir=temp_dir) as temp_file:
        temp_file.write(content.encode())
        temp_file_path = temp_file.name

    print(f"Running: {temp_file_path}")
    temp_file_name = os.path.basename(temp_file_path)
    temp_file_name = temp_file_name.replace('.fab', '') 

    # Run the resulting script using run_script
    print("Running baseline_packages script: " + temp_file_name)
    
    try:
        run_script(temp_file_name)(ip)
    except Exception as e:
        print(f"An error occurred while running the script: {e}")
        return None
    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)

def reboot(machine):
    '''
    Run the reboot script. We expect an exception since the remote machine
    reboots while Fabric is connected.
    '''
    try:
        print("Trying to reboot (this doesn't always work")
        run_script("reboot")(machine)
    except fabric.exceptions.GroupException:
        pass

def provision(ip):
    group = fabric.SerialGroup(
        ip,
        user=orchlib.config.creds['user'],
        connect_kwargs={"key_filename": orchlib.config.creds['key_filename']}
    )
    update()

    run_baseline_packages()
    ###baseline_packages()
    python_venv()
    reboot()

if __name__=='__main__':
    provision()
