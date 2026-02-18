import pandas as pd
import os

def parse_inventory(file_path):
    """
    Parses device inventory from CSV or Excel file.
    
    Args:
        file_path (str): Path to the inventory file.
        
    Returns:
        list: List of dictionaries containing device info.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Inventory file not found: {file_path}")
        
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please use CSV or Excel.")
        
    # Validate required columns
    required_columns = ['hostname', 'ip', 'role']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
    # Normalize data
    devices = []
    seen_ips = set()
    
    for _, row in df.iterrows():
        # Skip empty rows or rows with missing critical data
        if pd.isna(row['hostname']) or pd.isna(row['ip']):
            continue
            
        device = {
            'hostname': str(row['hostname']).strip(),
            'ip': str(row['ip']).strip(),
            'role': str(row['role']).strip().lower() if not pd.isna(row['role']) else 'unknown'
        }
        
        # Check for duplicate IPs (warning level, but we'll print to console for now or just log)
        if device['ip'] in seen_ips:
            print(f"Warning: Duplicate IP address found: {device['ip']}")
        seen_ips.add(device['ip'])
        
        devices.append(device)
        
    return devices
