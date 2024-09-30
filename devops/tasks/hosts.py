import orchlib.aws
import orchlib.config
import orchlib.fabric_flock
import orchlib.templates
import orchlib.ubuntu
import orchlib.repos
from orchlib.logger import system

def update_hosts_ini():
    # Fetch list of instances
    instances = orchlib.aws.list_instances()
    ###print(f"Debug: instances contains: {instances}")
        
    # Open or create the hosts.ini file
    with open('hosts.ini', 'w') as hosts_file:
        # Write a default header or group for the ansible inventory
        hosts_file.write('[aws_servers]\n')
        
        key_file =  orchlib.config.creds['key_filename']
         
        # Iterate through the instances and write their details
        for instance in instances:
            ## print(f"Debug: instance contains: {instance}")
            
            instance_name = instance['Tags']['Name']
            ip_address = instance['PublicIpAddress']
            hosts_file.write(f"{instance_name} ansible_host={ip_address} ansible_user=ubuntu ansible_ssh_private_key_file={key_file}\n")

# Call the function to update the hosts.ini file
update_hosts_ini()