from deepdiff import DeepDiff
import json
import os

def compare_snapshots(baseline_dir, current_dir):
    """
    Compares two snapshot directories.
    
    Args:
        baseline_dir (str): Path to baseline snapshot directory.
        current_dir (str): Path to current snapshot directory.
        
    Returns:
        dict: Differences report.
    """
    report = {
        'baseline': baseline_dir,
        'current': current_dir,
        'deviations': {}
    }
    
    # Load metadata to get device list? Or just iterate files.
    # We'll iterate files in baseline and check against current.
    
    baseline_files = [f for f in os.listdir(baseline_dir) if f.endswith('.json') and f != 'metadata.json']
    
    for filename in baseline_files:
        device_name = filename.replace('.json', '')
        
        base_path = os.path.join(baseline_dir, filename)
        curr_path = os.path.join(current_dir, filename)
        
        if not os.path.exists(curr_path):
            report['deviations'][device_name] = {'error': 'Device missing in current snapshot'}
            continue
            
        with open(base_path, 'r') as f:
            base_data = json.load(f)
        with open(curr_path, 'r') as f:
            curr_data = json.load(f)
            
        # Compare Interfaces
        # We focus on op_status changes as per PRD
        base_intf = base_data.get('interfaces', {})
        curr_intf = curr_data.get('interfaces', {})
        
        intf_diffs = []
        
        # Check for state changes
        for intf, details in base_intf.items():
            if intf not in curr_intf:
                intf_diffs.append({'interface': intf, 'change': 'Interface missing'})
                continue
                
            base_state = details.get('oper_status')
            curr_state = curr_intf[intf].get('oper_status')
            
            if base_state != curr_state:
                intf_diffs.append({
                    'interface': intf, 
                    'change': 'oper_status', 
                    'from': base_state, 
                    'to': curr_state
                })
                
        if intf_diffs:
            if device_name not in report['deviations']:
                report['deviations'][device_name] = {}
            report['deviations'][device_name]['interfaces'] = intf_diffs
            
    return report
