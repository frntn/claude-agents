#!/usr/bin/env python3
"""
Test script to generate and validate AVM-based Bicep templates.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import agent module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent import AzureFSILandingZoneAgent

BICEP_BUILD_TIMEOUT = int(os.environ.get("AZURE_BICEP_BUILD_TIMEOUT", "120"))
KEEP_GENERATED_TEMPLATES = os.environ.get("AZURE_BICEP_KEEP_TEMPLATES", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def _cleanup_temp_file(path: str) -> None:
    """Remove temp bicep/json artifacts unless retention requested."""
    json_path = path.replace(".bicep", ".json")
    if KEEP_GENERATED_TEMPLATES:
        print(f"ℹ️  Temporary file retained: {path}")
        if os.path.exists(json_path):
            print(f"ℹ️  Generated JSON retained: {json_path}")
        return

    for p in (path, json_path):
        if os.path.exists(p):
            try:
                os.unlink(p)
            except OSError as exc:
                print(f"⚠️  Unable to delete {p}: {exc}")


def validate_bicep_template(template_content: str, template_name: str) -> bool:
    """Validate a Bicep template using Azure CLI."""
    print(f"\n{'='*80}")
    print(f"Testing: {template_name}")
    print(f"{'='*80}")

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bicep', delete=False) as f:
        f.write(template_content)
        temp_path = f.name

    try:
        # Try to build the template
        result = subprocess.run(
            ['az', 'bicep', 'build', '--file', temp_path],
            capture_output=True,
            text=True,
            timeout=BICEP_BUILD_TIMEOUT
        )

        if result.returncode == 0:
            print(f"✅ {template_name}: Valid Bicep template")
            return True
        else:
            print(f"❌ {template_name}: Bicep validation failed")
            print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(
            f"❌ {template_name}: az bicep build timed out after "
            f"{BICEP_BUILD_TIMEOUT} seconds; set AZURE_BICEP_BUILD_TIMEOUT to override."
        )
        return False
    except Exception as e:
        print(f"❌ {template_name}: Exception during validation: {e}")
        return False
    finally:
        _cleanup_temp_file(temp_path)


def main():
    """Main test function."""
    print("🧪 Testing Azure FSI Landing Zone AVM Templates")
    print("="*80)

    # Initialize agent (synchronously for testing)
    config_dir = Path(__file__).parent
    agent = AzureFSILandingZoneAgent(config_dir)

    # Test templates
    templates = {
        "Hub VNet": agent._generate_hub_vnet_bicep(),
        "Spoke VNet": agent._generate_spoke_vnet_bicep(),
        "Key Vault": agent._generate_keyvault_bicep(),
        "Storage Account": agent._generate_storage_bicep(),
        "Policy Assignment": agent._generate_policy_bicep(),
    }

    results = {}
    for name, template in templates.items():
        results[name] = validate_bicep_template(template, name)

    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} templates valid")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
