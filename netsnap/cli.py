import click
import os
import sys
from netsnap.inventory_parser import parse_inventory
from netsnap.testbed_generator import generate_testbed
from netsnap.snapshot_collector import capture_snapshot
from netsnap.comparator import compare_snapshots
from netsnap.reporter import generate_console_report

@click.group()
def cli():
    """Netsnap: Network Snapshot & Validation Tool"""
    pass

@cli.command()
@click.option('--inventory', required=True, help='Path to inventory file (CSV/XLS)')
@click.option('--output', default='testbed.yaml', help='Output testbed file path')
def init(inventory, output):
    """Initialize testbed from inventory"""
    try:
        data = parse_inventory(inventory)
        generate_testbed(data, output)
        click.echo(f"Successfully generated testbed: {output}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--testbed', required=True, help='Path to pyATS testbed file')
@click.option('--name', required=True, help='Snapshot name')
@click.option('--output-dir', default='snapshots', help='Directory to save snapshots')
def capture(testbed, name, output_dir):
    """Capture a new network snapshot"""
    try:
        click.echo(f"Starting snapshot capture '{name}'...")
        snapshot_path = capture_snapshot(testbed, name, output_dir)
        click.echo(f"Snapshot saved to: {snapshot_path}")
    except Exception as e:
        click.echo(f"Error capturing snapshot: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--baseline', required=True, help='Path to baseline snapshot directory')
@click.option('--current', required=True, help='Path to current snapshot directory')
def diff(baseline, current):
    """Compare two snapshots"""
    try:
        compare_data = compare_snapshots(baseline, current)
        generate_console_report(compare_data)
    except Exception as e:
        click.echo(f"Error comparing snapshots: {e}", err=True)
        sys.exit(1)
        
@cli.command()
@click.option('--testbed', required=True, help='Path to pyATS testbed file')
@click.option('--baseline', required=True, help='Path to baseline snapshot directory')
def validate(testbed, baseline):
    """Validate current state against baseline (Capture + Diff)"""
    # This would involve taking a temporary snapshot and comparing it
    # For now, let's just stick to the requested commands structure 
    # capturing to a temp dir or just a new timestamped one and comparing.
    
    import shutil
    
    try:
        current_name = f"validation_run"
        click.echo("Capturing current state for validation...")
        current_path = capture_snapshot(testbed, current_name)
        
        click.echo(f"Comparing against baseline: {baseline}")
        compare_data = compare_snapshots(baseline, current_path)
        generate_console_report(compare_data)
        
    except Exception as e:
        click.echo(f"Error during validation: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()
