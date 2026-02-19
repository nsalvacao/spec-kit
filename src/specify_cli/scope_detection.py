"""Adaptive scope detection engine for Feature/Epic/Program recommendation.

This module provides a deterministic scoring model used to classify initiative
scope before task generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
import re
from typing import Any, Mapping

from .project_config import load_project_config


CONTRACT_VERSION = "scope-detection.v1"
SCORING_RUBRIC_VERSION = "scope-scoring-rubric.v1"
SCORING_RUBRIC_AGGREGATION_FORMULA = "total_score = min(max_total_score, sum(signal_scores))"
SCORING_RUBRIC_TIE_BREAK_RULE = (
    "Inclusive upper-bound comparison: score <= feature_max_score => feature; "
    "feature_max_score < score <= epic_max_score => epic; "
    "score > epic_max_score => program."
)
SCORING_RUBRIC_REQUIRED_KEYS = frozenset(
    {
        "rubric_version",
        "contract_version",
        "aggregation_formula",
        "score_bands",
        "tie_break_rule",
        "rationale_rule",
        "dimensions",
    }
)

DEFAULT_COMPLEXITY_KEYWORDS = frozenset(
    {
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
)

DEFAULT_RISK_WEIGHTS = {
    "low": 0,
    "medium": 6,
    "high": 12,
    "critical": 18,
}


class ScopeMode(str, Enum):
    """Supported orchestration modes."""

    FEATURE = "feature"
    EPIC = "epic"
    PROGRAM = "program"


class ScopeRiskLevel(str, Enum):
    """Supported risk levels for scoring."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ScopeDetectionConfig:
    """Configurable weights, caps, boundaries, and confidence heuristics."""

    feature_max_score: int = 34
    epic_max_score: int = 64
    max_total_score: int = 100

    timeline_cap: int = 10
    timeline_multiplier: int = 1

    work_items_cap: int = 20
    work_items_multiplier: int = 5

    dependency_cap: int = 15
    dependency_multiplier: int = 3

    integration_cap: int = 12
    integration_multiplier: int = 3

    domain_cap: int = 20
    domain_multiplier: int = 10

    cross_team_cap: int = 12
    cross_team_multiplier: int = 6

    compliance_score: int = 7
    migration_score: int = 9
    keyword_cap: int = 12

    complexity_keywords: frozenset[str] = field(default_factory=lambda: DEFAULT_COMPLEXITY_KEYWORDS)
    risk_weights: dict[str, int] = field(default_factory=lambda: DEFAULT_RISK_WEIGHTS.copy())

    confidence_base: float = 0.55
    confidence_active_signal_step: float = 0.04
    confidence_active_signal_cap: float = 0.30
    confidence_keyword_step: float = 0.01
    confidence_keyword_cap: float = 0.10
    confidence_boundary_penalty: float = 0.08
    confidence_short_description_penalty: float = 0.05
    confidence_short_description_word_threshold: int = 8
    confidence_boundary_distance_threshold: int = 1
    confidence_min: float = 0.35
    confidence_max: float = 0.95

    def validate(self) -> None:
        """Validate config invariants used by the scoring engine."""
        if self.feature_max_score < 0:
            raise ValueError("feature_max_score must be >= 0")
        if self.epic_max_score <= self.feature_max_score:
            raise ValueError("epic_max_score must be > feature_max_score")
        if self.max_total_score <= self.epic_max_score:
            raise ValueError("max_total_score must be > epic_max_score")
        if self.confidence_min < 0 or self.confidence_max > 1:
            raise ValueError("confidence bounds must be within [0, 1]")
        if self.confidence_min >= self.confidence_max:
            raise ValueError("confidence_min must be < confidence_max")


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
    risk_level: ScopeRiskLevel | str = ScopeRiskLevel.LOW
    requires_compliance_review: bool = False
    requires_migration: bool = False

    @property
    def normalized_description(self) -> str:
        return " ".join(self.description.lower().split())

    @property
    def normalized_risk_level(self) -> str:
        if isinstance(self.risk_level, ScopeRiskLevel):
            return self.risk_level.value
        return self.risk_level.strip().lower()

    def validate(self, config: ScopeDetectionConfig) -> None:
        """Validate input type and value constraints."""
        if not isinstance(self.description, str):
            raise TypeError("description must be a string")
        if not self.description.strip():
            raise ValueError("description cannot be empty")

        int_fields = [
            "estimated_timeline_weeks",
            "expected_work_items",
            "dependency_count",
            "integration_surface_count",
            "domain_count",
            "cross_team_count",
        ]
        for field_name in int_fields:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")

        bool_fields = ["requires_compliance_review", "requires_migration"]
        for field_name in bool_fields:
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a boolean")

        if self.normalized_risk_level not in config.risk_weights:
            valid = ", ".join(sorted(config.risk_weights))
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


def detect_scope(
    input_data: ScopeDetectionInput,
    *,
    config: ScopeDetectionConfig | None = None,
) -> ScopeDetectionResult:
    """Return a deterministic scope recommendation for the provided input."""
    resolved_config = config or ScopeDetectionConfig()
    resolved_config.validate()
    input_data.validate(resolved_config)
    keywords = _matched_keywords(input_data.normalized_description, resolved_config.complexity_keywords)

    timeline_score = _scaled_score(
        max(0, input_data.estimated_timeline_weeks - 1),
        resolved_config.timeline_multiplier,
        resolved_config.timeline_cap,
    )
    work_items_score = _scaled_score(
        max(0, input_data.expected_work_items - 1),
        resolved_config.work_items_multiplier,
        resolved_config.work_items_cap,
    )
    dependency_score = _scaled_score(
        input_data.dependency_count,
        resolved_config.dependency_multiplier,
        resolved_config.dependency_cap,
    )
    integration_score = _scaled_score(
        input_data.integration_surface_count,
        resolved_config.integration_multiplier,
        resolved_config.integration_cap,
    )
    domain_score = _scaled_score(
        max(0, input_data.domain_count - 1),
        resolved_config.domain_multiplier,
        resolved_config.domain_cap,
    )
    cross_team_score = _scaled_score(
        max(0, input_data.cross_team_count - 1),
        resolved_config.cross_team_multiplier,
        resolved_config.cross_team_cap,
    )
    risk_score = resolved_config.risk_weights[input_data.normalized_risk_level]
    compliance_score = resolved_config.compliance_score if input_data.requires_compliance_review else 0
    migration_score = resolved_config.migration_score if input_data.requires_migration else 0
    keyword_score = min(resolved_config.keyword_cap, len(keywords))

    signals = [
        ScopeSignal(
            name="timeline_weeks",
            value=input_data.estimated_timeline_weeks,
            weight=resolved_config.timeline_multiplier,
            score=timeline_score,
            rationale=(
                f"Estimated timeline of {input_data.estimated_timeline_weeks} weeks "
                f"adds {timeline_score} complexity points."
            ),
        ),
        ScopeSignal(
            name="expected_work_items",
            value=input_data.expected_work_items,
            weight=resolved_config.work_items_multiplier,
            score=work_items_score,
            rationale=(
                f"{input_data.expected_work_items} expected work items require greater "
                f"decomposition ({work_items_score} points)."
            ),
        ),
        ScopeSignal(
            name="dependency_count",
            value=input_data.dependency_count,
            weight=resolved_config.dependency_multiplier,
            score=dependency_score,
            rationale=(
                f"{input_data.dependency_count} external dependencies increase "
                f"coordination and operational risk ({dependency_score} points)."
            ),
        ),
        ScopeSignal(
            name="integration_surface_count",
            value=input_data.integration_surface_count,
            weight=resolved_config.integration_multiplier,
            score=integration_score,
            rationale=(
                f"{input_data.integration_surface_count} integration surfaces "
                f"add technical coupling ({integration_score} points)."
            ),
        ),
        ScopeSignal(
            name="domain_count",
            value=input_data.domain_count,
            weight=resolved_config.domain_multiplier,
            score=domain_score,
            rationale=(
                f"{input_data.domain_count} involved domains indicate scope "
                f"breadth ({domain_score} points)."
            ),
        ),
        ScopeSignal(
            name="cross_team_count",
            value=input_data.cross_team_count,
            weight=resolved_config.cross_team_multiplier,
            score=cross_team_score,
            rationale=(
                f"{input_data.cross_team_count} impacted teams increase "
                f"alignment cost ({cross_team_score} points)."
            ),
        ),
        ScopeSignal(
            name="risk_level",
            value=input_data.normalized_risk_level,
            weight=1,
            score=risk_score,
            rationale=f"Declared risk level '{input_data.normalized_risk_level}' adds {risk_score} points.",
        ),
        ScopeSignal(
            name="requires_compliance_review",
            value=input_data.requires_compliance_review,
            weight=resolved_config.compliance_score,
            score=compliance_score,
            rationale=(
                "Formal compliance requirement increases validation and approval "
                f"dependencies ({compliance_score} points)."
            ),
        ),
        ScopeSignal(
            name="requires_migration",
            value=input_data.requires_migration,
            weight=resolved_config.migration_score,
            score=migration_score,
            rationale=(
                "Migration/cutover adds transition and rollback risk "
                f"({migration_score} points)."
            ),
        ),
        ScopeSignal(
            name="complexity_keywords",
            value=keywords,
            weight=1,
            score=keyword_score,
            rationale=(
                f"Detected complexity keywords ({', '.join(keywords) or 'none'}) "
                f"contribute {keyword_score} points."
            ),
        ),
    ]

    raw_score = sum(signal.score for signal in signals)
    total_score = min(resolved_config.max_total_score, raw_score)
    mode = _mode_from_score(total_score, resolved_config)
    score_band = _score_band(total_score, resolved_config)
    reasons = _build_reasons(signals, mode)
    confidence = _compute_confidence(input_data, total_score, signals, keywords, resolved_config)

    return ScopeDetectionResult(
        contract_version=CONTRACT_VERSION,
        total_score=total_score,
        score_band=score_band,
        mode_recommendation=mode,
        recommendation_reasons=reasons,
        confidence=confidence,
        signals=signals,
    )


def scope_scoring_rubric(*, config: ScopeDetectionConfig | None = None) -> dict[str, Any]:
    """Return a versioned and machine-readable scoring rubric.

    This rubric is the canonical definition for dimension weights, thresholds,
    tie-break behavior, and rationale generation rules used by `detect_scope`.
    """
    resolved_config = config or ScopeDetectionConfig()
    resolved_config.validate()

    rubric_payload = {
        "rubric_version": SCORING_RUBRIC_VERSION,
        "contract_version": CONTRACT_VERSION,
        "aggregation_formula": SCORING_RUBRIC_AGGREGATION_FORMULA,
        "score_bands": _score_band_definitions(resolved_config),
        "tie_break_rule": {
            "classification": SCORING_RUBRIC_TIE_BREAK_RULE,
            "boundary_proximity_confidence_rule": {
                "distance_threshold": resolved_config.confidence_boundary_distance_threshold,
                "penalty": resolved_config.confidence_boundary_penalty,
                "description": (
                    "When a score is within threshold distance from classification boundaries, "
                    "confidence is reduced while mode selection remains deterministic."
                ),
            },
        },
        "rationale_rule": {
            "positive_signal_sorting": "score descending, then signal name ascending",
            "max_primary_reasons": 3,
            "min_reasons": 2,
            "fallback_behavior": (
                "If fewer than two positive signals exist, append mode-specific fallback rationale "
                "until at least two reasons are returned."
            ),
        },
        "dimensions": [
            {
                "name": "timeline_weeks",
                "input_field": "estimated_timeline_weeks",
                "scoring_type": "scaled",
                "raw_formula": "max(0, estimated_timeline_weeks - 1)",
                "weight": resolved_config.timeline_multiplier,
                "cap": resolved_config.timeline_cap,
            },
            {
                "name": "expected_work_items",
                "input_field": "expected_work_items",
                "scoring_type": "scaled",
                "raw_formula": "max(0, expected_work_items - 1)",
                "weight": resolved_config.work_items_multiplier,
                "cap": resolved_config.work_items_cap,
            },
            {
                "name": "dependency_count",
                "input_field": "dependency_count",
                "scoring_type": "scaled",
                "raw_formula": "dependency_count",
                "weight": resolved_config.dependency_multiplier,
                "cap": resolved_config.dependency_cap,
            },
            {
                "name": "integration_surface_count",
                "input_field": "integration_surface_count",
                "scoring_type": "scaled",
                "raw_formula": "integration_surface_count",
                "weight": resolved_config.integration_multiplier,
                "cap": resolved_config.integration_cap,
            },
            {
                "name": "domain_count",
                "input_field": "domain_count",
                "scoring_type": "scaled",
                "raw_formula": "max(0, domain_count - 1)",
                "weight": resolved_config.domain_multiplier,
                "cap": resolved_config.domain_cap,
            },
            {
                "name": "cross_team_count",
                "input_field": "cross_team_count",
                "scoring_type": "scaled",
                "raw_formula": "max(0, cross_team_count - 1)",
                "weight": resolved_config.cross_team_multiplier,
                "cap": resolved_config.cross_team_cap,
            },
            {
                "name": "risk_level",
                "input_field": "risk_level",
                "scoring_type": "mapped",
                "weight_map": {key: resolved_config.risk_weights[key] for key in sorted(resolved_config.risk_weights)},
            },
            {
                "name": "requires_compliance_review",
                "input_field": "requires_compliance_review",
                "scoring_type": "boolean",
                "enabled_score": resolved_config.compliance_score,
            },
            {
                "name": "requires_migration",
                "input_field": "requires_migration",
                "scoring_type": "boolean",
                "enabled_score": resolved_config.migration_score,
            },
            {
                "name": "complexity_keywords",
                "input_field": "description",
                "scoring_type": "keyword_count",
                "keyword_source": sorted(resolved_config.complexity_keywords),
                "weight": 1,
                "cap": resolved_config.keyword_cap,
            },
        ],
    }
    validate_scope_scoring_rubric_payload(rubric_payload, strict=True)
    return rubric_payload


def validate_scope_scoring_rubric_payload(
    payload: Mapping[str, Any],
    *,
    strict: bool = True,
) -> None:
    """Validate rubric payload structure for downstream consumers.

    This helper allows explicit schema validation for channels that consume the
    machine-readable rubric. Any mapping type is supported (e.g., dict-like
    objects). In strict mode, unknown top-level keys are rejected to avoid
    silent contract drift.
    """
    if not isinstance(payload, Mapping):
        raise TypeError("rubric payload must be a mapping")

    payload_keys = set(payload.keys())
    missing_keys = sorted(SCORING_RUBRIC_REQUIRED_KEYS - payload_keys)
    if missing_keys:
        raise ValueError(f"Rubric payload missing required keys: {', '.join(missing_keys)}")

    if strict:
        unknown_keys = sorted(payload_keys - SCORING_RUBRIC_REQUIRED_KEYS)
        if unknown_keys:
            raise ValueError(f"Rubric payload contains unknown keys: {', '.join(unknown_keys)}")

    score_bands = payload.get("score_bands")
    if not isinstance(score_bands, list) or not score_bands:
        raise ValueError("Rubric payload score_bands must be a non-empty list")
    if payload.get("rubric_version") == SCORING_RUBRIC_VERSION and len(score_bands) != 3:
        raise ValueError("Rubric payload score_bands must include exactly 3 entries for v1")
    for band in score_bands:
        if not isinstance(band, Mapping):
            raise ValueError("Each score band must be a mapping")
        if {"mode", "min_score", "max_score"} - set(band.keys()):
            raise ValueError("Each score band must include mode, min_score, and max_score")
        if not isinstance(band["mode"], str):
            raise ValueError("Score band mode must be a string")
        if isinstance(band["min_score"], bool) or not isinstance(band["min_score"], int):
            raise ValueError("Score band min_score must be an integer")
        if isinstance(band["max_score"], bool) or not isinstance(band["max_score"], int):
            raise ValueError("Score band max_score must be an integer")
        if band["min_score"] > band["max_score"]:
            raise ValueError("Score band min_score cannot be greater than max_score")

    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise ValueError("Rubric payload dimensions must be a non-empty list")
    dimension_names: list[str] = []
    for dimension in dimensions:
        if not isinstance(dimension, Mapping):
            raise ValueError("Each dimension entry must be a mapping")
        if "name" not in dimension:
            raise ValueError("Each dimension entry must include a name")
        if not isinstance(dimension["name"], str) or not dimension["name"].strip():
            raise ValueError("Dimension name must be a non-empty string")
        dimension_names.append(dimension["name"].strip())
    if len(set(dimension_names)) != len(dimension_names):
        raise ValueError("Dimension names must be unique")


def scope_detection_config_from_mapping(raw_config: Mapping[str, Any] | None) -> ScopeDetectionConfig:
    """Build ScopeDetectionConfig from a generic mapping."""
    if raw_config is None:
        return ScopeDetectionConfig()
    if not isinstance(raw_config, Mapping):
        raise ValueError("scope_detection config must be a mapping")

    allowed_fields = {field_info.name for field_info in fields(ScopeDetectionConfig)}
    unknown_keys = sorted(set(raw_config.keys()) - allowed_fields)
    if unknown_keys:
        unknown = ", ".join(unknown_keys)
        raise ValueError(f"Unknown scope_detection config keys: {unknown}")

    config_data = dict(raw_config)

    if "complexity_keywords" in config_data:
        raw_keywords = config_data["complexity_keywords"]
        if isinstance(raw_keywords, str):
            keywords = [raw_keywords]
        elif isinstance(raw_keywords, (list, tuple, set, frozenset)):
            keywords = list(raw_keywords)
        else:
            raise TypeError("scope_detection.complexity_keywords must be a string or list of strings")
        if not all(isinstance(keyword, str) for keyword in keywords):
            raise TypeError("scope_detection.complexity_keywords must contain only strings")
        config_data["complexity_keywords"] = frozenset(
            keyword.strip().lower() for keyword in keywords if keyword.strip()
        )

    if "risk_weights" in config_data:
        raw_weights = config_data["risk_weights"]
        if not isinstance(raw_weights, Mapping):
            raise TypeError("scope_detection.risk_weights must be a mapping")
        normalized_weights: dict[str, int] = {}
        for key, value in raw_weights.items():
            if not isinstance(key, str):
                raise TypeError("scope_detection.risk_weights keys must be strings")
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("scope_detection.risk_weights values must be integers")
            normalized_weights[key.strip().lower()] = value
        config_data["risk_weights"] = normalized_weights

    config = ScopeDetectionConfig(**config_data)
    config.validate()
    return config


def load_scope_detection_config(
    project_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> ScopeDetectionConfig:
    """Load ScopeDetectionConfig from merged project configuration files/env."""
    project_config = load_project_config(project_root=project_root, env=env)
    raw_scope_config = project_config.get("scope_detection", {})
    return scope_detection_config_from_mapping(raw_scope_config)


def detect_scope_for_project(
    input_data: ScopeDetectionInput,
    project_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> ScopeDetectionResult:
    """Detect scope using project configuration from .specify/spec-kit.yml."""
    config = load_scope_detection_config(project_root=project_root, env=env)
    return detect_scope(input_data, config=config)


def _scaled_score(raw: int, multiplier: int, cap: int) -> int:
    """Scale an integer signal by multiplier and clamp to a cap."""
    return min(cap, max(0, raw * multiplier))


def _matched_keywords(description: str, keywords: set[str] | frozenset[str]) -> list[str]:
    """Find configured keywords using whole-keyword regex matching.

    This prevents false positives from substring matching (e.g., 'sso' in
    'blossom').
    """
    matches: list[str] = []
    for keyword in keywords:
        pattern = rf"(?<![a-z0-9-]){re.escape(keyword)}(?![a-z0-9-])"
        if re.search(pattern, description):
            matches.append(keyword)
    return sorted(set(matches))


def _mode_from_score(score: int, config: ScopeDetectionConfig) -> ScopeMode:
    """Map score to scope mode using configured boundaries."""
    if score <= config.feature_max_score:
        return ScopeMode.FEATURE
    if score <= config.epic_max_score:
        return ScopeMode.EPIC
    return ScopeMode.PROGRAM


def _score_band(score: int, config: ScopeDetectionConfig) -> str:
    """Return score band label for the configured boundaries."""
    if score <= config.feature_max_score:
        return f"0-{config.feature_max_score}"
    if score <= config.epic_max_score:
        return f"{config.feature_max_score + 1}-{config.epic_max_score}"
    return f"{config.epic_max_score + 1}+"


def _build_reasons(signals: list[ScopeSignal], mode: ScopeMode) -> list[str]:
    """Build 2-3 human-readable recommendation reasons."""
    positive_signals = [signal for signal in signals if signal.score > 0]
    positive_signals.sort(key=lambda signal: (-signal.score, signal.name))

    reasons = [signal.rationale for signal in positive_signals[:3]]
    if len(reasons) < 2:
        if mode == ScopeMode.FEATURE:
            reasons.append(
                "Dependency, risk, and coordination signals remain low; "
                "it is viable to proceed as a single feature."
            )
        elif mode == ScopeMode.EPIC:
            reasons.append(
                "Intermediate complexity with multiple relevant vectors; "
                "decomposing into features before final tasks is recommended."
            )
        else:
            reasons.append(
                "High aggregate complexity suggests program-level structuring "
                "with progressive decomposition into epics and features."
            )

    if len(reasons) < 2:
        reasons.append("Structured signals were used to produce a deterministic recommendation.")

    return reasons[:3]


def _compute_confidence(
    input_data: ScopeDetectionInput,
    score: int,
    signals: list[ScopeSignal],
    keywords: list[str],
    config: ScopeDetectionConfig,
) -> float:
    """Compute confidence using configured heuristics and boundary proximity."""
    active_signals = sum(1 for signal in signals if signal.score > 0)
    boundary_points = (
        config.feature_max_score,
        config.feature_max_score + 1,
        config.epic_max_score,
        config.epic_max_score + 1,
    )
    boundary_distance = min(abs(score - point) for point in boundary_points)

    confidence = config.confidence_base
    confidence += min(config.confidence_active_signal_cap, active_signals * config.confidence_active_signal_step)
    confidence += min(config.confidence_keyword_cap, len(keywords) * config.confidence_keyword_step)
    if boundary_distance <= config.confidence_boundary_distance_threshold:
        confidence -= config.confidence_boundary_penalty
    if len(input_data.description.split()) < config.confidence_short_description_word_threshold:
        confidence -= config.confidence_short_description_penalty

    return round(min(config.confidence_max, max(config.confidence_min, confidence)), 2)


def _score_band_definitions(config: ScopeDetectionConfig) -> list[dict[str, Any]]:
    """Return machine-readable score band boundaries."""
    return [
        {"mode": ScopeMode.FEATURE.value, "min_score": 0, "max_score": config.feature_max_score},
        {
            "mode": ScopeMode.EPIC.value,
            "min_score": config.feature_max_score + 1,
            "max_score": config.epic_max_score,
        },
        {
            "mode": ScopeMode.PROGRAM.value,
            "min_score": config.epic_max_score + 1,
            "max_score": config.max_total_score,
        },
    ]
