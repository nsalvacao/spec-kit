#!/usr/bin/env bash
# Requires: Bash 4+
# calculate-ai-rice.sh — AI-RICE score calculator for Phase 0 SELECT
#
# Computes the AI-RICE score from six input dimensions and outputs a
# structured analysis with dimensional breakdown and rationale.
#
# Usage:
#   ./calculate-ai-rice.sh REACH IMPACT CONFIDENCE DATA_READINESS EFFORT RISK [--name "Idea Name"]
#
# Arguments:
#   REACH           Users/sessions impacted per quarter (positive integer)
#   IMPACT          Impact multiplier: 0.25 | 0.5 | 1.0 | 2.0 | 3.0
#   CONFIDENCE      Confidence as integer percentage 0-100
#   DATA_READINESS  Data readiness as integer percentage 0-100
#   EFFORT          Effort in person-weeks (positive number)
#   RISK            Risk level 1-10 (integer)
#
# Options:
#   --name "Name"   Optional idea name (for display)
#   --help, -h      Show this help message
#
# Formula:
#   AI-RICE = (Reach × Impact × Confidence × Data_Readiness) / (Effort × Risk)
#   (Confidence and Data_Readiness are raw integers 0-100)
#
# Note: To compare multiple ideas, normalise:
#   Norm_Score = (raw_score / session_max_raw) × 100

set -euo pipefail

if ((BASH_VERSINFO[0] < 4)); then
    echo "Error: Bash 4.0 or higher is required (running: ${BASH_VERSION})." >&2
    exit 1
fi

IDEA_NAME=""
POSITIONAL=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            echo "Usage: $(basename "$0") REACH IMPACT CONFIDENCE DATA_READINESS EFFORT RISK [--name \"Name\"]"
            echo ""
            echo "Compute AI-RICE score for a single idea."
            echo ""
            echo "Arguments:"
            echo "  REACH           Users/sessions per quarter (positive integer)"
            echo "  IMPACT          Impact multiplier: 0.25 | 0.5 | 1.0 | 2.0 | 3.0"
            echo "  CONFIDENCE      Confidence percentage 0-100"
            echo "  DATA_READINESS  Data readiness percentage 0-100"
            echo "  EFFORT          Person-weeks (positive number)"
            echo "  RISK            Risk 1-10 (integer)"
            echo ""
            echo "Options:"
            echo "  --name \"Name\"   Optional idea name for display"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Formula: (Reach × Impact × Confidence × Data_Readiness) / (Effort × Risk)"
            echo ""
            echo "Example:"
            echo "  $(basename "$0") 1000 2.0 70 80 4 5 --name \"My Feature\""
            exit 0
            ;;
        --name)
            shift
            IDEA_NAME="$1"
            ;;
        --*)
            echo "Error: Unknown option '$1'" >&2
            echo "Run '$(basename "$0") --help' for usage." >&2
            exit 1
            ;;
        *)
            POSITIONAL+=("$1")
            ;;
    esac
    shift
done

if [[ ${#POSITIONAL[@]} -ne 6 ]]; then
    echo "Error: Expected 6 positional arguments, got ${#POSITIONAL[@]}." >&2
    echo "Run '$(basename "$0") --help' for usage." >&2
    exit 1
fi

REACH="${POSITIONAL[0]}"
IMPACT="${POSITIONAL[1]}"
CONFIDENCE="${POSITIONAL[2]}"
DATA_READINESS="${POSITIONAL[3]}"
EFFORT="${POSITIONAL[4]}"
RISK="${POSITIONAL[5]}"

# --- Validation ---

# Reach: positive integer
if ! [[ "$REACH" =~ ^[0-9]+$ ]] || [[ "$REACH" -le 0 ]]; then
    echo "Error: REACH must be a positive integer (got: $REACH)" >&2
    exit 1
fi

# Impact: must be one of the allowed values
case "$IMPACT" in
    0.25|0.5|1.0|2.0|3.0) ;;
    *)
        echo "Error: IMPACT must be one of: 0.25, 0.5, 1.0, 2.0, 3.0 (got: $IMPACT)" >&2
        exit 1
        ;;
esac

# Confidence: integer 0-100
if ! [[ "$CONFIDENCE" =~ ^[0-9]+$ ]] || [[ "$CONFIDENCE" -gt 100 ]]; then
    echo "Error: CONFIDENCE must be an integer 0-100 (got: $CONFIDENCE)" >&2
    exit 1
fi

# Data_Readiness: integer 0-100
if ! [[ "$DATA_READINESS" =~ ^[0-9]+$ ]] || [[ "$DATA_READINESS" -gt 100 ]]; then
    echo "Error: DATA_READINESS must be an integer 0-100 (got: $DATA_READINESS)" >&2
    exit 1
fi

# Effort: positive number
if ! echo "$EFFORT" | awk '{exit ($1 > 0) ? 0 : 1}'; then
    echo "Error: EFFORT must be a positive number (got: $EFFORT)" >&2
    exit 1
fi

# Risk: integer 1-10
if ! [[ "$RISK" =~ ^[0-9]+$ ]] || [[ "$RISK" -lt 1 ]] || [[ "$RISK" -gt 10 ]]; then
    echo "Error: RISK must be an integer 1-10 (got: $RISK)" >&2
    exit 1
fi

# --- Calculate ---

RAW_SCORE=$(awk -v r="$REACH" -v i="$IMPACT" -v c="$CONFIDENCE" \
    -v dr="$DATA_READINESS" -v e="$EFFORT" -v risk="$RISK" \
    'BEGIN { printf "%.2f", (r * i * c * dr) / (e * risk) }')

# --- Classify dimensions ---

classify_reach() {
    local r="$1"
    if   [[ "$r" -ge 10000 ]]; then echo "HIGH (≥10 000 users/quarter)"
    elif [[ "$r" -ge 1000  ]]; then echo "MEDIUM (1 000–9 999)"
    elif [[ "$r" -ge 100   ]]; then echo "SMALL (100–999)"
    else                             echo "NICHE (<100)"
    fi
}

classify_impact() {
    case "$1" in
        3.0) echo "MASSIVE" ;;
        2.0) echo "HIGH" ;;
        1.0) echo "NORMAL" ;;
        0.5) echo "LOW" ;;
        *)   echo "MINIMAL" ;;
    esac
}

classify_pct() {
    local p="$1" label="$2"
    if   [[ "$p" -ge 85 ]]; then echo "${label}: HIGH (${p}%)"
    elif [[ "$p" -ge 70 ]]; then echo "${label}: GOOD (${p}%)"
    elif [[ "$p" -ge 40 ]]; then echo "${label}: MODERATE (${p}%)"
    else                          echo "${label}: LOW (${p}%)"
    fi
}

classify_effort() {
    local e="$1"
    awk -v e="$e" 'BEGIN {
        if (e >= 12)     print "HIGH (≥12 weeks — quarter)"
        else if (e >= 6) print "MEDIUM (6–11 weeks — months)"
        else if (e >= 2) print "MEDIUM (2–5 weeks)"
        else             print "LOW (<2 weeks)"
    }'
}

classify_risk() {
    local r="$1"
    if   [[ "$r" -ge 7 ]]; then echo "HIGH (${r}/10)"
    elif [[ "$r" -ge 4 ]]; then echo "MEDIUM (${r}/10)"
    else                         echo "LOW (${r}/10)"
    fi
}

# Identify biggest drivers and limiters for rationale
build_rationale() {
    local reach="$1" impact="$2" conf="$3" dr="$4" effort="$5" risk="$6"

    local drivers=()
    local moderators=()
    local limiters=()

    # Drivers: high reach amplifies
    if   [[ "$reach" -ge 10000 ]]; then drivers+=("very high Reach (${reach})")
    elif [[ "$reach" -ge 1000  ]]; then drivers+=("strong Reach (${reach})")
    elif [[ "$reach" -ge 100   ]]; then moderators+=("moderate Reach (${reach})")
    else                                moderators+=("low Reach (${reach})")
    fi

    # Impact drivers
    case "$impact" in
        3.0) drivers+=("massive Impact (3.0)") ;;
        2.0) drivers+=("high Impact (2.0)") ;;
        1.0) moderators+=("baseline Impact (1.0)") ;;
        *)   moderators+=("below-baseline Impact (${impact})") ;;
    esac

    # Confidence
    if   [[ "$conf" -ge 85 ]]; then drivers+=("high Confidence (${conf}%)")
    elif [[ "$conf" -ge 70 ]]; then moderators+=("good Confidence (${conf}%)")
    elif [[ "$conf" -ge 40 ]]; then moderators+=("moderate Confidence (${conf}%)")
    else                            limiters+=("low Confidence (${conf}%)")
    fi

    # Data_Readiness
    if   [[ "$dr" -ge 85 ]]; then drivers+=("high Data_Readiness (${dr}%)")
    elif [[ "$dr" -ge 70 ]]; then moderators+=("good Data_Readiness (${dr}%)")
    elif [[ "$dr" -ge 40 ]]; then moderators+=("moderate Data_Readiness (${dr}%)")
    else                          limiters+=("low Data_Readiness (${dr}%)")
    fi

    # Limiters: effort and risk divide the score
    local effort_class
    effort_class=$(awk -v e="$effort" 'BEGIN {
        if (e >= 12)     print "high"
        else if (e >= 6) print "medium"
        else if (e >= 2) print "moderate"
        else             print "low"
    }')
    case "$effort_class" in
        high)     limiters+=("high Effort (${effort} weeks)") ;;
        medium)   limiters+=("medium Effort (${effort} weeks)") ;;
        moderate) moderators+=("moderate Effort (${effort} weeks)") ;;
        *)        moderators+=("low Effort (${effort} weeks)") ;;
    esac

    if   [[ "$risk" -ge 7 ]]; then limiters+=("high Risk (${risk}/10)")
    elif [[ "$risk" -ge 4 ]]; then limiters+=("medium Risk (${risk}/10)")
    else                            moderators+=("low Risk (${risk}/10)")
    fi

    local driver_str="" limiter_str=""
    local driver_joined="" limiter_joined="" item
    for item in "${drivers[@]+"${drivers[@]}"}"; do
        driver_joined="${driver_joined:+${driver_joined}, }${item}"
    done
    for item in "${limiters[@]+"${limiters[@]}"}"; do
        limiter_joined="${limiter_joined:+${limiter_joined}, }${item}"
    done

    if [[ -n "$driver_joined" ]]; then
        driver_str="Score driven by ${driver_joined}."
    else
        driver_str="No standout drivers detected."
    fi
    if [[ -n "$limiter_joined" ]]; then
        limiter_str=" Limited by ${limiter_joined}."
    fi

    echo "${driver_str}${limiter_str}"
}

REACH_CLASS=$(classify_reach "$REACH")
IMPACT_CLASS=$(classify_impact "$IMPACT")
CONF_CLASS=$(classify_pct "$CONFIDENCE" "Confidence")
DR_CLASS=$(classify_pct "$DATA_READINESS" "Data_Readiness")
EFFORT_CLASS=$(classify_effort "$EFFORT")
RISK_CLASS=$(classify_risk "$RISK")
RATIONALE=$(build_rationale "$REACH" "$IMPACT" "$CONFIDENCE" "$DATA_READINESS" "$EFFORT" "$RISK")

NUMERATOR=$(awk -v r="$REACH" -v i="$IMPACT" -v c="$CONFIDENCE" -v dr="$DATA_READINESS" \
    'BEGIN { printf "%.0f", r * i * c * dr }')
DENOMINATOR=$(awk -v e="$EFFORT" -v risk="$RISK" \
    'BEGIN { printf "%.0f", e * risk }')

# --- Output ---

echo "┌─────────────────────────────────────────────────────────────┐"
if [[ -n "$IDEA_NAME" ]]; then
    printf "│ AI-RICE Calculator — %-40s│\n" "$IDEA_NAME"
else
    echo "│ AI-RICE Calculator                                          │"
fi
echo "└─────────────────────────────────────────────────────────────┘"
echo ""
echo "Input Dimensions:"
printf "  %-20s %s\n"  "Reach:"          "$REACH ($REACH_CLASS)"
printf "  %-20s %s\n"  "Impact:"         "$IMPACT ($IMPACT_CLASS)"
printf "  %-20s %s\n"  "Confidence:"     "$CONFIDENCE% ($CONF_CLASS)"
printf "  %-20s %s\n"  "Data_Readiness:" "$DATA_READINESS% ($DR_CLASS)"
printf "  %-20s %s\n"  "Effort:"         "$EFFORT weeks ($EFFORT_CLASS)"
printf "  %-20s %s\n"  "Risk:"           "$RISK/10 ($RISK_CLASS)"
echo ""
echo "Formula: (Reach × Impact × Confidence × Data_Readiness) / (Effort × Risk)"
echo "       = ($REACH × $IMPACT × $CONFIDENCE × $DATA_READINESS) / ($EFFORT × $RISK)"
echo "       = $NUMERATOR / $DENOMINATOR"
echo ""
printf "AI-RICE Raw Score: %.2f\n" "$RAW_SCORE"
echo ""
echo "Dimensional Analysis:"
echo "  ▲ Numerator (amplifiers): Reach, Impact, Confidence, Data_Readiness"
echo "  ▼ Denominator (reducers):  Effort, Risk"
echo ""
echo "  Reach          → $REACH_CLASS"
echo "  Impact         → $IMPACT_CLASS ($IMPACT)"
echo "  $CONF_CLASS"
echo "  $DR_CLASS"
echo "  Effort         → $EFFORT_CLASS"
echo "  Risk           → $RISK_CLASS"
echo ""
echo "Rationale: $RATIONALE"
echo ""
echo "Note: To compare across ideas in a session:"
echo "  Norm_Score = (raw_score / session_max_raw) × 100"
