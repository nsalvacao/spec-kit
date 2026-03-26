# =============================================================================
# ops/setup-repository.ps1
#
# Interactive setup script that configures all required GitHub Actions secrets
# and variables for this repository using a privileged Personal Access Token.
#
# The Copilot coding agent cannot manage secrets/variables directly (its token
# lacks the required GitHub App permissions). Run this script once, locally,
# with an admin PAT to set everything up.
#
# Usage:
#   $env:GH_ADMIN_TOKEN = "<your-PAT>"
#   .\ops\setup-repository.ps1 [-DryRun]
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

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

$Repo = 'nsalvacao/spec-kit'

# ─── Colours ──────────────────────────────────────────────────────────────────
function Write-Info    { param($Msg) Write-Host "ℹ  $Msg" -ForegroundColor Cyan }
function Write-Success { param($Msg) Write-Host "✅ $Msg" -ForegroundColor Green }
function Write-Warn    { param($Msg) Write-Host "⚠  $Msg" -ForegroundColor Yellow }
function Write-Err     { param($Msg) Write-Host "❌ $Msg" -ForegroundColor Red }
function Write-Header  { param($Msg) Write-Host "`n═══ $Msg ═══" -ForegroundColor Cyan }

# ─── Help ──────────────────────────────────────────────────────────────────────
if ($Help) {
    Write-Host @"
Usage: .\ops\setup-repository.ps1 [-DryRun]

  -DryRun    Show what would be configured without making changes

Environment variables required:
  GH_ADMIN_TOKEN   GitHub PAT with secrets/variables write access
"@
    exit 0
}

# ─── Pre-flight checks ────────────────────────────────────────────────────────
Write-Header 'Pre-flight checks'

$AdminToken = $env:GH_ADMIN_TOKEN
if (-not $AdminToken) {
    Write-Err 'GH_ADMIN_TOKEN is not set.'
    Write-Host ''
    Write-Host '  Create a fine-grained PAT at:'
    Write-Host '  https://github.com/settings/personal-access-tokens'
    Write-Host ''
    Write-Host '  Required repository permissions:'
    Write-Host '    Actions secrets: Read and write'
    Write-Host '    Actions variables: Read and write'
    Write-Host '    Administration: Read and write'
    Write-Host '    Environments: Read and write'
    Write-Host ''
    Write-Host '  Then: $env:GH_ADMIN_TOKEN = "<your-PAT>"'
    exit 1
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Err 'GitHub CLI (gh) is not installed.'
    Write-Host '  Install: https://cli.github.com/'
    exit 1
}

$env:GH_TOKEN = $AdminToken

try {
    $null = gh api "repos/$Repo" --jq '.full_name' 2>&1
    Write-Success "Token validated — has access to $Repo"
} catch {
    Write-Err "GH_ADMIN_TOKEN cannot access the repository $Repo."
    Write-Host '  Check that the token has the correct repository permissions.'
    exit 1
}

if ($DryRun) {
    Write-Warn 'DRY RUN mode — no changes will be made'
}

# ─── Helper: set a secret ─────────────────────────────────────────────────────
function Set-RepoSecret {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Description = ''
    )

    if (-not $Value) {
        Write-Warn "Skipping secret $Name — no value provided"
        return
    }

    if ($DryRun) {
        Write-Info "[dry-run] Would set secret: $Name"
        return
    }

    try {
        $Value | gh secret set $Name --repo $Repo 2>&1 | Out-Null
        Write-Success "Set secret: $Name"
    } catch {
        Write-Err "Failed to set secret: $Name"
        throw
    }
}

# ─── Helper: set a variable ───────────────────────────────────────────────────
function Set-RepoVariable {
    param(
        [string]$Name,
        [string]$Value
    )

    if (-not $Value) {
        Write-Warn "Skipping variable $Name — no value provided"
        return
    }

    if ($DryRun) {
        Write-Info "[dry-run] Would set variable: $Name = $Value"
        return
    }

    try {
        gh variable set $Name --repo $Repo --body $Value 2>&1 | Out-Null
        Write-Success "Set variable: $Name = $Value"
    } catch {
        Write-Err "Failed to set variable: $Name"
        throw
    }
}

# ─── Helper: prompt for a secret ──────────────────────────────────────────────
function Read-Secret {
    param(
        [string]$Name,
        [string]$Description,
        [string]$Example = ''
    )

    Write-Host ''
    Write-Host "  $Name" -ForegroundColor White
    Write-Host "  $Description"
    if ($Example) {
        Write-Host "  Example: $Example" -ForegroundColor Yellow
    }

    $SecureValue = Read-Host '  Value (empty to skip)' -AsSecureString
    $Bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($Bstr)
    } finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    }
}

# ─── Helper: prompt for a variable ────────────────────────────────────────────
function Read-Variable {
    param(
        [string]$Name,
        [string]$Description,
        [string]$DefaultVal = ''
    )

    Write-Host ''
    Write-Host "  $Name" -ForegroundColor White
    Write-Host "  $Description"
    if ($DefaultVal) {
        Write-Host "  Default: $DefaultVal" -ForegroundColor Yellow
    }

    $Value = Read-Host "  Value [$DefaultVal]"
    if (-not $Value) { return $DefaultVal }
    return $Value
}

# =============================================================================
# SECTION 1 — AI Review (ai-review.yml)
# =============================================================================
Write-Header 'AI Review — ai-review.yml'
Write-Host ''
Write-Host '  The AI Review workflow uses GitHub Models to provide automated code'
Write-Host '  review on pull requests. It requires a PAT with models:read scope.'

$ModelsPat = Read-Secret `
    -Name 'MODELS_PAT' `
    -Description "GitHub PAT with 'models:read' scope for GitHub Models API." `
    -Example 'github_pat_11A...'
Set-RepoSecret -Name 'MODELS_PAT' -Value $ModelsPat

Write-Host ''
Write-Info 'AI Review model variables (all have built-in defaults — press Enter to use defaults)'

$ReviewModel = Read-Variable `
    -Name 'REVIEW_MODEL' `
    -Description 'Primary model for AI code review.' `
    -DefaultVal 'openai/gpt-4.1'
Set-RepoVariable -Name 'REVIEW_MODEL' -Value $ReviewModel

$ReviewFallback = Read-Variable `
    -Name 'REVIEW_FALLBACK_MODEL' `
    -Description 'Fallback model if primary is unavailable.' `
    -DefaultVal 'openai/gpt-4o'
Set-RepoVariable -Name 'REVIEW_FALLBACK_MODEL' -Value $ReviewFallback

$ReviewFallback2 = Read-Variable `
    -Name 'REVIEW_FALLBACK_MODEL_2' `
    -Description 'Second fallback model.' `
    -DefaultVal 'meta/llama-4-maverick-17b-128e-instruct-fp8'
Set-RepoVariable -Name 'REVIEW_FALLBACK_MODEL_2' -Value $ReviewFallback2

$ReviewLongContext = Read-Variable `
    -Name 'REVIEW_LONG_CONTEXT_MODEL' `
    -Description 'Long-context model for large diffs.' `
    -DefaultVal 'openai/gpt-4.1'
Set-RepoVariable -Name 'REVIEW_LONG_CONTEXT_MODEL' -Value $ReviewLongContext

$ReviewAbMode = Read-Variable `
    -Name 'REVIEW_AB_MODE' `
    -Description 'A/B model comparison mode (off or parity).' `
    -DefaultVal 'off'
Set-RepoVariable -Name 'REVIEW_AB_MODE' -Value $ReviewAbMode

# =============================================================================
# SECTION 2 — Deployment (deploy.yml)
# =============================================================================
Write-Header 'Deployment — deploy.yml'
Write-Host ''
Write-Host '  The deploy workflow installs the specify-cli on a remote VM via SSH.'
Write-Host '  Skip this section if you do not have a deployment VM.'
Write-Host ''
$SetupDeploy = Read-Host '  Configure deployment secrets? [y/N]'

if ($SetupDeploy -eq 'y' -or $SetupDeploy -eq 'Y') {
    $DeployKey = Read-Secret `
        -Name 'DEPLOY_SSH_KEY' `
        -Description 'Private SSH key (Ed25519/RSA) for connecting to the deployment VM.' `
        -Example '-----BEGIN OPENSSH PRIVATE KEY-----'
    Set-RepoSecret -Name 'DEPLOY_SSH_KEY' -Value $DeployKey

    $DeployHost = Read-Secret `
        -Name 'DEPLOY_VM_HOST' `
        -Description 'Hostname or IP address of the deployment VM.' `
        -Example 'vm.example.com'
    Set-RepoSecret -Name 'DEPLOY_VM_HOST' -Value $DeployHost

    $DeployUser = Read-Secret `
        -Name 'DEPLOY_VM_USER' `
        -Description 'SSH username for connecting to the deployment VM.' `
        -Example 'ubuntu'
    Set-RepoSecret -Name 'DEPLOY_VM_USER' -Value $DeployUser

    $DeployPort = Read-Variable `
        -Name 'DEPLOY_VM_PORT' `
        -Description 'SSH port for the deployment VM.' `
        -DefaultVal '22'
    Set-RepoVariable -Name 'DEPLOY_VM_PORT' -Value $DeployPort

    $DeployFingerprint = Read-Variable `
        -Name 'DEPLOY_VM_HOST_FINGERPRINT' `
        -Description 'Expected SSH host fingerprint (format: SHA256:...).' `
        -DefaultVal ''
    Set-RepoVariable -Name 'DEPLOY_VM_HOST_FINGERPRINT' -Value $DeployFingerprint

    $DeployKnownHosts = Read-Variable `
        -Name 'DEPLOY_VM_KNOWN_HOSTS' `
        -Description 'Full known_hosts entry for the VM (format: hostname algorithm key).' `
        -DefaultVal ''
    Set-RepoVariable -Name 'DEPLOY_VM_KNOWN_HOSTS' -Value $DeployKnownHosts
} else {
    Write-Info 'Skipping deployment configuration.'
}

# =============================================================================
# SECTION 3 — Google Drive Backup (backup-gdrive.yml)
# =============================================================================
Write-Header 'Google Drive Backup — backup-gdrive.yml'
Write-Host ''
Write-Host '  The backup workflow uploads release assets to Google Drive.'
Write-Host '  Skip this section if you do not want automated backups.'
Write-Host ''
$SetupGDrive = Read-Host '  Configure Google Drive backup secrets? [y/N]'

if ($SetupGDrive -eq 'y' -or $SetupGDrive -eq 'Y') {
    Write-Host ''
    Write-Host '  How to obtain Google OAuth credentials:'
    Write-Host '  1. Go to https://console.cloud.google.com/'
    Write-Host '  2. Create a project and enable the Google Drive API'
    Write-Host '  3. Create OAuth 2.0 credentials (Desktop application)'
    Write-Host '  4. Use the OAuth 2.0 Playground to obtain a refresh token'
    Write-Host '     https://developers.google.com/oauthplayground'
    Write-Host '     (Scope: https://www.googleapis.com/auth/drive.file)'
    Write-Host ''

    $GDriveClientId = Read-Secret `
        -Name 'GDRIVE_OAUTH_CLIENT_ID' `
        -Description 'Google OAuth 2.0 client ID.' `
        -Example '123456789-abc.apps.googleusercontent.com'
    Set-RepoSecret -Name 'GDRIVE_OAUTH_CLIENT_ID' -Value $GDriveClientId

    $GDriveClientSecret = Read-Secret `
        -Name 'GDRIVE_OAUTH_CLIENT_SECRET' `
        -Description 'Google OAuth 2.0 client secret.' `
        -Example 'GOCSPX-...'
    Set-RepoSecret -Name 'GDRIVE_OAUTH_CLIENT_SECRET' -Value $GDriveClientSecret

    $GDriveRefreshToken = Read-Secret `
        -Name 'GDRIVE_OAUTH_REFRESH_TOKEN' `
        -Description 'Long-lived OAuth 2.0 refresh token for Drive uploads.' `
        -Example '1//0g...'
    Set-RepoSecret -Name 'GDRIVE_OAUTH_REFRESH_TOKEN' -Value $GDriveRefreshToken

    $GDriveFolderId = Read-Variable `
        -Name 'GDRIVE_BACKUP_FOLDER_ID' `
        -Description 'Google Drive folder ID where backups are uploaded.' `
        -DefaultVal ''
    Set-RepoVariable -Name 'GDRIVE_BACKUP_FOLDER_ID' -Value $GDriveFolderId

    $GDriveRetention = Read-Variable `
        -Name 'GDRIVE_BACKUP_RETENTION_COUNT' `
        -Description 'Number of backup sets to retain.' `
        -DefaultVal '30'
    Set-RepoVariable -Name 'GDRIVE_BACKUP_RETENTION_COUNT' -Value $GDriveRetention
} else {
    Write-Info 'Skipping Google Drive backup configuration.'
}

# =============================================================================
# DONE
# =============================================================================
Write-Header 'Setup complete'
Write-Host ''

if ($DryRun) {
    Write-Warn 'Dry run — no changes were made. Remove -DryRun to apply.'
} else {
    Write-Success 'Repository secrets and variables have been configured.'
    Write-Host ''
    Write-Host '  Next steps:'
    Write-Host "  1. Verify at: https://github.com/$Repo/settings/secrets/actions"
    Write-Host '  2. Trigger the AI Review workflow by opening a PR'
    Write-Host '  3. See docs/repository-admin-guide.md for full configuration reference'
}
