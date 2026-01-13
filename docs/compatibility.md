# Compatibility Policy

This fork aims to stay compatible with upstream `github/spec-kit` while adding Phase 0 enhancements.

## Supported Upstream Versions

- Compatible with upstream `main` at the time of each fork release
- Fork releases will note the upstream commit or tag they are based on

## Compatibility Guarantees

- Fork templates are the default when using this forked CLI
- Upstream templates remain available via `SPECIFY_TEMPLATE_REPO=github/spec-kit`
- Fork changes are additive and avoid breaking upstream workflows
- Phase 0 is a recommended prerequisite that preserves `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`

## Sync Expectations

When upstream updates:

1. Merge or rebase upstream into the fork
2. Re-validate fork templates and scripts
3. Update documentation as needed
