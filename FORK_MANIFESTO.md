# Fork Manifesto

This repository is an independent fork of `github/spec-kit` that adds **Phase 0: AI System Ideation** (IDEATE → SELECT → STRUCTURE → VALIDATE) while preserving upstream compatibility and workflows.

## Why This Fork Exists

- Introduce a structured pre-spec workflow for AI systems before `/speckit.constitution`
- Provide validated templates, checks, and scripts without breaking upstream behavior
- Keep a clean, sync-friendly extension path for long-term maintenance

## Compatibility Commitments

- **Default behavior uses fork**: when `SPECIFY_TEMPLATE_REPO` is unset, `specify init` pulls templates from `nsalvacao/spec-kit`
- **Opt-in upstream templates**: set `SPECIFY_TEMPLATE_REPO=github/spec-kit` or use `--template-repo github/spec-kit` to use upstream templates instead
- **Minimal divergence**: changes are additive and isolated to templates, scripts, and documented overrides

## Upstream Alignment Strategy

- Track upstream `main` regularly and rebase/merge changes safely
- Contribute improvements upstream when applicable
- Maintain a compatibility note for supported upstream versions

## Governance and Scope

- **Not affiliated with GitHub**
- MIT license preserved with attribution
- Focused on high-quality, reproducible workflows and documentation

## Roadmap

See `ROADMAP.md` and `.spec-kit/FUTURE_ENHANCEMENTS.md` for planned work.
