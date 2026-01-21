#!/usr/bin/env bash

# Consolidated prerequisite checking script
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --require-tasks     Require tasks.md to exist (for implementation phase)
#   --include-tasks     Include tasks.md in AVAILABLE_DOCS list
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: FEATURE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            ;;
        --include-tasks)
            INCLUDE_TASKS=true
            ;;
        --paths-only)
            PATHS_ONLY=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: check-prerequisites.sh [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for implementation phase)
  --include-tasks     Include tasks.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  ./check-prerequisites.sh --json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  ./check-prerequisites.sh --json --require-tasks --include-tasks
  
  # Get feature paths only (no validation)
  ./check-prerequisites.sh --paths-only
  
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Dependency checks (core tools used by Spec-Kit workflows)
deps_missing=false
missing_tools=()

log_dep() {
    if $JSON_MODE; then
        echo "$@" >&2
    else
        echo "$@"
    fi
}

OS_NAME="$(uname -s)"
LINUX_ID=""
if [[ "$OS_NAME" == "Linux" && -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    LINUX_ID="${ID:-}"
fi

install_hint() {
    local tool="$1"
    case "$tool" in
        git)
            if [[ "$OS_NAME" == "Darwin" ]]; then
                log_dep "  macOS: brew install git"
            elif [[ "$OS_NAME" == "Linux" ]]; then
                log_dep "  Linux: sudo apt install git"
            else
                log_dep "  Windows: winget install --id Git.Git"
            fi
            ;;
        python)
            if [[ "$OS_NAME" == "Darwin" ]]; then
                log_dep "  macOS: brew install python"
            elif [[ "$OS_NAME" == "Linux" ]]; then
                log_dep "  Linux: sudo apt install python3"
            else
                log_dep "  Windows: winget install --id Python.Python.3"
            fi
            ;;
        uv)
            if [[ "$OS_NAME" == "Darwin" ]]; then
                log_dep "  macOS: brew install uv"
            else
                log_dep "  pipx: pipx install uv"
                log_dep "  pip: pip install uv"
            fi
            ;;
        yq)
            if [[ "$OS_NAME" == "Darwin" ]]; then
                log_dep "  macOS: brew install yq"
            elif [[ "$OS_NAME" == "Linux" ]]; then
                log_dep "  Linux: sudo apt install yq"
            else
                log_dep "  Windows: winget install --id MikeFarah.yq"
            fi
            ;;
        rg)
            if [[ "$OS_NAME" == "Darwin" ]]; then
                log_dep "  macOS: brew install ripgrep"
            elif [[ "$OS_NAME" == "Linux" ]]; then
                log_dep "  Linux: sudo apt install ripgrep"
            else
                log_dep "  Windows: winget install --id BurntSushi.ripgrep.MSVC"
            fi
            ;;
    esac
}

check_cmd() {
    local cmd="$1"
    local label="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        return 0
    fi
    missing_tools+=("$label")
    deps_missing=true
    log_dep "✗ Missing required tool: $label"
    install_hint "$cmd"
    log_dep ""
    return 1
}

log_dep "Checking system dependencies..."
check_cmd "git" "git"

if command -v python3 >/dev/null 2>&1; then
    # Check if PyYAML is installed
    if ! python3 -c "import yaml" >/dev/null 2>&1; then
        missing_tools+=("pyyaml")
        deps_missing=true
        log_dep "✗ Missing required Python module: PyYAML"
        log_dep "  Install: pip install pyyaml"
        log_dep ""
    fi
elif command -v python >/dev/null 2>&1; then
    # Check if PyYAML is installed
    if ! python -c "import yaml" >/dev/null 2>&1; then
        missing_tools+=("pyyaml")
        deps_missing=true
        log_dep "✗ Missing required Python module: PyYAML"
        log_dep "  Install: pip install pyyaml"
        log_dep ""
    fi
else
    missing_tools+=("python3")
    deps_missing=true
    log_dep "✗ Missing required tool: python3 (or python)"
    install_hint "python"
    log_dep ""
fi

check_cmd "uv" "uv"
# yq is now optional - state management uses Python/PyYAML
if ! command -v yq >/dev/null 2>&1; then
    log_dep "⚠ Optional tool not found: yq (YAML processor)"
    log_dep "  Note: State management now uses Python/PyYAML instead"
    log_dep "  yq is still useful for manual YAML queries"
    install_hint "yq"
    log_dep ""
fi
check_cmd "rg" "rg (ripgrep)"

if $deps_missing; then
    log_dep "Missing required tools: ${missing_tools[*]}"
    log_dep ""
fi

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths and validate branch
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # Minimal JSON paths payload (no validation performed)
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","FEATURE_DIR":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$FEATURE_DIR" "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "FEATURE_DIR: $FEATURE_DIR"
        echo "FEATURE_SPEC: $FEATURE_SPEC"
        echo "IMPL_PLAN: $IMPL_PLAN"
        echo "TASKS: $TASKS"
    fi
    if $deps_missing; then
        exit 1
    fi
    exit 0
fi

# Validate required directories and files
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /speckit.specify first to create the feature structure." >&2
    exit 1
fi

if [[ ! -f "$IMPL_PLAN" ]]; then
    echo "ERROR: plan.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit.plan first to create the implementation plan." >&2
    exit 1
fi

# Check for tasks.md if required
if $REQUIRE_TASKS && [[ ! -f "$TASKS" ]]; then
    echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit.tasks first to create the task list." >&2
    exit 1
fi

# Build list of available documents
docs=()

# Always check these optional docs
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")

# Check contracts directory (only if it exists and has files)
if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi

[[ -f "$QUICKSTART" ]] && docs+=("quickstart.md")

# Include tasks.md if requested and it exists
if $INCLUDE_TASKS && [[ -f "$TASKS" ]]; then
    docs+=("tasks.md")
fi

# Output results
if $JSON_MODE; then
    # Build JSON array of documents
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi
    
    printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$FEATURE_DIR" "$json_docs"
else
    # Text output
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    check_file "$RESEARCH" "research.md"
    check_file "$DATA_MODEL" "data-model.md"
    check_dir "$CONTRACTS_DIR" "contracts/"
    check_file "$QUICKSTART" "quickstart.md"
    
    if $INCLUDE_TASKS; then
        check_file "$TASKS" "tasks.md"
    fi
fi

if $deps_missing; then
    exit 1
fi
