"""Tests for adaptive scope detection engine (issue #101)."""

import pytest

from specify_cli.scope_detection import (
    CONTRACT_VERSION,
    ScopeDetectionInput,
    ScopeMode,
    detect_scope,
)


def test_feature_mode_for_simple_request():
    result = detect_scope(
        ScopeDetectionInput(
            description="Adicionar filtro por estado na listagem de clientes.",
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
            description="Criar capability de onboarding com várias integrações internas.",
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
                "Plataforma multi-tenant com migration, security e rollout cross-team "
                "para billing, observability e compliance."
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
                description="Melhorar busca por estado com filtros simples.",
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
                description="Melhorar busca por estado com filtros simples.",
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
        description="Integração moderada com dependências de equipas internas.",
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
            description="Atualizar dashboard operacional com pouca mudança estrutural.",
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
                description="Pedido de teste.",
                risk_level="unknown",
            )
        )
