# Template/Script Instruction Contract (v1)

Issue: `#115`

This document defines the normative instruction contract used by command
templates and helper scripts so agent behavior stays consistent across providers.

- Module: `src/specify_cli/template_instruction_contract.py`
- Validator script: `scripts/python/template-instruction-contract.py`
- Cross-platform wrappers:
  - `scripts/bash/template-instruction-contract.sh`
  - `scripts/powershell/template-instruction-contract.ps1`

## Required markers

Templates must include all markers below:

- `instruction-contract:options`
- `instruction-contract:recommended-default`
- `instruction-contract:risk-confirmation`
- `instruction-contract:canonical-write-paths`
- `instruction-contract:machine-readable-output`

## Normative behavior

- Always present explicit options when multiple valid paths exist.
- Provide one recommended default with rationale before alternatives.
- Require explicit confirmation for risky overrides.
- Write only to canonical artifact paths.
- Keep outputs parseable for orchestration gates and handoffs.

## Current coverage

Validated templates:

- `templates/commands/specify.md`
- `templates/commands/clarify.md`
- `templates/commands/plan.md`
- `templates/commands/tasks.md`

## Local usage

```bash
python3 scripts/python/template-instruction-contract.py validate --repo-root .
```

```bash
scripts/bash/template-instruction-contract.sh validate --repo-root .
```

```powershell
./scripts/powershell/template-instruction-contract.ps1 validate --repo-root .
```
