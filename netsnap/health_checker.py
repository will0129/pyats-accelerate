import logging

logger = logging.getLogger(__name__)

def check_health(snapshot_data):
    """
    Analyzes a single device snapshot and returns standardized health metrics.
    
    Args:
        snapshot_data (dict): The raw JSON snapshot for a device.
        
    Returns:
        dict: Normalized health indicators.
    """
    health_report = {
        'hostname': snapshot_data.get('hostname'),
        'interfaces_up': 0,
        'interfaces_down': 0,
        'cpu_load_5min': 0, # Normalized 0-100
        'memory_usage_percent': 0
    }
    
    # Interfaces
    interfaces = snapshot_data.get('interfaces', {})
    for intf, details in interfaces.items():
        if details.get('oper_status') == 'up':
            health_report['interfaces_up'] += 1
        elif details.get('oper_status') == 'down':
             # Check if administratively down?
             if details.get('enabled') is False or 'administratively down' in details.get('line_protocol', ''):
                 pass # Ignore admin down? PRD says exclude admin down
             else:
                health_report['interfaces_down'] += 1
                
    # CPU
    cpu_data = snapshot_data.get('cpu', {}).get('five_min_cpu') # IOS-XE specific structure usually
    if cpu_data:
        health_report['cpu_load_5min'] = cpu_data
        
    return health_report
