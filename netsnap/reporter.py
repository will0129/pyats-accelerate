import json
from tabulate import tabulate

def generate_console_report(diff_report):
    """
    Generates a console report from the diff report.
    """
    print("\n=== Validation Report ===")
    print(f"Baseline: {diff_report['baseline']}")
    print(f"Current:  {diff_report['current']}")
    
    deviations = diff_report.get('deviations', {})
    if not deviations:
        print("\nNo deviations found. System is compliant with baseline.")
        return
        
    print(f"\nDeviations Found: {len(deviations)} devices affected\n")
    
    for device, changes in deviations.items():
        if 'error' in changes:
            print(f"[ERROR] {device}: {changes['error']}")
            continue
            
        print(f"[DEVICE] {device}")
        
        if 'interfaces' in changes:
            table_data = []
            for item in changes['interfaces']:
                table_data.append([item['interface'], item['change'], item.get('from', 'N/A'), item.get('to', 'N/A')])
                
            print(tabulate(table_data, headers=['Interface', 'Change', 'From', 'To'], tablefmt="simple"))
        print("-" * 40)
