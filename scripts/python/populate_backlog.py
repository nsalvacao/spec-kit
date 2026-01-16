#!/usr/bin/env python3
"""
Populate Backlog Script
-----------------------
Parses the structured analysis output (Markdown) and creates GitHub Issues
using the specific templates and taxonomy of the Spec-Kit project.

Usage:
    python3 scripts/python/populate_backlog.py --source .spec-kit-dev-notes/analysis-pipeline-output.md
    python3 scripts/python/populate_backlog.py --source ... --execute
    python3 scripts/python/populate_backlog.py --source ... --category CAT-001 --execute

Features:
- Robust Markdown parsing using state detection
- Maps severity and categories to project labels
- Dry-run mode by default
- Idempotency check (skips existing Pxxx issues to prevent duplicates)
"""

import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

# --- Configuration & Mappings ---

SEVERITY_MAP = {
    "CRITICAL": "severity:critical",
    "HIGH": "severity:high",
    "MEDIUM": "severity:medium",
    "LOW": "severity:low"
}

TYPE_MAP = {
    "BUG": "bug",
    "TECHNICAL_DEBT": "tech-debt",
    "UX_ISSUE": "ux",
    "MISSING_FEATURE": "enhancement",
    "DOCUMENTATION": "documentation",
    "INFRASTRUCTURE": "infrastructure"
}

# Map Analysis Categories (CAT-XXX) to GitHub Labels
CATEGORY_MAP = {
    "CAT-001": "cat:state-management",
    "CAT-002": "cat:phase0-integration",
    "CAT-003": "cat:automation-scripts",
    "CAT-004": "cat:validators",
    "CAT-005": "cat:cli-ux",
    "CAT-006": "cat:framework-design",
    "CAT-007": "cat:qa-docs"
    # Note: CAT-008 was merged into CAT-007 in the report, handling gracefully
}

class IssueData:
    def __init__(self):
        self.p_id: str = ""
        self.title: str = ""
        self.original_type: str = ""
        self.severity: str = ""
        self.quick_win: bool = False
        self.category_id: str = ""
        self.description: List[str] = []
        self.solution: List[str] = []
        self.effort: str = ""
        self.owner: str = ""

    @property
    def labels(self) -> List[str]:
        lbls = []
        # Category Label
        if self.category_id in CATEGORY_MAP:
            lbls.append(CATEGORY_MAP[self.category_id])
        
        # Severity Label
        sev_key = self.severity.upper()
        if sev_key in SEVERITY_MAP:
            lbls.append(SEVERITY_MAP[sev_key])
            
        # Type Label
        type_key = self.original_type.upper()
        if type_key in TYPE_MAP:
            lbls.append(TYPE_MAP[type_key])
            
        # Quick Win
        if self.quick_win:
            lbls.append("quick-win")
            
        return lbls

    def construct_body(self) -> str:
        """
        Constructs a Markdown body mimicking the project's specific YAML Issue Forms.
        Adapts structure based on issue type (Bug, Feature, Tech Debt).
        """
        body = []
        
        # --- Context / Metadata Section ---
        body.append(f"**Origin ID**: `{self.p_id}`")
        body.append(f"**Analysis Category**: {self.category_id}")
        if self.effort:
            body.append(f"**Estimated Effort**: {self.effort}")
        if self.owner:
            body.append(f"**Suggested Owner**: {self.owner}")
        
        # Combine extracted text for analysis
        full_desc_text = "\n".join(self.description)
        
        # --- Type-Specific Formatting ---
        
        if "bug" in self.labels:
            # Template: bug-report.yml
            # Headers: Describe the bug, To Reproduce, Expected behavior, Logs
            
            # Extract 'Desired State'/Expected Behavior if present
            expected = ""
            desc_cleaned = []
            for line in self.description:
                if "**Desired State**" in line or "Desired State" in line:
                    expected = line.replace("**Desired State**", "").replace("Desired State", "").strip()
                    # If it's a header line, maybe the next lines are the content. 
                    # For simplicity in this parser, we assume single line or paragraph context.
                else:
                    desc_cleaned.append(line)
            
            body.append("\n### Describe the bug")
            body.append("\n".join(desc_cleaned).strip())
            
            if expected:
                body.append("\n### Expected behavior")
                body.append(expected)
            else:
                body.append("\n### Expected behavior")
                body.append("*Derived from desired state analysis*")

            body.append("\n### To Reproduce")
            body.append("*Issue identified via static analysis pipeline. See Evidence below.*")

        elif "enhancement" in self.labels or "ux" in self.labels:
            # Template: feature-request.yml
            # Headers: Target Category, Is your feature request related to a problem?, Describe the solution, Business Value
            
            body.append("\n### Is your feature request related to a problem?")
            body.append("\n".join(self.description).strip())
            
            if self.solution:
                body.append("\n### Describe the solution you'd like")
                body.append("\n".join(self.solution).strip())
            
            body.append("\n### Business Value / Impact")
            # Try to extract impact from description if possible, else generic
            impact_found = False
            for line in self.description:
                if "Impact" in line:
                    body.append(line)
                    impact_found = True
            if not impact_found:
                 body.append("See Severity/Priority field.")

        elif "tech-debt" in self.labels or "infrastructure" in self.labels:
            # Template: technical-debt.yml
            # Headers: Area, Current Implementation, Proposed Improvement, Risk Level
            
            body.append("\n### Current Implementation")
            body.append("\n".join(self.description).strip())
            
            if self.solution:
                body.append("\n### Proposed Improvement")
                body.append("\n".join(self.solution).strip())
            
            body.append("\n### Risk Level")
            body.append("Medium (Default for Tech Debt analysis)")

        else:
            # Fallback for Documentation/Other
            body.append("\n### Problem Description")
            body.append("\n".join(self.description).strip())
            if self.solution:
                body.append("\n### Proposed Solution")
                body.append("\n".join(self.solution).strip())
            
        # --- Evidence / Footer ---
        body.append("\n### Evidence / Context")
        body.append("*Auto-generated from Analysis Pipeline Output*")
        
        return "\n".join(body)

class ParserState(Enum):
    SEARCHING = 0
    IN_CATEGORY = 1
    IN_PROBLEM = 2

def parse_markdown(file_path: Path, target_cat: Optional[str] = None) -> List[IssueData]:
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    issues = []
    current_issue: Optional[IssueData] = None
    current_category = ""
    
    # State tracking
    capture_mode = None # 'description', 'solution', None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Regex patterns
    cat_header_re = re.compile(r"^###\s+(CAT-\d+):")
    prob_header_re = re.compile(r"^####\s+Problem\s+(P\d+):\s+(.*)")
    field_re = re.compile(r"^\*\*(Original ID|Type|Severity|Quick Win|Total Effort|Owner)\*\*:\s*(.*)")
    section_header_re = re.compile(r"^#####\s+(.*)")

    for line in lines:
        line = line.strip()

        # 1. Detect Category Header
        cat_match = cat_header_re.match(line)
        if cat_match:
            current_category = cat_match.group(1)
            continue

        # 2. Detect Problem Header
        prob_match = prob_header_re.match(line)
        if prob_match:
            # Save previous issue if exists
            if current_issue:
                issues.append(current_issue)
            
            # Start new issue
            current_issue = IssueData()
            current_issue.p_id = prob_match.group(1)
            current_issue.title = prob_match.group(2)
            current_issue.category_id = current_category
            capture_mode = None
            continue

        # If we are inside an issue parsing block
        if current_issue:
            # 3. Detect Metadata Fields
            field_match = field_re.match(line)
            if field_match:
                key = field_match.group(1)
                val = field_match.group(2).strip()
                
                if key == "Type": current_issue.original_type = val
                elif key == "Severity": current_issue.severity = val
                elif key == "Quick Win": current_issue.quick_win = (val.upper() == "YES")
                elif key == "Total Effort": current_issue.effort = val
                elif key == "Owner": current_issue.owner = val
                continue

            # 4. Detect Section Headers (Description vs Solution)
            section_match = section_header_re.match(line)
            if section_match:
                section_title = section_match.group(1).lower()
                if "analysis" in section_title or "description" in section_title:
                    capture_mode = 'description'
                elif "solution" in section_title or "options" in section_title:
                    capture_mode = 'solution'
                else:
                    capture_mode = None
                continue
            
            # 5. Capture Content
            if capture_mode == 'description':
                # Skip Metadata bullets if they appear in description
                if not line.startswith("**"):
                    current_issue.description.append(line)
            elif capture_mode == 'solution':
                if not line.startswith("**Metadata"):
                    current_issue.solution.append(line)

    # Append last issue
    if current_issue:
        issues.append(current_issue)

    # Filter by category if requested
    if target_cat:
        issues = [i for i in issues if i.category_id == target_cat]

    return issues

def issue_exists(p_id: str) -> bool:
    """Check if an issue with this P_ID already exists in GitHub."""
    try:
        # Search for issue with P_ID in title
        cmd = ["gh", "issue", "list", "--search", f"{p_id} in:title", "--json", "number"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return len(data) > 0
    except Exception:
        return False # Assume false on error to be safe, or true to be conservative. 
                     # Safe approach: False allows creation, but let's warn.
        return False

def create_issue(issue: IssueData, dry_run: bool):
    title = f"{issue.p_id}: {issue.title}"
    body = issue.construct_body()
    labels = ",".join(issue.labels)

    print(f"\n[Processing] {title}")
    print(f"  Labels: {labels}")
    
    if dry_run:
        print("  --- DRY RUN: Body Preview ---")
        print(f"  {body[:100].replace(chr(10), ' ')}...") # First 100 chars
        print("  -----------------------------")
        return

    if issue_exists(issue.p_id):
        print(f"  [SKIP] Issue {issue.p_id} already exists.")
        return

    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body,
        "--label", labels
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  [SUCCESS] Created: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Failed to create issue: {e.stderr}")

def main():
    parser = argparse.ArgumentParser(description="Populate GitHub Backlog from Analysis")
    parser.add_argument("--source", required=True, type=Path, help="Path to analysis markdown file")
    parser.add_argument("--category", help="Filter by Category ID (e.g., CAT-001)")
    parser.add_argument("--execute", action="store_true", help="Execute creation (default is dry-run)")
    
    args = parser.parse_args()
    
    print(f"Parsing {args.source}...")
    issues = parse_markdown(args.source, args.category)
    
    print(f"Found {len(issues)} issues to process.")
    
    if not args.execute:
        print("\n*** DRY RUN MODE *** (Use --execute to create issues)\n")
    
    for issue in issues:
        create_issue(issue, not args.execute)

if __name__ == "__main__":
    main()
