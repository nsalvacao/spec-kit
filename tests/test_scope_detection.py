"""Tests for adaptive scope detection engine (issue #101)."""

import pytest

from specify_cli.scope_detection import (
    CONTRACT_VERSION,
    ScopeDetectionConfig,
    ScopeDetectionInput,
    ScopeMode,
    detect_scope_for_project,
    detect_scope,
    load_scope_detection_config,
    scope_detection_config_from_mapping,
)


def test_feature_mode_for_simple_request():
    result = detect_scope(
        ScopeDetectionInput(
            description="Add status filter to customer listing.",
            estimated_timeline_weeks=2,
            expected_work_items=1,
            dependency_count=0,
            integration_surface_count=0,
            domain_count=1,
            cross_team_count=1,
            risk_level="low",
        )
    )

    assert result.mode_recommendation == ScopeMode.FEATURE
    assert result.score_band == "0-34"
    assert 0 <= result.total_score <= 34
    assert 2 <= len(result.recommendation_reasons) <= 3
    assert 0.35 <= result.confidence <= 0.95


def test_epic_mode_for_intermediate_request():
    result = detect_scope(
        ScopeDetectionInput(
            description="Create onboarding capability with several internal integrations.",
            estimated_timeline_weeks=8,
            expected_work_items=3,
            dependency_count=3,
            integration_surface_count=2,
            domain_count=2,
            cross_team_count=2,
            risk_level="medium",
        )
    )

    assert result.mode_recommendation == ScopeMode.EPIC
    assert result.score_band == "35-64"
    assert 35 <= result.total_score <= 64
    assert len(result.recommendation_reasons) >= 2


def test_program_mode_for_large_request():
    result = detect_scope(
        ScopeDetectionInput(
            description=(
                "Build a multi-tenant platform with migration, security, and cross-team rollout "
                "for billing, observability, and compliance."
            ),
            estimated_timeline_weeks=14,
            expected_work_items=5,
            dependency_count=5,
            integration_surface_count=4,
            domain_count=3,
            cross_team_count=3,
            risk_level="high",
            requires_compliance_review=True,
            requires_migration=True,
        )
    )

    assert result.mode_recommendation == ScopeMode.PROGRAM
    assert result.score_band == "65+"
    assert result.total_score >= 65


@pytest.mark.parametrize(
    ("input_data", "expected_score", "expected_mode", "expected_band"),
    [
        (
            ScopeDetectionInput(
                description="Improve search with simple state filters.",
                estimated_timeline_weeks=5,
                expected_work_items=2,
                dependency_count=3,
                integration_surface_count=2,
                domain_count=2,
                cross_team_count=1,
                risk_level="low",
            ),
            34,
            ScopeMode.FEATURE,
            "0-34",
        ),
        (
            ScopeDetectionInput(
                description="Improve search with simple state filters.",
                estimated_timeline_weeks=6,
                expected_work_items=2,
                dependency_count=3,
                integration_surface_count=2,
                domain_count=2,
                cross_team_count=1,
                risk_level="low",
            ),
            35,
            ScopeMode.EPIC,
            "35-64",
        ),
        (
            ScopeDetectionInput(
                description="platform migration rollout integration audit",
                estimated_timeline_weeks=10,
                expected_work_items=3,
                dependency_count=3,
                integration_surface_count=3,
                domain_count=2,
                cross_team_count=2,
                risk_level="medium",
            ),
            64,
            ScopeMode.EPIC,
            "35-64",
        ),
        (
            ScopeDetectionInput(
                description="platform migration rollout integration audit",
                estimated_timeline_weeks=11,
                expected_work_items=3,
                dependency_count=3,
                integration_surface_count=3,
                domain_count=2,
                cross_team_count=2,
                risk_level="medium",
            ),
            65,
            ScopeMode.PROGRAM,
            "65+",
        ),
    ],
)
def test_score_band_boundaries(input_data, expected_score, expected_mode, expected_band):
    result = detect_scope(input_data)
    assert result.total_score == expected_score
    assert result.mode_recommendation == expected_mode
    assert result.score_band == expected_band


def test_result_contract_payload_is_stable():
    input_data = ScopeDetectionInput(
        description="Moderate integration with internal team dependencies.",
        estimated_timeline_weeks=7,
        expected_work_items=2,
        dependency_count=2,
        integration_surface_count=2,
        domain_count=2,
        cross_team_count=2,
        risk_level="medium",
    )
    result_a = detect_scope(input_data)
    result_b = detect_scope(input_data)

    assert result_a.to_dict() == result_b.to_dict()
    payload = result_a.to_dict()
    assert payload["contract_version"] == CONTRACT_VERSION
    assert payload["mode_recommendation"] in {"feature", "epic", "program"}
    assert "recommendation_reasons" in payload
    assert "confidence" in payload
    assert "signals" in payload


def test_result_includes_expected_signal_names():
    result = detect_scope(
        ScopeDetectionInput(
            description="Update operational dashboard with minimal structural changes.",
            estimated_timeline_weeks=2,
            expected_work_items=1,
            dependency_count=0,
            integration_surface_count=1,
            domain_count=1,
            cross_team_count=1,
            risk_level="low",
        )
    )
    signal_names = {signal.name for signal in result.signals}
    assert signal_names == {
        "timeline_weeks",
        "expected_work_items",
        "dependency_count",
        "integration_surface_count",
        "domain_count",
        "cross_team_count",
        "risk_level",
        "requires_compliance_review",
        "requires_migration",
        "complexity_keywords",
    }


def test_invalid_risk_level_raises_error():
    with pytest.raises(ValueError, match="risk_level must be one of"):
        detect_scope(
            ScopeDetectionInput(
                description="Validation test request.",
                risk_level="unknown",
            )
        )


def test_invalid_description_type_raises_error():
    with pytest.raises(TypeError, match="description must be a string"):
        detect_scope(
            ScopeDetectionInput(  # type: ignore[arg-type]
                description=123,
            )
        )


def test_invalid_boolean_flag_type_raises_error():
    with pytest.raises(TypeError, match="requires_migration must be a boolean"):
        detect_scope(
            ScopeDetectionInput(  # type: ignore[arg-type]
                description="Run migration orchestration.",
                requires_migration="yes",
            )
        )


def test_keyword_matching_avoids_substring_false_positive():
    result = detect_scope(
        ScopeDetectionInput(
            description="Improve blossom analytics dashboard for retention.",
            estimated_timeline_weeks=2,
            expected_work_items=1,
            dependency_count=0,
            integration_surface_count=0,
            domain_count=1,
            cross_team_count=1,
            risk_level="low",
        )
    )

    keyword_signal = next(signal for signal in result.signals if signal.name == "complexity_keywords")
    assert "sso" not in keyword_signal.value


def test_custom_config_allows_overriding_default_weights():
    input_data = ScopeDetectionInput(
        description="Prepare a platform migration with integration and security checks.",
        estimated_timeline_weeks=10,
        expected_work_items=4,
        dependency_count=4,
        integration_surface_count=3,
        domain_count=2,
        cross_team_count=2,
        risk_level="high",
    )
    default_result = detect_scope(input_data)

    tuned_config = ScopeDetectionConfig(
        work_items_multiplier=2,
        dependency_multiplier=1,
        integration_multiplier=1,
        domain_multiplier=6,
        cross_team_multiplier=2,
        complexity_keywords=frozenset({"platform", "migration"}),
    )
    tuned_result = detect_scope(input_data, config=tuned_config)

    assert default_result.total_score != tuned_result.total_score


def test_scope_detection_config_can_be_loaded_from_project_file(tmp_path):
    config_file = tmp_path / ".specify" / "spec-kit.yml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        """
schema_version: 1
scope_detection:
  work_items_multiplier: 1
  dependency_multiplier: 1
  complexity_keywords:
    - platform
    - migration
""".strip(),
        encoding="utf-8",
    )

    loaded = load_scope_detection_config(project_root=tmp_path)
    assert loaded.work_items_multiplier == 1
    assert loaded.dependency_multiplier == 1
    assert loaded.complexity_keywords == frozenset({"platform", "migration"})


def test_scope_detection_env_override_changes_loaded_config(tmp_path):
    (tmp_path / ".specify").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".specify" / "spec-kit.yml").write_text("schema_version: 1\n", encoding="utf-8")

    loaded = load_scope_detection_config(
        project_root=tmp_path,
        env={"SPECIFY_CONFIG__SCOPE_DETECTION__WORK_ITEMS_MULTIPLIER": "2"},
    )
    assert loaded.work_items_multiplier == 2


def test_detect_scope_for_project_uses_project_config(tmp_path):
    config_file = tmp_path / ".specify" / "spec-kit.yml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        """
schema_version: 1
scope_detection:
  work_items_multiplier: 1
  dependency_multiplier: 1
  integration_multiplier: 1
  domain_multiplier: 5
  cross_team_multiplier: 2
""".strip(),
        encoding="utf-8",
    )

    input_data = ScopeDetectionInput(
        description="Platform migration and integration plan for security hardening.",
        estimated_timeline_weeks=10,
        expected_work_items=4,
        dependency_count=4,
        integration_surface_count=3,
        domain_count=2,
        cross_team_count=2,
        risk_level="high",
    )

    default_result = detect_scope(input_data)
    project_result = detect_scope_for_project(input_data, project_root=tmp_path)
    assert default_result.total_score != project_result.total_score


def test_unknown_scope_detection_config_key_raises_error():
    with pytest.raises(ValueError, match="Unknown scope_detection config keys"):
        scope_detection_config_from_mapping({"unknown_key": 123})
