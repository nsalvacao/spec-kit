# Methodology (Fork)

This fork extends Spec-Driven Development with **Phase 0** for AI system ideation as a recommended prerequisite. The result is a complete workflow from idea exploration to execution, with explicit artifacts and validation gates.

## Spec-Driven Development (SDD)

SDD treats specifications as executable artifacts. Instead of starting with code, the workflow starts with structured specs and progressively narrows to implementation:

1. **Constitution** - project principles and constraints
2. **Specify** - functional requirements and user stories
3. **Plan** - technical implementation choices
4. **Tasks** - actionable breakdown
5. **Implement** - execution against the plan

## Why Phase 0

AI systems benefit from early ideation and validation before formal specs. Phase 0 provides that structure:

- **IDEATE**: SCAMPER + HMW to generate a backlog of ideas
- **SELECT**: AI-RICE scoring to choose a winner
- **STRUCTURE**: Integrated AI Vision Canvas + Vision Brief
- **VALIDATE**: Gate G0 checks (automated + manual)

This creates a defensible, documented rationale before the SDD pipeline starts.

## End-to-End Workflow

1. **Phase 0**: IDEATE → SELECT → STRUCTURE → VALIDATE  
2. **SDD Core**: CONSTITUTION → SPECIFY → PLAN → TASKS → IMPLEMENT

## Core Principles

- **Traceability**: each decision has a documented artifact
- **Validation-first**: checks are explicit and repeatable
- **Quality gates**: Phase 0 and spec review block weak ideas early
- **Compatibility**: upstream workflows remain intact

## Key Artifacts

- `.spec-kit/ideas_backlog.md`
- `.spec-kit/idea_selection.md`
- `.spec-kit/ai_vision_canvas.md`
- `.spec-kit/vision_brief.md`
- `.spec-kit/approvals/g0-validation-report.md`
- `.specify/specs/<feature>/spec.md`
- `.specify/specs/<feature>/plan.md`
- `.specify/specs/<feature>/tasks.md`

## Next Steps

- See `quickstart.md` for the shortest path to start
- See `walkthrough.md` for a full step-by-step guide
