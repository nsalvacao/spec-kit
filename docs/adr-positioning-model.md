# ADR: Product Positioning Model

**Status:** Accepted
**Date:** 2026-03-02
**Issue:** [#179 Product identity strategy beyond fork positioning](https://github.com/nsalvacao/spec-kit/issues/179)

## Context

Nexo Spec Kit began as a fork of `github/spec-kit` adding Phase 0 AI ideation.
As the toolkit has grown — adding 17+ agent integrations, enterprise compliance
controls, contract validation modules, and a full release/deploy pipeline — the
"fork with Phase 0" framing no longer captures the product's scope or value.

We need a clear, ownable product identity that:

- differentiates Nexo Spec Kit from upstream on merit, not just heritage;
- retains optional upstream compatibility for teams that need it;
- supports enterprise adoption without creating confusion about affiliation.

## Options Evaluated

### Option A — Independent product, upstream-compatible (Recommended)

Adopt a distinct product identity (name, messaging, documentation) while
maintaining an explicit, opt-in compatibility layer with `github/spec-kit`.

**Advantages:**

- Clearest long-term identity; positions the product on its own capabilities.
- Explicit compatibility layer is honest about the relationship rather than
  implying feature parity that does not exist.
- Allows the roadmap to evolve without being constrained by upstream decisions.
- Lower confusion risk for enterprise adopters who may be wary of "forks."

**Disadvantages:**

- Higher documentation migration effort.
- Risk of appearing to distance from a well-known upstream brand prematurely.

### Option B — Fork-plus branding

Keep fork-centric framing; add messaging that highlights differentiators
without fully separating from the upstream identity.

**Advantages:**

- Lower migration effort (minimal README/docs changes).
- Maintains association with the upstream brand as social proof.

**Disadvantages:**

- Weak identity: "fork with extras" is not a compelling or ownable position.
- Upstream decisions continue to define the product's frame of reference.
- Creates ceiling on enterprise adoption (forks carry a reputational discount).

### Option C — Dual track

Maintain a core independent product *and* a "compat pack" that maintains exact
upstream parity for teams that need it.

**Advantages:**

- Serves two distinct market segments.
- Can be positioned as both the independent tool and the upstream distribution.

**Disadvantages:**

- Significant maintenance overhead for two parallel tracks.
- Requires dedicated versioning and release pipelines per track.
- Scope exceeds current team capacity and complicates the roadmap.

## Decision

**Option A is selected.**

Nexo Spec Kit adopts a clear, independent product identity while maintaining
explicit, opt-in upstream compatibility. The rationale:

1. **The capabilities already justify independence.** Phase 0 ideation, 17+
   agent integrations, contract validation, enterprise compliance, and the
   deploy pipeline are not "extras on a fork" — they constitute a distinct
   product.

2. **Compatibility is a feature, not a constraint.** Retaining the upstream
   compatibility layer (`--template-repo github/spec-kit`,
   `SPECIFY_TEMPLATE_REPO`) gives teams a low-friction migration path and
   preserves goodwill with the upstream project, without forcing us to match
   upstream decisions one-for-one.

3. **Option B is not viable long-term.** Fork-plus framing creates an
   artificial ceiling on identity and makes enterprise positioning harder.

4. **Option C is premature.** A dual-track architecture is worth revisiting
   once the independent product has established its own community and cadence.

## Consequences

### What changes

- README and docs landing updated to reflect the independent product identity
  (Nexo Spec Kit) with explicit non-affiliation and upstream-compatibility
  statements.
- A dedicated `docs/positioning.md` document defines the product identity,
  target users, differentiation, and promise.
- Release notes and messaging use Nexo Spec Kit terminology, not "fork"
  framing, as the primary description.

### What stays the same

- Upstream intake workflow (7-step process in `AGENTS.md`) remains active.
- `SPECIFY_TEMPLATE_REPO` and `--template-repo` flags continue to support
  upstream templates.
- MIT license is preserved with full attribution.
- Non-affiliation statement ("This fork is not affiliated with GitHub") is
  retained in all user-facing materials per the compliance policy.

### Follow-up items

- Coordinate with the naming and logo issues to align visual identity with the
  positioning decision.
- Review `docs/compatibility.md` to ensure the compatibility statement matches
  the selected model.
- Revisit Option C in a future cycle once independent community traction is
  established.

## References

- [docs/positioning.md](positioning.md) — Full positioning document
- [docs/compatibility.md](compatibility.md) — Compatibility policy
- [docs/legal-compliance.md](legal-compliance.md) — Legal and trademark policy
- [FORK_MANIFESTO.md](../FORK_MANIFESTO.md) — Original fork rationale
- [ROADMAP.md](../ROADMAP.md) — Current roadmap
