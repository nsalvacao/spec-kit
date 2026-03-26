# Repository Administration Guide

This document answers a key operational question:

> **As a Copilot coding agent, can I configure repository settings (secrets,
> environments, branch protection, etc.) — not just code?**

The short answer is **partially**. This guide explains exactly what the agent
can and cannot do, why the boundary exists, and what tooling or MCP servers you
should provide to close the gap.

---

## What the Copilot Coding Agent CAN Do

The Copilot coding agent operates with a `ghu_` user-on-behalf-of token that
has been granted a narrow set of GitHub App permissions. Within those limits it
can:

| Category | Operations |
|----------|-----------|
| **Repository content** | Create, edit, and delete files; commit to branches; push to PRs |
| **Pull requests** | Open, update, merge, and comment on PRs |
| **Issues** | Create, update, comment, and close issues |
| **Releases & tags** | Read releases; read git tags |
| **Environments** | Read environment metadata and protection rules |
| **Rulesets** | Read repository rulesets (branch protection) |
| **Pages** | Read GitHub Pages configuration |
| **Collaborators** | Read collaborator list |
| **Actions workflows** | Read workflow definitions and run history |
| **OIDC** | Read OIDC sub-claim customisation |

## What the Copilot Coding Agent CANNOT Do

These operations return `HTTP 403 Resource not accessible by integration`
because they require permissions the GitHub Copilot App has not been granted:

| Category | Operations blocked |
|----------|-------------------|
| **Secrets** | Read, create, or update Actions secrets |
| **Variables** | Read, create, or update repository/environment variables |
| **Repository settings** | Update description, merge strategy, auto-merge, topics, etc. |
| **Rulesets** | Create, update, or delete branch protection rulesets |
| **Branch protection** | Classic branch protection rules (legacy endpoint) |
| **Webhooks** | List, create, update, or delete webhooks |
| **Dependabot** | View or dismiss Dependabot alerts |
| **Code scanning** | View or dismiss code scanning alerts |
| **Workflow dispatch** | Trigger `workflow_dispatch` events |
| **Collaborators** | Add or remove collaborators |
| **GitHub Projects** | Create or manage classic Projects |
| **Labels** | Create, update, or delete labels |
| **OIDC** | Update OIDC sub-claim customisation |

### Why this boundary exists

The Copilot coding agent token is intentionally scoped this way. Secrets
management and repository administration are security-sensitive operations that
GitHub deliberately excludes from the set of capabilities it grants to AI
agents by default. This prevents a compromised or misbehaving agent from
exfiltrating credentials or weakening security controls.

---

## Required Configuration for This Repository

The following settings must be configured manually (by the repository owner) or
via a privileged automation tool (see [Tooling Recommendations](#tooling-recommendations)).

### Actions Secrets

Navigate to **Settings → Secrets and variables → Actions → Secrets**.

| Secret name | Required by | Description |
|-------------|------------|-------------|
| `MODELS_PAT` | `ai-review.yml` | GitHub Personal Access Token with `models:read` scope. Used to call the GitHub Models API for AI code review. |
| `DEPLOY_SSH_KEY` | `deploy.yml` | Private SSH key (Ed25519 or RSA) whose public key is installed on the deployment VM. |
| `DEPLOY_VM_HOST` | `deploy.yml` | Hostname or IP address of the deployment VM. |
| `DEPLOY_VM_USER` | `deploy.yml` | SSH username used to connect to the deployment VM. |
| `GDRIVE_OAUTH_CLIENT_ID` | `backup-gdrive.yml` | Google OAuth 2.0 client ID for Drive API access. |
| `GDRIVE_OAUTH_CLIENT_SECRET` | `backup-gdrive.yml` | Google OAuth 2.0 client secret. |
| `GDRIVE_OAUTH_REFRESH_TOKEN` | `backup-gdrive.yml` | Long-lived OAuth 2.0 refresh token for non-interactive Drive uploads. |

### Actions Variables

Navigate to **Settings → Secrets and variables → Actions → Variables**.

| Variable name | Required by | Default | Description |
|---------------|------------|---------|-------------|
| `REVIEW_MODEL` | `ai-review.yml` | `openai/gpt-4.1` | Primary model for AI review. |
| `REVIEW_FALLBACK_MODEL` | `ai-review.yml` | `openai/gpt-4o` | Fallback model if primary is unavailable. |
| `REVIEW_FALLBACK_MODEL_2` | `ai-review.yml` | `meta/llama-4-maverick-17b-128e-instruct-fp8` | Second fallback model. |
| `REVIEW_LONG_CONTEXT_MODEL` | `ai-review.yml` | `openai/gpt-4.1` | Long-context model for large diffs. |
| `REVIEW_AB_MODE` | `ai-review.yml` | `off` | Enable A/B model comparison (`off` or `parity`). |
| `REVIEW_AB_MODELS` | `ai-review.yml` | *(empty)* | Comma-separated model IDs for A/B pool. |
| `DEPLOY_VM_PORT` | `deploy.yml` | `22` | SSH port for the deployment VM. |
| `DEPLOY_VM_HOST_FINGERPRINT` | `deploy.yml` | *(none)* | Expected SSH host fingerprint (e.g. `SHA256:…`). |
| `DEPLOY_VM_KNOWN_HOSTS` | `deploy.yml` | *(none)* | Full `known_hosts` entry for the VM. |
| `GDRIVE_BACKUP_FOLDER_ID` | `backup-gdrive.yml` | *(required)* | Google Drive folder ID where backups are uploaded. |
| `GDRIVE_BACKUP_RETENTION_COUNT` | `backup-gdrive.yml` | `30` | How many release backup sets to retain. |

### Existing Environments

The repository has two environments pre-configured:

| Environment | Purpose |
|-------------|---------|
| `copilot` | Used by the Copilot coding agent. |
| `github-pages` | Used by the GitHub Pages deployment workflow. |

---

## Tooling Recommendations

To enable the Copilot coding agent (or any automation) to manage these settings
programmatically, you need one or more of the following approaches:

### Option 1 — Fine-Grained PAT as MCP Server Configuration (Recommended)

Configure an additional MCP server instance that authenticates with a
**fine-grained Personal Access Token** scoped to this repository with elevated
permissions. The existing `github-mcp-server` already supports this — you just
need to run a second instance with a privileged token and expose it to the
agent.

**Steps:**

1. Create a fine-grained PAT at
   [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)
   with these repository permissions:

   | Permission | Access |
   |-----------|--------|
   | Actions secrets | Read and write |
   | Actions variables | Read and write |
   | Administration | Read and write |
   | Environments | Read and write |
   | Webhooks | Read and write |
   | Contents | Read and write |
   | Pull requests | Read and write |
   | Issues | Read and write |

2. Add a second MCP server entry in your Copilot/IDE configuration:

   ```json
   {
     "mcpServers": {
       "github-admin": {
         "command": "docker",
         "args": ["run", "-i", "--rm",
           "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
           "ghcr.io/github/github-mcp-server"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-fine-grained-PAT>"
         }
       }
     }
   }
   ```

   The agent can now call `github-admin` tools to manage secrets, variables,
   and settings, while the default `github` MCP server continues handling
   code operations.

### Option 2 — Terraform MCP Server (GitOps / Declarative Approach)

Use a Terraform MCP server with the
[GitHub Terraform Provider](https://registry.terraform.io/providers/integrations/github/latest)
to manage **all** repository settings as code. This gives you:

- Full audit trail via git history
- Declarative state (desired state always in code)
- Support for secrets, variables, branch protection, webhooks, environments,
  and more

**MCP servers to add:**

```json
{
  "mcpServers": {
    "terraform": {
      "command": "npx",
      "args": ["-y", "@hashicorp/terraform-mcp-server"]
    }
  }
}
```

The agent can then write and apply Terraform configurations like:

```hcl
resource "github_actions_secret" "models_pat" {
  repository      = "spec-kit"
  secret_name     = "MODELS_PAT"
  plaintext_value = var.models_pat
}

resource "github_actions_variable" "review_model" {
  repository    = "spec-kit"
  variable_name = "REVIEW_MODEL"
  value         = "openai/gpt-4.1"
}
```

### Option 3 — Local Setup Script (Quick Start)

Run the included setup script with a privileged PAT to configure all required
secrets and variables in one shot:

```bash
# Bash (Linux / macOS)
export GH_ADMIN_TOKEN="<your-classic-or-fine-grained-PAT>"
./ops/setup-repository.sh

# PowerShell (Windows / cross-platform)
$env:GH_ADMIN_TOKEN = "<your-classic-or-fine-grained-PAT>"
./ops/setup-repository.ps1
```

See [`ops/setup-repository.sh`](../ops/setup-repository.sh) and
[`ops/setup-repository.ps1`](../ops/setup-repository.ps1) for full details.

### Option 4 — Expand Copilot App Permissions (Limited)

GitHub allows repository owners to grant additional permissions to the Copilot
GitHub App via **Settings → GitHub Copilot → Policies**. However, as of the
current release, GitHub does not expose secrets write permissions to the
Copilot App regardless of configuration — this is a platform-level security
boundary, not a repository configuration issue.

This option may become available as Copilot's agent capabilities evolve.

---

## Quick Reference: What Needs a Privileged Token

```text
│ CAN be done by Copilot agent (default token)                    │
│  ✅ Code changes, PRs, issues, reading all settings             │
│                                                                 │
│ REQUIRES privileged token (PAT / admin MCP server)             │
│  🔑 Set/update Actions secrets                                  │
│  🔑 Set/update Actions variables                               │
│  🔑 Set/update environment secrets/variables                   │
│  🔑 Update repository settings (merge strategy, topics, etc.)  │
│  🔑 Create/update/delete branch protection rulesets            │
│  🔑 Create/update/delete webhooks                              │
│  🔑 Trigger workflow_dispatch events                           │
│  🔑 Manage collaborators                                       │
│  🔑 Manage labels                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## See Also

- [`docs/backup-google-drive.md`](backup-google-drive.md) — Google Drive
  backup configuration details
- [`ops/setup-repository.sh`](../ops/setup-repository.sh) — Automated setup
  script
- [GitHub MCP Server](https://github.com/github/github-mcp-server) — Official
  GitHub MCP server
- [GitHub Terraform Provider](https://registry.terraform.io/providers/integrations/github/latest)
  — Full repository management via Terraform
- [Copilot Coding Agent docs](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent-to-work-on-tasks)
  — Official Copilot agent documentation
