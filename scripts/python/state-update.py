#!/usr/bin/env python3
"""
State Update Script
-------------------
Replaces bash+yq approach with Python for atomic, safe YAML updates.

This script provides a reliable alternative to yq v3/v4 syntax issues by using PyYAML
for parsing, modifying, and writing YAML files atomically.

Usage:
    python3 state-update.py --file <yaml_file> --operation <op> [options]

Operations:
    set-value       Set a nested key to a value
    append-item     Append item to an array
    ensure-array    Ensure a key exists as an empty array
    log-violation   Add a violation entry
    set-multiple    Set multiple keys at once (JSON input)

Examples:
    # Set a simple value
    python3 state-update.py --file state.yaml --operation set-value --key current_phase --value ideate

    # Set a nested value
    python3 state-update.py --file state.yaml --operation set-value --key artifacts.ideas_backlog --value path/to/file.md

    # Append to array
    python3 state-update.py --file state.yaml --operation append-item --key phases_completed --value ideate

    # Ensure array exists
    python3 state-update.py --file state.yaml --operation ensure-array --key violations

    # Log a violation
    python3 state-update.py --file state.yaml --operation log-violation \\
        --violation-phase ideate --violation-principle P1 \\
        --violation-message "Test" --violation-severity high --violation-source validator

    # Set multiple values at once
    python3 state-update.py --file state.yaml --operation set-multiple \\
        --json-data '{"current_phase": "select", "artifacts.idea_selection": "path/to/selection.md"}'
"""

import sys
import argparse
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
import json


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load YAML file safely."""
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if data is None:
        data = {}
    
    return data


def save_yaml(file_path: Path, data: Dict[str, Any]) -> None:
    """Save YAML file atomically using temporary file."""
    temp_file = file_path.parent / f".{file_path.name}.tmp"
    
    try:
        # Write to temporary file first
        with open(temp_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        # Atomic move (replace for cross-platform compatibility)
        temp_file.replace(file_path)
    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise e


def get_nested_value(data: Dict[str, Any], key_path: str) -> Any:
    """Get value from nested dictionary using dot notation."""
    if not key_path:
        raise ValueError("Key path cannot be empty")
    
    keys = key_path.split('.')
    value = data
    
    for key in keys:
        if not key:  # Handle consecutive dots or leading/trailing dots
            raise ValueError(f"Invalid key path: {key_path} (contains empty key)")
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return None
        else:
            return None
    
    return value


def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> None:
    """Set value in nested dictionary using dot notation."""
    if not key_path:
        raise ValueError("Key path cannot be empty")
    
    keys = key_path.split('.')
    
    # Validate no empty keys
    for key in keys:
        if not key:
            raise ValueError(f"Invalid key path: {key_path} (contains empty key)")
    
    current = data
    
    # Navigate to the parent of the target key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            # If intermediate key exists but isn't a dict, we can't navigate further
            raise ValueError(f"Cannot set nested key: {key} is not a dictionary")
        current = current[key]
    
    # Set the final key
    current[keys[-1]] = value


def ensure_array(data: Dict[str, Any], key_path: str) -> None:
    """Ensure a key exists and is initialized as an empty array if not present."""
    value = get_nested_value(data, key_path)
    if value is None:
        set_nested_value(data, key_path, [])
    elif not isinstance(value, list):
        raise ValueError(f"Key {key_path} exists but is not an array")


def append_to_array(data: Dict[str, Any], key_path: str, item: Any) -> None:
    """Append an item to an array at the specified key path."""
    ensure_array(data, key_path)
    value = get_nested_value(data, key_path)
    if isinstance(value, list):
        value.append(item)
    else:
        raise ValueError(f"Key {key_path} is not an array")


def parse_value(value_str: str) -> Any:
    """Parse a string value into appropriate Python type."""
    # Try to parse as JSON first (for arrays, objects, booleans, numbers, null)
    try:
        return json.loads(value_str)
    except (json.JSONDecodeError, TypeError):
        # If not valid JSON, treat as string
        return value_str


def operation_set_value(data: Dict[str, Any], args: argparse.Namespace) -> None:
    """Set a single key to a value."""
    if not args.key or args.value is None:
        raise ValueError("--key and --value required for set-value operation")
    
    value = parse_value(args.value)
    set_nested_value(data, args.key, value)


def operation_append_item(data: Dict[str, Any], args: argparse.Namespace) -> None:
    """Append an item to an array."""
    if not args.key or args.value is None:
        raise ValueError("--key and --value required for append-item operation")
    
    value = parse_value(args.value)
    append_to_array(data, args.key, value)


def operation_ensure_array(data: Dict[str, Any], args: argparse.Namespace) -> None:
    """Ensure a key exists as an array."""
    if not args.key:
        raise ValueError("--key required for ensure-array operation")
    
    ensure_array(data, args.key)


def operation_log_violation(data: Dict[str, Any], args: argparse.Namespace) -> None:
    """Log a violation entry."""
    required = ['violation_phase', 'violation_principle', 'violation_message']
    if not all(getattr(args, attr, None) for attr in required):
        raise ValueError("--violation-phase, --violation-principle, and --violation-message required")
    
    # Ensure violations array exists
    ensure_array(data, 'violations')
    
    # Create violation entry
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    violation = {
        'timestamp': timestamp,
        'phase': args.violation_phase,
        'principle': args.violation_principle,
        'message': args.violation_message,
        'severity': args.violation_severity or 'high',
        'source': args.violation_source or 'validator'
    }
    
    append_to_array(data, 'violations', violation)


def operation_set_multiple(data: Dict[str, Any], args: argparse.Namespace) -> None:
    """Set multiple key-value pairs from JSON input."""
    if not args.json_data:
        raise ValueError("--json-data required for set-multiple operation")
    
    try:
        updates = json.loads(args.json_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}")
    
    if not isinstance(updates, dict):
        raise ValueError("JSON data must be an object/dictionary")
    
    for key, value in updates.items():
        set_nested_value(data, key, value)


def main():
    parser = argparse.ArgumentParser(
        description="Atomic YAML state file updates using Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--file', required=True, type=Path,
                        help='Path to YAML file to update')
    parser.add_argument('--operation', required=True,
                        choices=['set-value', 'append-item', 'ensure-array', 'log-violation', 'set-multiple'],
                        help='Operation to perform')
    
    # Common arguments
    parser.add_argument('--key', help='Key path (dot notation for nested keys)')
    parser.add_argument('--value', help='Value to set/append')
    
    # For log-violation operation
    parser.add_argument('--violation-phase', help='Phase for violation entry')
    parser.add_argument('--violation-principle', help='Principle for violation entry')
    parser.add_argument('--violation-message', help='Message for violation entry')
    parser.add_argument('--violation-severity', default='high', help='Severity for violation entry')
    parser.add_argument('--violation-source', default='validator', help='Source for violation entry')
    
    # For set-multiple operation
    parser.add_argument('--json-data', help='JSON object with key-value pairs to set')
    
    args = parser.parse_args()
    
    try:
        # Load current state
        data = load_yaml(args.file)
        
        # Perform operation
        operation_handlers = {
            'set-value': operation_set_value,
            'append-item': operation_append_item,
            'ensure-array': operation_ensure_array,
            'log-violation': operation_log_violation,
            'set-multiple': operation_set_multiple
        }
        
        handler = operation_handlers[args.operation]
        handler(data, args)
        
        # Save atomically
        save_yaml(args.file, data)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
