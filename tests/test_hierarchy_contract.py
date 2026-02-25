"""Tests for Program/Epic/Feature hierarchy metadata contract (issue #107)."""

import pytest

from specify_cli.hierarchy_contract import (
    HIERARCHY_CONTRACT_VERSION,
    HierarchyMode,
    build_feature_hierarchy_contract,
    normalize_hierarchy_contract_payload,
    validate_hierarchy_contract_payload,
)


def test_normalize_hierarchy_contract_accepts_complete_tree():
    payload = {
        "contract_version": HIERARCHY_CONTRACT_VERSION,
        "mode": "program",
        "program": {
            "id": "Program-Alpha",
            "title": "Platform Expansion",
            "status": "active",
            "owner": "pm-core",
            "epic_ids": ["epic-onboarding"],
            "lineage": {
                "origin": "specify",
                "parent_id": None,
                "depth": 0,
                "source_decision": "program_mode",
            },
        },
        "epics": [
            {
                "id": "epic-onboarding",
                "title": "Onboarding Foundation",
                "status": "active",
                "owner": "planner-team",
                "program_id": "program-alpha",
                "feature_ids": ["021-user-onboarding"],
                "lineage": {
                    "origin": "specify",
                    "parent_id": "program-alpha",
                    "depth": 1,
                    "source_decision": "decomposition_gate",
                },
            }
        ],
        "features": [
            {
                "id": "021-user-onboarding",
                "title": "User onboarding journey",
                "status": "draft",
                "owner": "team-app",
                "program_id": "program-alpha",
                "epic_id": "epic-onboarding",
                "artifacts": {
                    "spec": "specs/021-user-onboarding/spec.md",
                    "plan": "specs/021-user-onboarding/plan.md",
                    "tasks": "specs/021-user-onboarding/tasks.md",
                },
                "lineage": {
                    "origin": "specify",
                    "parent_id": "epic-onboarding",
                    "depth": 2,
                    "source_decision": "decomposition_gate",
                },
            }
        ],
    }

    contract = normalize_hierarchy_contract_payload(payload, strict=True)
    assert contract.mode == HierarchyMode.PROGRAM
    assert contract.program is not None
    assert contract.program.id == "program-alpha"
    assert len(contract.epics) == 1
    assert len(contract.features) == 1
    assert contract.features[0].artifacts.tasks == "specs/021-user-onboarding/tasks.md"


def test_build_feature_hierarchy_contract_creates_feature_only_contract():
    contract = build_feature_hierarchy_contract(
        feature_id="030-payment-retry",
        title="Payment retry flow",
        owner="team-billing",
    )

    payload = contract.to_dict()
    assert payload["contract_version"] == HIERARCHY_CONTRACT_VERSION
    assert payload["mode"] == "feature"
    assert len(payload["features"]) == 1
    assert payload["features"][0]["artifacts"]["tasks"] == "specs/030-payment-retry/tasks.md"


def test_normalize_hierarchy_contract_rejects_epic_mode_without_program():
    payload = {
        "mode": "epic",
        "epics": [
            {
                "id": "epic-ops",
                "title": "Ops",
                "status": "active",
                "owner": "team-ops",
                "program_id": "program-ops",
                "feature_ids": ["050-ops-dashboard"],
            }
        ],
        "features": [
            {
                "id": "050-ops-dashboard",
                "title": "Ops dashboard",
                "status": "draft",
                "owner": "team-ops",
                "epic_id": "epic-ops",
                "program_id": "program-ops",
                "artifacts": {
                    "spec": "specs/050-ops-dashboard/spec.md",
                    "plan": "specs/050-ops-dashboard/plan.md",
                    "tasks": "specs/050-ops-dashboard/tasks.md",
                },
            }
        ],
    }

    with pytest.raises(ValueError, match="requires program metadata"):
        normalize_hierarchy_contract_payload(payload, strict=True)


def test_normalize_hierarchy_contract_rejects_invalid_artifact_reference():
    payload = {
        "mode": "feature",
        "features": [
            {
                "id": "040-auth-hardening",
                "title": "Auth hardening",
                "status": "draft",
                "owner": "team-security",
                "artifacts": {
                    "spec": "specs/040-auth-hardening/spec.md",
                    "plan": "specs/040-auth-hardening/plan.md",
                    "tasks": "../escape/tasks.md",
                },
            }
        ],
    }

    with pytest.raises(ValueError, match="cannot contain parent traversal"):
        normalize_hierarchy_contract_payload(payload)


def test_validate_hierarchy_contract_payload_non_strict_returns_errors():
    payload = {
        "mode": "feature",
        "features": [],
    }
    errors = validate_hierarchy_contract_payload(payload, strict=False)
    assert errors
    assert "at least one feature" in errors[0]

