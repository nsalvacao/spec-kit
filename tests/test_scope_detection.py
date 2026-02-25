"""Tests for adaptive scope detection engine (issue #101)."""

import pytest

from specify_cli.scope_detection import (
    CONTRACT_VERSION,
    SCORING_RUBRIC_AGGREGATION_FORMULA,
    SCORING_RUBRIC_VERSION,
    ScopeDetectionConfig,
    ScopeDetectionInput,
    ScopeMode,
    detect_scope_for_project,
    detect_scope,
    load_scope_detection_config,
    scope_scoring_rubric,
    scope_detection_input_from_mapping,
    scope_detection_config_from_mapping,
    validate_scope_scoring_rubric_payload,
)


@pytest.fixture
def low_complexity_request() -> ScopeDetectionInput:
    return ScopeDetectionInput(
        description="Add status filter to customer listing.",
        estimated_timeline_weeks=2,
        expected_work_items=1,
        dependency_count=0,
        integration_surface_count=0,
        domain_count=1,
        cross_team_count=1,
        risk_level="low",
    )


@pytest.fixture
def medium_complexity_request() -> ScopeDetectionInput:
    return ScopeDetectionInput(
        description="Create onboarding capability with several internal integrations.",
        estimated_timeline_weeks=8,
        expected_work_items=3,
        dependency_count=3,
        integration_surface_count=2,
        domain_count=2,
        cross_team_count=2,
        risk_level="medium",
    )


@pytest.fixture
def high_complexity_request() -> ScopeDetectionInput:
    return ScopeDetectionInput(
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


def test_scope_detection_input_from_mapping_normalizes_scalars():
    parsed = scope_detection_input_from_mapping(
        {
            "description": " Cross-team migration plan ",
            "estimated_timeline_weeks": "6",
            "expected_work_items": "3",
            "dependency_count": "2",
            "integration_surface_count": 1,
            "domain_count": "2",
            "cross_team_count": 2,
            "risk_level": " HIGH ",
            "requires_compliance_review": "true",
            "requires_migration": "0",
        }
    )

    assert parsed.description == "Cross-team migration plan"
    assert parsed.estimated_timeline_weeks == 6
    assert parsed.expected_work_items == 3
    assert parsed.dependency_count == 2
    assert parsed.integration_surface_count == 1
    assert parsed.domain_count == 2
    assert parsed.cross_team_count == 2
    assert parsed.normalized_risk_level == "high"
    assert parsed.requires_compliance_review is True
    assert parsed.requires_migration is False


def test_scope_detection_input_from_mapping_rejects_unknown_keys():
    with pytest.raises(ValueError, match="Unknown scope_detection input keys"):
        scope_detection_input_from_mapping({"description": "hello", "unknown": 1})


def test_scope_detection_input_from_mapping_requires_description():
    with pytest.raises(ValueError, match="missing required key: description"):
        scope_detection_input_from_mapping({"expected_work_items": 2})


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


def test_scope_scoring_rubric_has_expected_defaults():
    defaults = ScopeDetectionConfig()
    rubric = scope_scoring_rubric()

    assert rubric["rubric_version"] == SCORING_RUBRIC_VERSION
    assert rubric["contract_version"] == CONTRACT_VERSION
    assert rubric["aggregation_formula"] == SCORING_RUBRIC_AGGREGATION_FORMULA
    assert rubric["score_bands"] == [
        {"mode": "feature", "min_score": 0, "max_score": defaults.feature_max_score},
        {"mode": "epic", "min_score": defaults.feature_max_score + 1, "max_score": defaults.epic_max_score},
        {"mode": "program", "min_score": defaults.epic_max_score + 1, "max_score": defaults.max_total_score},
    ]
    assert rubric["rationale_rule"]["min_reasons"] == 2
    assert rubric["rationale_rule"]["max_primary_reasons"] == 3
    validate_scope_scoring_rubric_payload(rubric, strict=True)


def test_scope_scoring_rubric_respects_custom_config():
    rubric = scope_scoring_rubric(
        config=ScopeDetectionConfig(
            feature_max_score=20,
            epic_max_score=50,
            max_total_score=80,
            work_items_multiplier=2,
            keyword_cap=5,
            risk_weights={"low": 1, "medium": 4, "high": 8, "critical": 12},
            complexity_keywords=frozenset({"platform", "cutover"}),
        )
    )

    assert rubric["score_bands"] == [
        {"mode": "feature", "min_score": 0, "max_score": 20},
        {"mode": "epic", "min_score": 21, "max_score": 50},
        {"mode": "program", "min_score": 51, "max_score": 80},
    ]

    by_name = {dimension["name"]: dimension for dimension in rubric["dimensions"]}
    assert by_name["expected_work_items"]["weight"] == 2
    assert by_name["complexity_keywords"]["cap"] == 5
    assert by_name["risk_level"]["weight_map"] == {"critical": 12, "high": 8, "low": 1, "medium": 4}
    assert by_name["complexity_keywords"]["keyword_source"] == ["cutover", "platform"]


def test_scope_scoring_rubric_dimensions_match_signal_contract():
    result = detect_scope(ScopeDetectionInput(description="Simple task."))
    signal_names = {signal.name for signal in result.signals}
    rubric_dimension_names = {dimension["name"] for dimension in scope_scoring_rubric()["dimensions"]}

    assert rubric_dimension_names == signal_names


def test_validate_scope_scoring_rubric_payload_rejects_missing_required_keys():
    payload = scope_scoring_rubric()
    payload.pop("dimensions")

    with pytest.raises(ValueError, match="missing required keys"):
        validate_scope_scoring_rubric_payload(payload, strict=True)


def test_validate_scope_scoring_rubric_payload_rejects_unknown_keys_in_strict_mode():
    payload = scope_scoring_rubric()
    payload["unknown_key"] = "value"

    with pytest.raises(ValueError, match="unknown keys"):
        validate_scope_scoring_rubric_payload(payload, strict=True)


def test_validate_scope_scoring_rubric_payload_allows_unknown_keys_in_non_strict_mode():
    payload = scope_scoring_rubric()
    payload["future_extension"] = {"foo": "bar"}

    result = validate_scope_scoring_rubric_payload(payload, strict=False)
    assert result is None
    assert "future_extension" in payload


def test_validate_scope_scoring_rubric_payload_rejects_wrong_band_count_for_v1():
    payload = scope_scoring_rubric()
    payload["score_bands"] = payload["score_bands"] + [{"mode": "experimental", "min_score": 101, "max_score": 120}]

    with pytest.raises(ValueError, match="exactly 3 entries for v1"):
        validate_scope_scoring_rubric_payload(payload, strict=True)


def test_validate_scope_scoring_rubric_payload_allows_different_band_count_for_future_version():
    payload = scope_scoring_rubric()
    payload["rubric_version"] = "scope-scoring-rubric.v2"
    payload["score_bands"] = payload["score_bands"] + [{"mode": "experimental", "min_score": 101, "max_score": 120}]

    validate_scope_scoring_rubric_payload(payload, strict=True)


def test_validate_scope_scoring_rubric_payload_rejects_invalid_score_band_shape():
    payload = scope_scoring_rubric()
    payload["score_bands"][0] = {"mode": "feature", "min_score": 0}

    with pytest.raises(ValueError, match="must include mode, min_score, and max_score"):
        validate_scope_scoring_rubric_payload(payload, strict=True)


def test_validate_scope_scoring_rubric_payload_rejects_duplicate_dimension_names():
    payload = scope_scoring_rubric()
    payload["dimensions"] = [
        {"name": "dimension_a"},
        {"name": "dimension_a"},
    ]

    with pytest.raises(ValueError, match="Dimension names must be unique"):
        validate_scope_scoring_rubric_payload(payload, strict=True)


def test_representative_scope_fixtures_cover_feature_epic_program(
    low_complexity_request: ScopeDetectionInput,
    medium_complexity_request: ScopeDetectionInput,
    high_complexity_request: ScopeDetectionInput,
):
    low_result = detect_scope(low_complexity_request)
    medium_result = detect_scope(medium_complexity_request)
    high_result = detect_scope(high_complexity_request)

    assert low_result.mode_recommendation == ScopeMode.FEATURE
    assert medium_result.mode_recommendation == ScopeMode.EPIC
    assert high_result.mode_recommendation == ScopeMode.PROGRAM


@pytest.mark.parametrize(
    ("estimated_timeline_weeks", "expected_score", "expected_mode"),
    [
        (4, 33, ScopeMode.FEATURE),
        (5, 34, ScopeMode.FEATURE),
        (6, 35, ScopeMode.EPIC),
    ],
)
def test_low_to_mid_boundary_neighbor_scores_are_stable(
    estimated_timeline_weeks: int,
    expected_score: int,
    expected_mode: ScopeMode,
):
    result = detect_scope(
        ScopeDetectionInput(
            description="Improve search with simple state filters.",
            estimated_timeline_weeks=estimated_timeline_weeks,
            expected_work_items=2,
            dependency_count=3,
            integration_surface_count=2,
            domain_count=2,
            cross_team_count=1,
            risk_level="low",
        )
    )

    assert result.total_score == expected_score
    assert result.mode_recommendation == expected_mode


@pytest.mark.parametrize(
    ("estimated_timeline_weeks", "expected_score", "expected_mode"),
    [
        (9, 63, ScopeMode.EPIC),
        (10, 64, ScopeMode.EPIC),
        (11, 65, ScopeMode.PROGRAM),
    ],
)
def test_mid_to_high_boundary_neighbor_scores_are_stable(
    estimated_timeline_weeks: int,
    expected_score: int,
    expected_mode: ScopeMode,
):
    result = detect_scope(
        ScopeDetectionInput(
            description="platform migration rollout integration audit",
            estimated_timeline_weeks=estimated_timeline_weeks,
            expected_work_items=3,
            dependency_count=3,
            integration_surface_count=3,
            domain_count=2,
            cross_team_count=2,
            risk_level="medium",
        )
    )

    assert result.total_score == expected_score
    assert result.mode_recommendation == expected_mode


def test_threshold_regression_matrix_changes_classification_when_boundaries_change(
    medium_complexity_request: ScopeDetectionInput,
):
    input_data = medium_complexity_request

    default_result = detect_scope(input_data)
    custom_threshold_result = detect_scope(
        input_data,
        config=ScopeDetectionConfig(feature_max_score=55, epic_max_score=80, max_total_score=100),
    )

    assert default_result.total_score == custom_threshold_result.total_score
    assert default_result.mode_recommendation == ScopeMode.EPIC
    assert custom_threshold_result.mode_recommendation == ScopeMode.FEATURE


def test_weight_regression_matrix_changes_classification_when_signal_weights_change(
    medium_complexity_request: ScopeDetectionInput,
):
    input_data = medium_complexity_request

    default_result = detect_scope(input_data)
    lightweight_result = detect_scope(
        input_data,
        config=ScopeDetectionConfig(
            work_items_multiplier=1,
            dependency_multiplier=1,
            integration_multiplier=1,
            domain_multiplier=5,
            cross_team_multiplier=2,
        ),
    )

    assert default_result.mode_recommendation == ScopeMode.EPIC
    assert lightweight_result.mode_recommendation == ScopeMode.FEATURE
    assert default_result.total_score > lightweight_result.total_score
