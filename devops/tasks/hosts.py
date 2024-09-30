import orchlib.aws

def update_hosts_ini():
    # Fetch list of instances
    instances = orchlib.aws.list_instances()
    
    # Open or create the hosts.ini file
    with open('hosts.ini', 'w') as hosts_file:
        # Write a default header or group for the ansible inventory
        hosts_file.write('[aws_servers]\n')
        
        # Iterate through the instances and write their IP addresses
        for instance in instances:
            # Assuming the instance object has an attribute 'ip_address'
            hosts_file.write(f"{instance.ip_address}\n")

# Call the function to update the hosts.ini file
update_hosts_ini()