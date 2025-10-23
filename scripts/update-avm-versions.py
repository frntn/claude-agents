#!/usr/bin/env python3
"""
Update AVM Module Versions

This script retrieves the latest version for each Azure Verified Module (AVM)
listed in avm-modules.yaml by querying the Microsoft Container Registry API.

Usage:
    python scripts/update-avm-versions.py [--update] [--yaml-file PATH]

Options:
    --update        Update the YAML file with latest versions
    --yaml-file     Path to avm-modules.yaml (default: agents/azure-fsi-landingzone/avm-modules.yaml)
    --help          Show this help message
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError

import yaml


# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def get_latest_version(registry_path: str) -> Optional[str]:
    """
    Query MCR API to get the latest semantic version for a module.

    Args:
        registry_path: Module registry path (e.g., "br/public:avm/res/network/virtual-network")

    Returns:
        Latest semantic version string or None if error
    """
    # Convert registry path to MCR API URL
    # Example: br/public:avm/res/network/virtual-network -> avm/res/network/virtual-network
    module_path = registry_path.replace("br/public:", "")
    api_url = f"https://mcr.microsoft.com/v2/bicep/{module_path}/tags/list"

    try:
        with urlopen(api_url, timeout=10) as response:
            data = json.loads(response.read().decode())
            tags = data.get("tags", [])

            # Filter for semantic versions (X.Y.Z)
            semver_pattern = re.compile(r'^\d+\.\d+\.\d+$')
            versions = [tag for tag in tags if semver_pattern.match(tag)]

            if not versions:
                return None

            # Sort versions and return latest
            def version_key(v):
                return tuple(map(int, v.split('.')))

            return sorted(versions, key=version_key)[-1]

    except (URLError, json.JSONDecodeError, KeyError) as e:
        print(f"{Colors.RED}Error querying {api_url}: {e}{Colors.NC}", file=sys.stderr)
        return None


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two semantic versions.

    Returns:
        1 if v1 > v2, -1 if v1 < v2, 0 if equal
    """
    def version_tuple(v):
        return tuple(map(int, v.split('.')))

    t1, t2 = version_tuple(v1), version_tuple(v2)
    if t1 > t2:
        return 1
    elif t1 < t2:
        return -1
    return 0


def check_versions(yaml_file: Path) -> Tuple[Dict[str, str], Dict[str, Dict]]:
    """
    Check all module versions in the YAML file.

    Args:
        yaml_file: Path to avm-modules.yaml

    Returns:
        Tuple of (updates dict, stats dict)
    """
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    modules = data.get('modules', {})
    updates = {}
    stats = {
        'total': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
        'up_to_date': 0
    }

    print(f"{Colors.BLUE}Checking AVM module versions...{Colors.NC}\n")

    for module_key, module_data in modules.items():
        registry = module_data.get('registry')
        current_version = module_data.get('version')
        status = module_data.get('status')

        # Skip modules without registry (native, planned, etc.)
        if not registry:
            print(f"{Colors.YELLOW}⊘ {module_key}: Skipped (no registry path){Colors.NC}")
            stats['skipped'] += 1
            continue

        stats['total'] += 1
        print(f"Checking {module_key}... ", end='', flush=True)

        # Get latest version from MCR
        latest_version = get_latest_version(registry)

        if latest_version is None:
            print(f"{Colors.RED}✗ Failed to retrieve version{Colors.NC}")
            stats['errors'] += 1
            continue

        # Compare versions
        if not current_version:
            print(f"{Colors.YELLOW}⊕ {latest_version} (no current version){Colors.NC}")
            updates[module_key] = latest_version
            stats['updated'] += 1
        elif compare_versions(latest_version, current_version) > 0:
            print(f"{Colors.GREEN}↑ {current_version} → {latest_version}{Colors.NC}")
            updates[module_key] = latest_version
            stats['updated'] += 1
        else:
            print(f"{Colors.GREEN}✓ {current_version} (up to date){Colors.NC}")
            stats['up_to_date'] += 1

    return updates, stats


def update_yaml_file(yaml_file: Path, updates: Dict[str, str]) -> None:
    """
    Update the YAML file with new versions.

    Args:
        yaml_file: Path to avm-modules.yaml
        updates: Dictionary of module_key -> new_version
    """
    # Create backup
    backup_file = yaml_file.with_suffix(f'.yaml.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    backup_file.write_text(yaml_file.read_text())
    print(f"Backup created: {backup_file}")

    # Load YAML
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # Update versions
    for module_key, new_version in updates.items():
        if module_key in data.get('modules', {}):
            data['modules'][module_key]['version'] = new_version
            print(f"  {Colors.GREEN}✓{Colors.NC} Updated {module_key} to {new_version}")

    # Update metadata generation date
    if 'metadata' in data:
        data['metadata']['generated'] = datetime.now().strftime("%Y-%m-%d")

    # Write back to file
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\n{Colors.GREEN}YAML file updated successfully!{Colors.NC}")


def main():
    parser = argparse.ArgumentParser(
        description="Update AVM module versions from Microsoft Container Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update the YAML file with latest versions'
    )
    parser.add_argument(
        '--yaml-file',
        type=Path,
        default=Path(__file__).parent.parent / 'agents' / 'azure-fsi-landingzone' / 'avm-modules.yaml',
        help='Path to avm-modules.yaml'
    )

    args = parser.parse_args()

    # Check if YAML file exists
    if not args.yaml_file.exists():
        print(f"{Colors.RED}Error: YAML file not found: {args.yaml_file}{Colors.NC}", file=sys.stderr)
        sys.exit(1)

    # Check versions
    updates, stats = check_versions(args.yaml_file)

    # Print summary
    print(f"\n{Colors.BLUE}Summary:{Colors.NC}")
    print(f"  Total modules checked: {stats['total']}")
    print(f"  Updates available: {stats['updated']}")
    print(f"  Up to date: {stats['up_to_date']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")

    # Update file if requested
    if args.update and updates:
        print(f"\n{Colors.YELLOW}Updating {args.yaml_file}...{Colors.NC}")
        update_yaml_file(args.yaml_file, updates)
    elif args.update:
        print(f"\n{Colors.GREEN}No updates needed - all modules are up to date!{Colors.NC}")
    elif updates:
        print(f"\n{Colors.YELLOW}Run with --update flag to apply these changes{Colors.NC}")


if __name__ == '__main__':
    main()
