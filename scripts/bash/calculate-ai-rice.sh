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
            if [[ -z "${1:-}" || "${1:-}" == --* ]]; then
                echo "Error: --name requires a value (e.g., --name \"My Idea\")" >&2
                exit 1
            fi
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

# Effort: positive number (must be numeric)
if ! [[ "$EFFORT" =~ ^[0-9]+(\.[0-9]+)?$ ]] || ! echo "$EFFORT" | awk '{exit ($1 > 0) ? 0 : 1}'; then
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
        else if (e >= 2) print "MODERATE (2–5 weeks)"
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

# --- Sensitivity Analysis ---

# Impact discrete scale for step-wise ±1
IMPACT_SCALE=(0.25 0.5 1.0 2.0 3.0)

_impact_step_up() {
    local current="$1" found=0 val
    for val in "${IMPACT_SCALE[@]}"; do
        if [[ "$found" -eq 1 ]]; then echo "$val"; return; fi
        [[ "$val" == "$current" ]] && found=1
    done
    echo "$current"
}

_impact_step_down() {
    local current="$1" prev="" val
    for val in "${IMPACT_SCALE[@]}"; do
        if [[ "$val" == "$current" ]]; then echo "${prev:-$current}"; return; fi
        prev="$val"
    done
    echo "$current"
}

_score_raw() {
    awk -v r="$1" -v i="$2" -v c="$3" -v dr="$4" -v e="$5" -v risk="$6" \
        'BEGIN { printf "%.2f", (r * i * c * dr) / (e * risk) }'
}

_fmt_delta() {
    awk -v n="$1" -v b="$2" \
        'BEGIN { d = n - b; if (d >= 0) printf "+%.2f", d; else printf "%.2f", d }'
}

_clamp_pct()  { local v="$1"; echo $(( v < 0 ? 0 : (v > 100 ? 100 : v) )); }
_clamp_risk() { local v="$1"; echo $(( v < 1 ? 1 : (v > 10  ? 10  : v) )); }
_clamp_reach(){ local v="$1"; echo $(( v < 1 ? 1 : v )); }

# Bounded ±1 values per dimension
SENS_RP=$(_clamp_reach $(( REACH + 1 )))
SENS_RM=$(_clamp_reach $(( REACH - 1 )))
SENS_IP=$(_impact_step_up   "$IMPACT")
SENS_IM=$(_impact_step_down "$IMPACT")
SENS_CP=$(_clamp_pct $(( CONFIDENCE + 1 )))
SENS_CM=$(_clamp_pct $(( CONFIDENCE - 1 )))
SENS_DP=$(_clamp_pct $(( DATA_READINESS + 1 )))
SENS_DM=$(_clamp_pct $(( DATA_READINESS - 1 )))
SENS_EP=$(awk -v e="$EFFORT" 'BEGIN { printf "%.10g", e + 1 }')
SENS_EM=$(awk -v e="$EFFORT" 'BEGIN { v = e - 1; printf "%.10g", (v < 1 ? 1 : v) }')
SENS_KP=$(_clamp_risk $(( RISK + 1 )))
SENS_KM=$(_clamp_risk $(( RISK - 1 )))

# Scenario scores
SC_RP=$(_score_raw "$SENS_RP" "$IMPACT"   "$CONFIDENCE"    "$DATA_READINESS" "$EFFORT"   "$RISK")
SC_RM=$(_score_raw "$SENS_RM" "$IMPACT"   "$CONFIDENCE"    "$DATA_READINESS" "$EFFORT"   "$RISK")
SC_IP=$(_score_raw "$REACH"   "$SENS_IP"  "$CONFIDENCE"    "$DATA_READINESS" "$EFFORT"   "$RISK")
SC_IM=$(_score_raw "$REACH"   "$SENS_IM"  "$CONFIDENCE"    "$DATA_READINESS" "$EFFORT"   "$RISK")
SC_CP=$(_score_raw "$REACH"   "$IMPACT"   "$SENS_CP"       "$DATA_READINESS" "$EFFORT"   "$RISK")
SC_CM=$(_score_raw "$REACH"   "$IMPACT"   "$SENS_CM"       "$DATA_READINESS" "$EFFORT"   "$RISK")
SC_DP=$(_score_raw "$REACH"   "$IMPACT"   "$CONFIDENCE"    "$SENS_DP"        "$EFFORT"   "$RISK")
SC_DM=$(_score_raw "$REACH"   "$IMPACT"   "$CONFIDENCE"    "$SENS_DM"        "$EFFORT"   "$RISK")
SC_EP=$(_score_raw "$REACH"   "$IMPACT"   "$CONFIDENCE"    "$DATA_READINESS" "$SENS_EP"  "$RISK")
SC_EM=$(_score_raw "$REACH"   "$IMPACT"   "$CONFIDENCE"    "$DATA_READINESS" "$SENS_EM"  "$RISK")
SC_KP=$(_score_raw "$REACH"   "$IMPACT"   "$CONFIDENCE"    "$DATA_READINESS" "$EFFORT"   "$SENS_KP")
SC_KM=$(_score_raw "$REACH"   "$IMPACT"   "$CONFIDENCE"    "$DATA_READINESS" "$EFFORT"   "$SENS_KM")

# Delta strings (formatted with sign)
D_RP=$(_fmt_delta "$SC_RP" "$RAW_SCORE"); D_RM=$(_fmt_delta "$SC_RM" "$RAW_SCORE")
D_IP=$(_fmt_delta "$SC_IP" "$RAW_SCORE"); D_IM=$(_fmt_delta "$SC_IM" "$RAW_SCORE")
D_CP=$(_fmt_delta "$SC_CP" "$RAW_SCORE"); D_CM=$(_fmt_delta "$SC_CM" "$RAW_SCORE")
D_DP=$(_fmt_delta "$SC_DP" "$RAW_SCORE"); D_DM=$(_fmt_delta "$SC_DM" "$RAW_SCORE")
D_EP=$(_fmt_delta "$SC_EP" "$RAW_SCORE"); D_EM=$(_fmt_delta "$SC_EM" "$RAW_SCORE")
D_KP=$(_fmt_delta "$SC_KP" "$RAW_SCORE"); D_KM=$(_fmt_delta "$SC_KM" "$RAW_SCORE")

# Identify most influential positive and negative levers
SENS_SUMMARY=$(awk -v base="$RAW_SCORE" \
    -v srp="$SC_RP" -v sip="$SC_IP" -v scp="$SC_CP" \
    -v sdp="$SC_DP" -v sem="$SC_EM" -v skm="$SC_KM" \
    -v srm="$SC_RM" -v sim="$SC_IM" -v scm="$SC_CM" \
    -v sdm="$SC_DM" -v sep="$SC_EP" -v skp="$SC_KP" \
'BEGIN {
    pos_d[0] = srp - base; pos_n[0] = "Reach +1"
    pos_d[1] = sip - base; pos_n[1] = "Impact +1 step"
    pos_d[2] = scp - base; pos_n[2] = "Confidence +1%"
    pos_d[3] = sdp - base; pos_n[3] = "Data_Readiness +1%"
    pos_d[4] = sem - base; pos_n[4] = "Effort -1 wk"
    pos_d[5] = skm - base; pos_n[5] = "Risk -1"
    neg_d[0] = srm - base; neg_n[0] = "Reach -1"
    neg_d[1] = sim - base; neg_n[1] = "Impact -1 step"
    neg_d[2] = scm - base; neg_n[2] = "Confidence -1%"
    neg_d[3] = sdm - base; neg_n[3] = "Data_Readiness -1%"
    neg_d[4] = sep - base; neg_n[4] = "Effort +1 wk"
    neg_d[5] = skp - base; neg_n[5] = "Risk +1"
    bi = 0; ni = 0
    for (i = 1; i < 6; i++) {
        if (pos_d[i] > pos_d[bi]) bi = i
        if (neg_d[i] < neg_d[ni]) ni = i
    }
    pd = pos_d[bi]; nd = neg_d[ni]
    pstr = (pd >= 0) ? sprintf("+%.2f", pd) : sprintf("%.2f", pd)
    printf "  ▲ Best upside:  %s → Δ%s\n", pos_n[bi], pstr
    printf "  ▼ Biggest risk: %s → Δ%.2f\n", neg_n[ni], nd
}')

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
echo "Sensitivity Analysis (what-if ±1 per dimension):"
printf "  %-18s +1 → %s (Δ%s) | -1 → %s (Δ%s)\n" \
    "Reach:"         "$SC_RP" "$D_RP" "$SC_RM" "$D_RM"
printf "  %-18s +1 step → %s (Δ%s) | -1 step → %s (Δ%s)\n" \
    "Impact:"        "$SC_IP" "$D_IP" "$SC_IM" "$D_IM"
printf "  %-18s +1%% → %s (Δ%s) | -1%% → %s (Δ%s)\n" \
    "Confidence:"    "$SC_CP" "$D_CP" "$SC_CM" "$D_CM"
printf "  %-18s +1%% → %s (Δ%s) | -1%% → %s (Δ%s)\n" \
    "Data_Readiness:" "$SC_DP" "$D_DP" "$SC_DM" "$D_DM"
printf "  %-18s +1 wk → %s (Δ%s) | -1 wk → %s (Δ%s)\n" \
    "Effort:"        "$SC_EP" "$D_EP" "$SC_EM" "$D_EM"
printf "  %-18s +1 → %s (Δ%s) | -1 → %s (Δ%s)\n" \
    "Risk:"          "$SC_KP" "$D_KP" "$SC_KM" "$D_KM"
echo ""
echo "Levers summary:"
echo "$SENS_SUMMARY"
echo ""
echo "Note: To compare across ideas in a session:"
echo "  Norm_Score = (raw_score / session_max_raw) × 100"
