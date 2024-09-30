#!/usr/bin/env python3
import json
import orchlib.aws
import orchlib.config

def get_inventory():
    # Fetch list of instances
    instances = orchlib.aws.list_instances()
    
    # Initialize inventory structure
    inventory = {
        'servers': {
            'hosts': [],
            'vars': {
                'ansible_user': 'ubuntu',
                'ansible_ssh_private_key_file': orchlib.config.creds['key_filename']
            }
        },
        '_meta': {
            'hostvars': {}
        }
    }
    
    # Iterate through the instances and add them to the inventory
    for instance in instances:
        instance_name = instance['Tags']['Name']
        ip_address = instance['PublicIpAddress']
        
        # Add instance to the aws_servers group
        inventory['aws_servers']['hosts'].append(instance_name)
        
        # Add host-specific variables
        inventory['_meta']['hostvars'][instance_name] = {
            'ansible_host': ip_address
        }
    
    return inventory

if __name__ == '__main__':
    inventory = get_inventory()
    print(json.dumps(inventory, indent=2))