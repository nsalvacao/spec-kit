#!/usr/bin/env bash
# =============================================================================
# ops/setup-repository.sh
#
# Interactive setup script that configures all required GitHub Actions secrets
# and variables for this repository using a privileged Personal Access Token.
#
# The Copilot coding agent cannot manage secrets/variables directly (its token
# lacks the required GitHub App permissions). Run this script once, locally,
# with an admin PAT to set everything up.
#
# Usage:
#   export GH_ADMIN_TOKEN="<your-PAT>"
#   ./ops/setup-repository.sh [--dry-run]
#
# Required PAT permissions (fine-grained):
#   - Actions secrets: Read and write
#   - Actions variables: Read and write
#   - Administration: Read and write
#   - Environments: Read and write
#   - Contents: Read and write
#
# Or use a classic PAT with scopes: repo, workflow, admin:repo_hook
# =============================================================================
set -euo pipefail

REPO="nsalvacao/spec-kit"
DRY_RUN=false

# ─── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${CYAN}ℹ ${RESET}$*"; }
success() { echo -e "${GREEN}✅ ${RESET}$*"; }
warn()    { echo -e "${YELLOW}⚠  ${RESET}$*"; }
error()   { echo -e "${RED}❌ ${RESET}$*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}═══ $* ═══${RESET}"; }

# ─── Argument parsing ─────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --help|-h)
      echo "Usage: $0 [--dry-run]"
      echo ""
      echo "  --dry-run   Show what would be configured without making changes"
      echo ""
      echo "Environment variables required:"
      echo "  GH_ADMIN_TOKEN   GitHub PAT with secrets/variables write access"
      exit 0
      ;;
    *)
      error "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

# ─── Pre-flight checks ────────────────────────────────────────────────────────
header "Pre-flight checks"

if [[ -z "${GH_ADMIN_TOKEN:-}" ]]; then
  error "GH_ADMIN_TOKEN is not set."
  echo ""
  echo "  Create a fine-grained PAT at:"
  echo "  https://github.com/settings/personal-access-tokens"
  echo ""
  echo "  Required repository permissions:"
  echo "    Actions secrets: Read and write"
  echo "    Actions variables: Read and write"
  echo "    Administration: Read and write"
  echo "    Environments: Read and write"
  echo ""
  echo "  Then: export GH_ADMIN_TOKEN=\"<your-PAT>\""
  exit 1
fi

if ! command -v gh &>/dev/null; then
  error "GitHub CLI (gh) is not installed."
  echo "  Install: https://cli.github.com/"
  exit 1
fi

# Use the admin token for all gh calls in this script
export GH_TOKEN="${GH_ADMIN_TOKEN}"

# Verify the token works and has access to the repo
if ! gh api "repos/${REPO}" --jq '.full_name' &>/dev/null; then
  error "GH_ADMIN_TOKEN cannot access the repository ${REPO}."
  echo "  Check that the token has the correct repository permissions."
  exit 1
fi

success "Token validated — has access to ${REPO}"

if [[ "${DRY_RUN}" == "true" ]]; then
  warn "DRY RUN mode — no changes will be made"
fi

# ─── Helper: set a secret ─────────────────────────────────────────────────────
set_secret() {
  local name="$1"
  local value="$2"
  local description="${3:-}"

  if [[ -z "${value}" ]]; then
    warn "Skipping secret ${name} — no value provided"
    return 0
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    info "[dry-run] Would set secret: ${name}"
    # Wipe the value from memory immediately after inspection
    value=""
    return 0
  fi

  # Pipe directly into gh to avoid leaving the value in a variable longer than needed
  printf '%s' "${value}" | gh secret set "${name}" --repo "${REPO}" 2>&1 && \
    success "Set secret: ${name}" || \
    { error "Failed to set secret: ${name}"; value=""; return 1; }

  # Wipe the value from local scope as soon as it has been consumed
  value=""
}

# ─── Helper: set a variable ───────────────────────────────────────────────────
set_variable() {
  local name="$1"
  local value="$2"

  if [[ -z "${value}" ]]; then
    warn "Skipping variable ${name} — no value provided"
    return 0
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    info "[dry-run] Would set variable: ${name} = ${value}"
    return 0
  fi

  gh variable set "${name}" --repo "${REPO}" --body "${value}" 2>&1 && \
    success "Set variable: ${name} = ${value}" || \
    { error "Failed to set variable: ${name}"; return 1; }
}

# ─── Helper: prompt for a secret value ───────────────────────────────────────
prompt_secret() {
  local name="$1"
  local description="$2"
  local example="${3:-}"
  local value=""

  echo ""
  echo -e "  ${BOLD}${name}${RESET}"
  echo "  ${description}"
  [[ -n "${example}" ]] && echo -e "  ${YELLOW}Example: ${example}${RESET}"

  read -rsp "  Value (empty to skip): " value
  echo ""
  echo "${value}"
}

# ─── Helper: prompt for a variable value ──────────────────────────────────────
prompt_variable() {
  local name="$1"
  local description="$2"
  local default_val="${3:-}"
  local value=""

  echo ""
  echo -e "  ${BOLD}${name}${RESET}"
  echo "  ${description}"
  [[ -n "${default_val}" ]] && echo -e "  ${YELLOW}Default: ${default_val}${RESET}"

  read -rp "  Value [${default_val}]: " value
  echo "${value:-${default_val}}"
}

# =============================================================================
# SECTION 1 — AI Review (ai-review.yml)
# =============================================================================
header "AI Review — ai-review.yml"
echo ""
echo "  The AI Review workflow uses GitHub Models to provide automated code"
echo "  review on pull requests. It requires a PAT with models:read scope."

MODELS_PAT_VAL=$(prompt_secret \
  "MODELS_PAT" \
  "GitHub PAT with 'models:read' scope for GitHub Models API." \
  "github_pat_11A...")
set_secret "MODELS_PAT" "${MODELS_PAT_VAL}"
MODELS_PAT_VAL=""

echo ""
info "AI Review model variables (all have built-in defaults — press Enter to use defaults)"

REVIEW_MODEL_VAL=$(prompt_variable \
  "REVIEW_MODEL" \
  "Primary model for AI code review." \
  "openai/gpt-4.1")
set_variable "REVIEW_MODEL" "${REVIEW_MODEL_VAL}"

REVIEW_FALLBACK_MODEL_VAL=$(prompt_variable \
  "REVIEW_FALLBACK_MODEL" \
  "Fallback model if primary is unavailable." \
  "openai/gpt-4o")
set_variable "REVIEW_FALLBACK_MODEL" "${REVIEW_FALLBACK_MODEL_VAL}"

REVIEW_FALLBACK_MODEL_2_VAL=$(prompt_variable \
  "REVIEW_FALLBACK_MODEL_2" \
  "Second fallback model." \
  "meta/llama-4-maverick-17b-128e-instruct-fp8")
set_variable "REVIEW_FALLBACK_MODEL_2" "${REVIEW_FALLBACK_MODEL_2_VAL}"

REVIEW_LONG_CONTEXT_MODEL_VAL=$(prompt_variable \
  "REVIEW_LONG_CONTEXT_MODEL" \
  "Long-context model for large diffs." \
  "openai/gpt-4.1")
set_variable "REVIEW_LONG_CONTEXT_MODEL" "${REVIEW_LONG_CONTEXT_MODEL_VAL}"

REVIEW_AB_MODE_VAL=$(prompt_variable \
  "REVIEW_AB_MODE" \
  "A/B model comparison mode (off or parity)." \
  "off")
set_variable "REVIEW_AB_MODE" "${REVIEW_AB_MODE_VAL}"

# =============================================================================
# SECTION 2 — Deployment (deploy.yml)
# =============================================================================
header "Deployment — deploy.yml"
echo ""
echo "  The deploy workflow installs the specify-cli on a remote VM via SSH."
echo "  Skip this section if you do not have a deployment VM."
echo ""
read -rp "  Configure deployment secrets? [y/N]: " SETUP_DEPLOY
SETUP_DEPLOY="${SETUP_DEPLOY:-n}"

if [[ "${SETUP_DEPLOY,,}" == "y" ]]; then
  DEPLOY_SSH_KEY_VAL=$(prompt_secret \
    "DEPLOY_SSH_KEY" \
    "Private SSH key (Ed25519/RSA) for connecting to the deployment VM." \
    "-----BEGIN OPENSSH PRIVATE KEY-----")
  set_secret "DEPLOY_SSH_KEY" "${DEPLOY_SSH_KEY_VAL}"
  DEPLOY_SSH_KEY_VAL=""

  DEPLOY_VM_HOST_VAL=$(prompt_secret \
    "DEPLOY_VM_HOST" \
    "Hostname or IP address of the deployment VM." \
    "vm.example.com")
  set_secret "DEPLOY_VM_HOST" "${DEPLOY_VM_HOST_VAL}"
  DEPLOY_VM_HOST_VAL=""

  DEPLOY_VM_USER_VAL=$(prompt_secret \
    "DEPLOY_VM_USER" \
    "SSH username for connecting to the deployment VM." \
    "ubuntu")
  set_secret "DEPLOY_VM_USER" "${DEPLOY_VM_USER_VAL}"
  DEPLOY_VM_USER_VAL=""

  DEPLOY_VM_PORT_VAL=$(prompt_variable \
    "DEPLOY_VM_PORT" \
    "SSH port for the deployment VM." \
    "22")
  set_variable "DEPLOY_VM_PORT" "${DEPLOY_VM_PORT_VAL}"

  DEPLOY_VM_HOST_FINGERPRINT_VAL=$(prompt_variable \
    "DEPLOY_VM_HOST_FINGERPRINT" \
    "Expected SSH host fingerprint (format: SHA256:...)." \
    "")
  set_variable "DEPLOY_VM_HOST_FINGERPRINT" "${DEPLOY_VM_HOST_FINGERPRINT_VAL}"

  DEPLOY_VM_KNOWN_HOSTS_VAL=$(prompt_variable \
    "DEPLOY_VM_KNOWN_HOSTS" \
    "Full known_hosts entry for the VM (format: hostname algorithm key)." \
    "")
  set_variable "DEPLOY_VM_KNOWN_HOSTS" "${DEPLOY_VM_KNOWN_HOSTS_VAL}"
else
  info "Skipping deployment configuration."
fi

# =============================================================================
# SECTION 3 — Google Drive Backup (backup-gdrive.yml)
# =============================================================================
header "Google Drive Backup — backup-gdrive.yml"
echo ""
echo "  The backup workflow uploads release assets to Google Drive."
echo "  Skip this section if you do not want automated backups."
echo ""
read -rp "  Configure Google Drive backup secrets? [y/N]: " SETUP_GDRIVE
SETUP_GDRIVE="${SETUP_GDRIVE:-n}"

if [[ "${SETUP_GDRIVE,,}" == "y" ]]; then
  echo ""
  echo "  How to obtain Google OAuth credentials:"
  echo "  1. Go to https://console.cloud.google.com/"
  echo "  2. Create a project and enable the Google Drive API"
  echo "  3. Create OAuth 2.0 credentials (Desktop application)"
  echo "  4. Use the OAuth 2.0 Playground to obtain a refresh token"
  echo "     https://developers.google.com/oauthplayground"
  echo "     (Scope: https://www.googleapis.com/auth/drive.file)"
  echo ""

  GDRIVE_OAUTH_CLIENT_ID_VAL=$(prompt_secret \
    "GDRIVE_OAUTH_CLIENT_ID" \
    "Google OAuth 2.0 client ID." \
    "123456789-abc.apps.googleusercontent.com")
  set_secret "GDRIVE_OAUTH_CLIENT_ID" "${GDRIVE_OAUTH_CLIENT_ID_VAL}"
  GDRIVE_OAUTH_CLIENT_ID_VAL=""

  GDRIVE_OAUTH_CLIENT_SECRET_VAL=$(prompt_secret \
    "GDRIVE_OAUTH_CLIENT_SECRET" \
    "Google OAuth 2.0 client secret." \
    "GOCSPX-...")
  set_secret "GDRIVE_OAUTH_CLIENT_SECRET" "${GDRIVE_OAUTH_CLIENT_SECRET_VAL}"
  GDRIVE_OAUTH_CLIENT_SECRET_VAL=""

  GDRIVE_OAUTH_REFRESH_TOKEN_VAL=$(prompt_secret \
    "GDRIVE_OAUTH_REFRESH_TOKEN" \
    "Long-lived OAuth 2.0 refresh token for Drive uploads." \
    "1//0g...")
  set_secret "GDRIVE_OAUTH_REFRESH_TOKEN" "${GDRIVE_OAUTH_REFRESH_TOKEN_VAL}"
  GDRIVE_OAUTH_REFRESH_TOKEN_VAL=""

  GDRIVE_BACKUP_FOLDER_ID_VAL=$(prompt_variable \
    "GDRIVE_BACKUP_FOLDER_ID" \
    "Google Drive folder ID where backups are uploaded." \
    "")
  set_variable "GDRIVE_BACKUP_FOLDER_ID" "${GDRIVE_BACKUP_FOLDER_ID_VAL}"

  GDRIVE_BACKUP_RETENTION_COUNT_VAL=$(prompt_variable \
    "GDRIVE_BACKUP_RETENTION_COUNT" \
    "Number of backup sets to retain." \
    "30")
  set_variable "GDRIVE_BACKUP_RETENTION_COUNT" "${GDRIVE_BACKUP_RETENTION_COUNT_VAL}"
else
  info "Skipping Google Drive backup configuration."
fi

# =============================================================================
# DONE
# =============================================================================
header "Setup complete"
echo ""

if [[ "${DRY_RUN}" == "true" ]]; then
  warn "Dry run — no changes were made. Remove --dry-run to apply."
else
  success "Repository secrets and variables have been configured."
  echo ""
  echo "  Next steps:"
  echo "  1. Verify at: https://github.com/${REPO}/settings/secrets/actions"
  echo "  2. Trigger the AI Review workflow by opening a PR"
  echo "  3. See docs/repository-admin-guide.md for full configuration reference"
fi
