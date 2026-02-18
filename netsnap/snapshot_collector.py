import logging
from genie.testbed import load
from pyats.topology import Testbed
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

def capture_snapshot(testbed_path, snapshot_name, output_dir='snapshots'):
    """
    Captures a snapshot of the network state.
    
    Args:
        testbed_path (str): Path to the testbed YAML file.
        snapshot_name (str): Name of the snapshot.
        output_dir (str): Directory to save snapshots.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = os.path.join(output_dir, f"{snapshot_name}_{timestamp}")
    os.makedirs(snapshot_dir)
    
    testbed = load(testbed_path)
    
    metadata = {
        'snapshot_id': f"{snapshot_name}_{timestamp}",
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'device_count': len(testbed.devices),
        'status': 'in_progress',
        'devices': list(testbed.devices.keys())
    }
    
    # Save initial metadata
    with open(os.path.join(snapshot_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
        
    for name, device in testbed.devices.items():
        logger.info(f"Connecting to {name}...")
        try:
            device.connect(log_stdout=False)
            
            # 1. Interface Health
            logger.info(f"Collecting interface operational state for {name}...")
            interfaces = device.parse('show interfaces')
            
            # 2. Device Health
            # Note: These commands are IOS-XE specific in the example. 
            # Ideally we'd use platform-agnostic Genie parsers or check OS.
            logger.info(f"Collecting CPU usage for {name}...")
            cpu = {}
            if device.os in ['iosxe', 'ios']:
                cpu = device.parse('show processes cpu')
            # Add more OS checks or use generic if available
            
            logger.info(f"Collecting memory usage for {name}...")
            memory = {}
            if device.os in ['iosxe', 'ios']:
                memory = device.parse('show processes memory') # simplified command
            
            # Combine into device snapshot
            device_snapshot = {
                'hostname': name,
                'interfaces': interfaces,
                'cpu': cpu,
                'memory': memory
            }
            
            # Save device snapshot
            with open(os.path.join(snapshot_dir, f"{name}.json"), 'w') as f:
                json.dump(device_snapshot, f, indent=2)
                
            device.disconnect()
            
        except Exception as e:
            logger.error(f"Failed to capture snapshot for {name}: {e}")
            device_snapshot = {
                'hostname': name,
                'error': str(e)
            }
            with open(os.path.join(snapshot_dir, f"{name}_error.json"), 'w') as f:
                json.dump(device_snapshot, f, indent=2)

    metadata['status'] = 'completed'
    with open(os.path.join(snapshot_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
        
    return snapshot_dir
