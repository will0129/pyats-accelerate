import yaml
import os

def generate_testbed(inventory_data, output_path=None):
    """
    Generates a pyATS testbed YAML from inventory data.
    
    Args:
        inventory_data (list): List of device dictionaries.
        output_path (str, optional): Path to save the YAML file.
        
    Returns:
        dict: The testbed dictionary.
    """
    testbed = {
        'devices': {}
    }
    
    for device in inventory_data:
        hostname = device['hostname']
        # Determine OS based on role or default (user can enhance this mapping)
        # For now, defaulting to iosxe for 'router'/'switch' if not specified, 
        # or we could require 'os' in inventory. PRD implies minimal columns.
        # We'll map role to likely OS or generic.
        dev_role = device['role']
        dev_os = 'iosxe' # Default
        if 'nxos' in dev_role:
            dev_os = 'nxos'
        elif 'asa' in dev_role or 'firewall' in dev_role:
             dev_os = 'asa'
             
        testbed['devices'][hostname] = {
            'type': dev_role,
            'os': dev_os,
            'connections': {
                'cli': {
                    'protocol': 'ssh',
                    'ip': device['ip']
                }
            },
            'credentials': {
                'default': {
                    'username': '%ENV{NETWORK_USER}',
                    'password': '%ENV{NETWORK_PASS}'
                }
            }
        }
        
    if output_path:
        with open(output_path, 'w') as f:
            yaml.dump(testbed, f, default_flow_style=False)
            
    return testbed
