This is a set of ansible playbooks to setup a new server, currently reliant on the python tasks to assist in the server creation.

To setup a new server, do the following:

  cd ../tasks
  sudo inv initialize [machine]
  ansible-playbook -i hosts.ini ../ansible/tasks/A_setup_flock.yaml --extra-vars "target_server=[machine]"
  ansible-playbook -i hosts.ini ../ansible/tasks/B_install_baseline.yaml --limit [machine]
  ansible-playbook -i hosts.ini ../ansible/tasks/C_install_repos.yaml --limit [machine]
  ansible-playbook -i hosts.ini ../ansible/tasks/D_copy_files.yaml --limit [machine]
  ansible-playbook -i hosts.ini ../ansible/tasks/E_setup_os_environment_variables.yaml --limit [machine]
  ansible-playbook -i hosts.ini ../ansible/tasks/F_run_additional_tasks.yaml --limit [machine]

  ansible-playbook -i hosts.ini ./tasks/reboot.yaml --limit [machine]
  inv  inv certbot [machine]
  ansible-playbook -i hosts.ini ./tasks/reboot.yaml --limit [machine]
  
  ansible-playbook -i hosts.ini ../ansible/tasks/G_download_config.yaml --limit [machine]
  
  TO DO: replace the hosts.ini with a python script that returns inv list output in correct format

  Example for daclassroom:

  sudo inv initialize daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/A_setup_flock.yaml --extra-vars "target_server=daclassroom"
  <at this point, we can modify the yaml & files in the flock-project/daclassroom/yaml>
  ansible-playbook -i hosts.ini ../ansible/tasks/B_install_baseline.yaml --limit daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/C_install_repos.yaml --limit daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/D_copy_files.yaml --limit daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/E_setup_os_environment_variables.yaml --limit daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/F_run_additional_tasks.yaml --limit daclassroom
  inv certbot daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/reboot.yaml --limit daclassroom

  alternately, we can just use the master playbook to run steps B-F in one go:
  sudo inv initialize daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/A_setup_flock.yaml --extra-vars "target_server=daclassroom"
  <at this point, we can modify the yaml & files in the flock-project/daclassroom/yaml>
  ansible-playbook -i hosts.ini ../ansible/tasks/master_playbook.yaml --limit daclassroom
  inv certbot daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/reboot.yaml --limit daclassroom
  ansible-playbook -i hosts.ini ../ansible/tasks/G_download_config.yaml --limit daclassroom

  The hosts.ini file can be created by running python hosts.py in the tasks directory.
  To remove the hosts.ini file completely, you can call the dynamic_hosts.py script. First make sure the script is executable:
  chmod +x ./dynamic_hosts.py

  Make sure you're logged into aws by running:
  aws sso login

  Then call a playbook usign the dyanmic_hosts.py script like this:
  
  ansible-playbook -i dynamic_hosts.py ../ansible/tasks/B_install_baseline.yaml --limit coglabs
  ansible-playbook -i dynamic_hosts.py ../ansible/tasks/C_install_repos.yaml --limit coglabs
  ansible-playbook -i dynamic_hosts.py ../ansible/tasks/D_copy_files.yaml --limit coglabs
  ansible-playbook -i dynamic_hosts.py ../ansible/tasks/E_setup_os_environment_variables.yaml --limit coglabs
  ansible-playbook -i dynamic_hosts.py ../ansible/tasks/F_run_additional_tasks.yaml --limit coglabs
  inv certbot daclassroom
  ansible-playbook -i dynamic_hosts.py ../ansible/tasks/reboot.yaml --limit coglabs
  ansible-playbook -i dynamic_hosts.py ../ansible/tasks/G_download_config.yaml --limit coglabs
  
