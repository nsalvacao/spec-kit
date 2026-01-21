<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit (Fork)</h1>
    <h3><em>Build high-quality software faster — now with Phase 0 AI Ideation built in.</em></h3>
</div>

<p align="center">
    <strong>A fork of GitHub Spec Kit that adds Phase 0 (AI System Ideation) as a first-class workflow prerequisite before Spec‑Driven Development.</strong>
</p>

<p align="center">
    <a href="https://github.com/nsalvacao/spec-kit/actions/workflows/release.yml"><img src="https://github.com/nsalvacao/spec-kit/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/nsalvacao/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/nsalvacao/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/nsalvacao/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/nsalvacao/spec-kit" alt="License"/></a>
    <a href="https://nsalvacao.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

---

## Table of Contents

- [🧭 Fork Notice](#-fork-notice)
- [🧠 Why Phase 0](#-why-phase-0)
- [🧩 Workflow Overview](#-workflow-overview)
- [⚡ Quickstart](#-quickstart)
- [📚 Docs & Guides](#-docs--guides)
- [🔧 Prerequisites](#-prerequisites)
- [🔁 Compatibility](#-compatibility)
- [📄 License](#-license)

## 🧭 Fork Notice

This repository is an independent fork of `github/spec-kit` with **Phase 0: AI System Ideation** integrated as a recommended prerequisite before the standard Spec‑Driven Development (SDD) workflow.

**Not affiliated with GitHub.**  
**License:** MIT (original copyright GitHub, Inc.) preserved.  
**Trademarks:** GitHub® and Spec Kit™ are used for attribution only (see `docs/trademarks.md`).

## 🧠 Why Phase 0

AI systems benefit from early ideation and validation before formal specifications. Phase 0 ensures you:

- Generate and evaluate multiple ideas before committing
- Select the strongest candidate with structured scoring
- Capture the rationale in reusable artifacts
- Validate feasibility early (Gate G0) before investing in specs

See `docs/methodology.md` for the full philosophy and methodology.

## 🧩 Workflow Overview

**Phase 0 (recommended prerequisite)**  
IDEATE → SELECT → STRUCTURE → VALIDATE

**Spec‑Driven Development (SDD)**  
CONSTITUTION → SPECIFY → PLAN → TASKS → IMPLEMENT

Full walkthrough: `docs/walkthrough.md`

## ⚡ Quickstart

### 1) Install the forked CLI

```bash
uv tool install specify-cli --from git+https://github.com/nsalvacao/spec-kit.git

```

### 2) Initialize a project

```bash
specify init my-project --ai codex
```

### 3) Run Phase 0 (recommended prerequisite)

```text
/speckit.ideate
/speckit.select
/speckit.structure
/speckit.validate

```

### 4) Continue with SDD

```text
/speckit.constitution
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement
```

For detailed guidance, see `docs/quickstart.md` and `docs/walkthrough.md`.

## 📚 Docs & Guides

- **Methodology**: `docs/methodology.md`
- **Walkthrough**: `docs/walkthrough.md`
- **Quickstart**: `docs/quickstart.md`
- **Installation**: `docs/installation.md`
- **CLI Reference**: `docs/cli.md`
- **Supported Agents**: `docs/agents.md`
- **Distribution**: `docs/distribution.md`
- **Compatibility**: `docs/compatibility.md`
- **Upstream Sync**: `docs/upstream-sync.md`

## 🔧 Prerequisites

- **Linux/macOS/Windows**
- **Python 3.11+**
- **uv** for package management
- **Git**
- **yq** (YAML edits)
- **ripgrep (rg)** (validation scripts)
- An AI coding agent (see `docs/agents.md`)

Full list: `docs/installation.md`

## 🔁 Compatibility

This fork stays compatible with upstream while adding Phase 0.

- Fork templates are the default
- Upstream templates can be used via override when needed

See `docs/compatibility.md` and `docs/distribution.md`.

## 📄 License

MIT License. See `LICENSE`.
