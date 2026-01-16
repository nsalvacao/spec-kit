#!/usr/bin/env python3
"""
Sync Project Fields
-------------------
Reads items from GitHub Project 7 (Spec-kit), checks their labels,
and updates the 'Category' and 'Priority' single-select fields accordingly.

Usage:
    python3 scripts/python/sync_project.py --execute
"""

import json
import subprocess
import argparse
import sys

# --- Configuration ---
PROJECT_NUMBER = 7
PROJECT_ID = "PVT_kwHOCtidn84BMwrw"
OWNER = "nsalvacao"

# Field IDs (from gh project field-list)
FIELD_CATEGORY_ID = "PVTSSF_lAHOCtidn84BMwrwzg7895Y"
FIELD_PRIORITY_ID = "PVTSSF_lAHOCtidn84BMwrwzg7876Y"

# Option IDs (from gh project field-list)
CATEGORY_OPTIONS = {
    "cat:state-management": "2f7e3985",    # CAT-001
    "cat:phase0-integration": "50359eb2",  # CAT-002
    "cat:automation-scripts": "824789a2",  # CAT-003
    "cat:validators": "9f74c12c",          # CAT-004
    "cat:cli-ux": "9e6f4177",              # CAT-005
    "cat:framework-design": "af6540e9",    # CAT-006
    "cat:qa-docs": "b3ccca63"              # CAT-007
}

PRIORITY_OPTIONS = {
    "severity:critical": "2692d975",       # P0
    "severity:high": "f290d668",           # P1
    "severity:medium": "7ab6836c",         # P2
    "severity:low": "7ab6836c"             # P2 (Group Low with Medium/P2)
}

def get_project_items():
    print("Fetching project items...")
    cmd = ["gh", "project", "item-list", str(PROJECT_NUMBER), "--owner", OWNER, "--format", "json", "--limit", "100"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)["items"]

def update_item(item_id, field_id, option_id, dry_run=True):
    if dry_run:
        print(f"  [DRY RUN] Update item {item_id}: Field {field_id} -> Option {option_id}")
        return

    cmd = [
        "gh", "project", "item-edit",
        "--id", item_id,
        "--project-id", PROJECT_ID,
        "--field-id", field_id,
        "--single-select-option-id", option_id
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  [SUCCESS] Updated item {item_id}")
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Failed to update item {item_id}: {e.stderr}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Execute updates")
    args = parser.parse_args()

    items = get_project_items()
    print(f"Found {len(items)} items.")

    for item in items:
        # Extract labels directly from item root
        # JSON format: "labels": ["bug", "cat:state-management", ...]
        labels = item.get("labels", [])
        
        print(f"\nProcessing Item: {item.get('title', 'Unknown')}")
        print(f"  Labels: {labels}")

        # 1. Determine Category
        target_cat_id = None
        for lbl in labels:
            if lbl in CATEGORY_OPTIONS:
                target_cat_id = CATEGORY_OPTIONS[lbl]
                break # First match wins
        
        # 2. Determine Priority
        target_prio_id = None
        for lbl in labels:
            if lbl in PRIORITY_OPTIONS:
                # Simple precedence: Critical (P0) > High (P1) > Medium/Low (P2)
                current_prio_val = PRIORITY_OPTIONS[lbl]
                
                # Logic: Keep the highest priority found
                if target_prio_id is None:
                    target_prio_id = current_prio_val
                else:
                    # P0 ID starts with 26, P1 with f2, P2 with 7a
                    # If we found P0, keep it. If we found P1 and haven't found P0 yet, update.
                    if current_prio_val == "2692d975": 
                        target_prio_id = current_prio_val
                    elif current_prio_val == "f290d668" and target_prio_id != "2692d975":
                        target_prio_id = current_prio_val

        # 3. Apply Updates
        if target_cat_id:
            update_item(item["id"], FIELD_CATEGORY_ID, target_cat_id, not args.execute)
        
        if target_prio_id:
            update_item(item["id"], FIELD_PRIORITY_ID, target_prio_id, not args.execute)

if __name__ == "__main__":
    main()
