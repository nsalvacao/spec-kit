# External Baseline Integration Traceability

This project treats external plugins as design baselines, then migrates useful
capabilities into native, first-party functionality.

## Integration Contract

- External locations (for example
  `~/.copilot/installed-plugins/nsalvacao-claude-code-plugins/...`) are
  reference-only.
- Runtime logic must live in this repository (`src/`, `scripts/`,
  `templates/commands/`, workflows).
- New integrations are tracked as explicit issues/PRs with tests and docs.

## Capability Matrix

| Baseline capability | Native implementation target | Tracking issue | Status |
| --- | --- | --- | --- |
| One branch per feature execution unit | `scripts/python/branch-policy.py` + create-feature scripts + docs/tests | [#108](https://github.com/nsalvacao/spec-kit/issues/108) | In hardening/closure |
| Single canonical tasks artifact (`specs/<feature>/tasks.md`) | `scripts/python/task-artifact-policy.py` + tests | [#109](https://github.com/nsalvacao/spec-kit/issues/109) | Delivered |
| Productivity start flow parity (A1 bootstrap + launch) | `specify productivity start` + `src/specify_cli/productivity*.py` + tests | [#200](https://github.com/nsalvacao/spec-kit/issues/200) | Delivered |
| Productivity update flow parity (A2 default + comprehensive) | `specify productivity update` + task sync/stale/memory proposal engine + tests | [#201](https://github.com/nsalvacao/spec-kit/issues/201) | Delivered |
| Productivity config + safety parity (A4 schema/guards) | `.cockpit.json` contract + path sandboxing + runtime tuning in project config | [#203](https://github.com/nsalvacao/spec-kit/issues/203) | In progress |
| Cockpit feature binding to active feature tasks | CLI/state + dashboard binding | [#110](https://github.com/nsalvacao/spec-kit/issues/110) | Planned |
| Guided orchestration across Layers 0-4 | Wizard/orchestrator in native CLI flow | [#111](https://github.com/nsalvacao/spec-kit/issues/111) | Planned |
| TTY/TUI concise orchestration adapter | Native TTY/TUI prompts and payload parity | [#112](https://github.com/nsalvacao/spec-kit/issues/112) | Planned |
| Programmatic orchestration payload contract | `src/specify_cli/orchestration_contract.py` + docs/tests | [#113](https://github.com/nsalvacao/spec-kit/issues/113) | Delivered |
| Instruction contract for templates/scripts | `templates/commands/*` + validation behavior | [#115](https://github.com/nsalvacao/spec-kit/issues/115) | Delivered |
| Handoff metadata schema and validation gate | `tests/test_handoff_metadata.py` + contracts/docs | [#116](https://github.com/nsalvacao/spec-kit/issues/116) | Delivered |

## Verification Guardrail

Runtime code must not reference external plugin installation paths directly.
Automated guard:

- `tests/test_runtime_nativity_guard.py`
