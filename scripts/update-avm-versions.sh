#!/usr/bin/env bash
#
# Update AVM Module Versions - Bash Wrapper
#
# This is a wrapper script that calls the Python implementation.
# The Python version is more robust and easier to maintain.
#
# Usage:
#   ./scripts/update-avm-versions.sh [--update] [--yaml-file PATH]
#
# Options:
#   --update        Update the YAML file with latest versions
#   --yaml-file     Path to avm-modules.yaml (default: agents/azure-fsi-landingzone/avm-modules.yaml)
#   --help          Show this help message
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/update-avm-versions.py"

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found: $PYTHON_SCRIPT" >&2
    exit 1
fi

# Pass all arguments to the Python script
# Use uv if available, otherwise fall back to python3
if command -v uv &> /dev/null; then
    exec uv run python "$PYTHON_SCRIPT" "$@"
else
    exec python3 "$PYTHON_SCRIPT" "$@"
fi
