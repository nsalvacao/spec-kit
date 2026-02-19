"""Adaptive scope detection engine for Feature/Epic/Program recommendation.

This module provides a deterministic scoring model used to classify initiative
scope before task generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


CONTRACT_VERSION = "scope-detection.v1"


class ScopeMode(StrEnum):
    """Supported orchestration modes."""

    FEATURE = "feature"
    EPIC = "epic"
    PROGRAM = "program"


RISK_WEIGHTS = {
    "low": 0,
    "medium": 6,
    "high": 12,
    "critical": 18,
}

COMPLEXITY_KEYWORDS = {
    "platform",
    "migration",
    "rollout",
    "integration",
    "compliance",
    "audit",
    "multi-tenant",
    "legacy",
    "cross-team",
    "multi-region",
    "portfolio",
    "sso",
    "billing",
    "observability",
    "security",
}


@dataclass(frozen=True)
class ScopeDetectionInput:
    """Input model for scope detection scoring."""

    description: str
    estimated_timeline_weeks: int = 1
    expected_work_items: int = 1
    dependency_count: int = 0
    integration_surface_count: int = 0
    domain_count: int = 1
    cross_team_count: int = 1
    risk_level: str = "low"
    requires_compliance_review: bool = False
    requires_migration: bool = False

    def validate(self) -> None:
        if not self.description.strip():
            raise ValueError("description cannot be empty")
        if self.risk_level not in RISK_WEIGHTS:
            valid = ", ".join(sorted(RISK_WEIGHTS))
            raise ValueError(f"risk_level must be one of: {valid}")
        if self.estimated_timeline_weeks < 1:
            raise ValueError("estimated_timeline_weeks must be >= 1")
        if self.expected_work_items < 1:
            raise ValueError("expected_work_items must be >= 1")
        if self.domain_count < 1:
            raise ValueError("domain_count must be >= 1")
        if self.cross_team_count < 1:
            raise ValueError("cross_team_count must be >= 1")
        if self.dependency_count < 0:
            raise ValueError("dependency_count must be >= 0")
        if self.integration_surface_count < 0:
            raise ValueError("integration_surface_count must be >= 0")

    @property
    def normalized_description(self) -> str:
        return " ".join(self.description.lower().split())


@dataclass(frozen=True)
class ScopeSignal:
    """Single scoring signal used by the engine."""

    name: str
    value: Any
    weight: int
    score: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "score": self.score,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ScopeDetectionResult:
    """Output contract for scope recommendation consumers."""

    contract_version: str
    total_score: int
    score_band: str
    mode_recommendation: ScopeMode
    recommendation_reasons: list[str]
    confidence: float
    signals: list[ScopeSignal]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "total_score": self.total_score,
            "score_band": self.score_band,
            "mode_recommendation": self.mode_recommendation.value,
            "recommendation_reasons": self.recommendation_reasons,
            "confidence": self.confidence,
            "signals": [signal.to_dict() for signal in self.signals],
        }


def detect_scope(input_data: ScopeDetectionInput) -> ScopeDetectionResult:
    """Return a deterministic scope recommendation for the provided input."""

    input_data.validate()
    keywords = _matched_keywords(input_data.normalized_description)

    timeline_score = min(10, max(0, input_data.estimated_timeline_weeks - 1))
    work_items_score = min(20, max(0, (input_data.expected_work_items - 1) * 5))
    dependency_score = min(15, input_data.dependency_count * 3)
    integration_score = min(12, input_data.integration_surface_count * 3)
    domain_score = min(20, max(0, (input_data.domain_count - 1) * 10))
    cross_team_score = min(12, max(0, (input_data.cross_team_count - 1) * 6))
    risk_score = RISK_WEIGHTS[input_data.risk_level]
    compliance_score = 7 if input_data.requires_compliance_review else 0
    migration_score = 9 if input_data.requires_migration else 0
    keyword_score = min(12, len(keywords))

    signals = [
        ScopeSignal(
            name="timeline_weeks",
            value=input_data.estimated_timeline_weeks,
            weight=1,
            score=timeline_score,
            rationale=(
                f"Timeline estimada de {input_data.estimated_timeline_weeks} semanas "
                f"adiciona {timeline_score} pontos de complexidade."
            ),
        ),
        ScopeSignal(
            name="expected_work_items",
            value=input_data.expected_work_items,
            weight=5,
            score=work_items_score,
            rationale=(
                f"{input_data.expected_work_items} work items previstos exigem maior "
                f"decomposição ({work_items_score} pontos)."
            ),
        ),
        ScopeSignal(
            name="dependency_count",
            value=input_data.dependency_count,
            weight=3,
            score=dependency_score,
            rationale=(
                f"{input_data.dependency_count} dependências externas elevam coordenação "
                f"e risco operacional ({dependency_score} pontos)."
            ),
        ),
        ScopeSignal(
            name="integration_surface_count",
            value=input_data.integration_surface_count,
            weight=3,
            score=integration_score,
            rationale=(
                f"{input_data.integration_surface_count} superfícies de integração "
                f"adicionam acoplamento técnico ({integration_score} pontos)."
            ),
        ),
        ScopeSignal(
            name="domain_count",
            value=input_data.domain_count,
            weight=10,
            score=domain_score,
            rationale=(
                f"{input_data.domain_count} domínios envolvidos indicam amplitude "
                f"de escopo ({domain_score} pontos)."
            ),
        ),
        ScopeSignal(
            name="cross_team_count",
            value=input_data.cross_team_count,
            weight=6,
            score=cross_team_score,
            rationale=(
                f"{input_data.cross_team_count} equipas impactadas aumentam custo "
                f"de alinhamento ({cross_team_score} pontos)."
            ),
        ),
        ScopeSignal(
            name="risk_level",
            value=input_data.risk_level,
            weight=1,
            score=risk_score,
            rationale=f"Risco declarado '{input_data.risk_level}' soma {risk_score} pontos.",
        ),
        ScopeSignal(
            name="requires_compliance_review",
            value=input_data.requires_compliance_review,
            weight=7,
            score=compliance_score,
            rationale=(
                "Necessidade de compliance formal aumenta validações e dependências "
                f"de aprovação ({compliance_score} pontos)."
            ),
        ),
        ScopeSignal(
            name="requires_migration",
            value=input_data.requires_migration,
            weight=9,
            score=migration_score,
            rationale=(
                "Migração/cutover acrescenta risco de transição e rollback "
                f"({migration_score} pontos)."
            ),
        ),
        ScopeSignal(
            name="complexity_keywords",
            value=keywords,
            weight=1,
            score=keyword_score,
            rationale=(
                f"Palavras-chave de complexidade detetadas ({', '.join(keywords) or 'nenhuma'}) "
                f"contribuem {keyword_score} pontos."
            ),
        ),
    ]

    raw_score = sum(signal.score for signal in signals)
    total_score = min(100, raw_score)
    mode = _mode_from_score(total_score)
    score_band = _score_band(total_score)
    reasons = _build_reasons(signals, mode)
    confidence = _compute_confidence(input_data, total_score, signals, keywords)

    return ScopeDetectionResult(
        contract_version=CONTRACT_VERSION,
        total_score=total_score,
        score_band=score_band,
        mode_recommendation=mode,
        recommendation_reasons=reasons,
        confidence=confidence,
        signals=signals,
    )


def _matched_keywords(description: str) -> list[str]:
    matches = [keyword for keyword in COMPLEXITY_KEYWORDS if keyword in description]
    return sorted(set(matches))


def _mode_from_score(score: int) -> ScopeMode:
    if score <= 34:
        return ScopeMode.FEATURE
    if score <= 64:
        return ScopeMode.EPIC
    return ScopeMode.PROGRAM


def _score_band(score: int) -> str:
    if score <= 34:
        return "0-34"
    if score <= 64:
        return "35-64"
    return "65+"


def _build_reasons(signals: list[ScopeSignal], mode: ScopeMode) -> list[str]:
    positive_signals = [signal for signal in signals if signal.score > 0]
    positive_signals.sort(key=lambda signal: (-signal.score, signal.name))

    reasons = [signal.rationale for signal in positive_signals[:3]]
    if len(reasons) < 2:
        if mode == ScopeMode.FEATURE:
            reasons.append(
                "Sinais de dependências, risco e coordenação mantêm-se baixos; "
                "é viável avançar como feature única."
            )
        elif mode == ScopeMode.EPIC:
            reasons.append(
                "Existe complexidade intermédia com múltiplos vetores relevantes; "
                "é recomendado decompor em features antes de tarefas finais."
            )
        else:
            reasons.append(
                "Complexidade agregada elevada sugere estruturação por programa "
                "com decomposição progressiva em épicos e features."
            )

    if len(reasons) < 2:
        reasons.append("Foram usados sinais estruturados para produzir recomendação determinística.")

    return reasons[:3]


def _compute_confidence(
    input_data: ScopeDetectionInput,
    score: int,
    signals: list[ScopeSignal],
    keywords: list[str],
) -> float:
    active_signals = sum(1 for signal in signals if signal.score > 0)
    boundary_distance = min(abs(score - 34), abs(score - 35), abs(score - 64), abs(score - 65))
    confidence = 0.55
    confidence += min(0.30, active_signals * 0.04)
    confidence += min(0.10, len(keywords) * 0.01)
    if boundary_distance <= 1:
        confidence -= 0.08
    if len(input_data.description.split()) < 8:
        confidence -= 0.05
    return round(min(0.95, max(0.35, confidence)), 2)
