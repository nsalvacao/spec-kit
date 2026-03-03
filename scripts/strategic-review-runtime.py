#!/usr/bin/env python3
"""Runtime helpers for native strategic-review scaffold/validation flows.

This script is intentionally placed at `scripts/` root so release packaging
copies it for both shell variants.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover - fallback path
    yaml = None


ENV_PREFIX = "SPECIFY_CONFIG__"

DIMENSION_LABELS: dict[str, str] = {
    "output_quality": "Output quality",
    "readme_docs_quality": "README/docs quality",
    "developer_experience": "Developer experience",
    "security_trust": "Security/trust",
    "competitive_positioning": "Competitive positioning",
    "test_coverage": "Test coverage",
}

SECTION_PATTERNS = (
    r"^## 1\. Output Quality Evaluation$",
    r"^## 2\. Cross-Output Consistency$",
    r"^## 3\. README Conversion Audit$",
    r"^## 4\. Developer Experience Audit$",
    r"^## 5\. Security & Trust Audit$",
    r"^## 6\. Competitive Positioning$",
    r"^## 7\. Launch Readiness Scorecard$",
    r"^## 8\. Action Items$",
)

DEFAULT_CONFIG: dict[str, Any] = {
    "weights": {
        "output_quality": 0.25,
        "readme_docs_quality": 0.20,
        "developer_experience": 0.20,
        "security_trust": 0.15,
        "competitive_positioning": 0.10,
        "test_coverage": 0.10,
    },
    "thresholds": {
        "green_min_score": 4.0,
        "yellow_min_score": 3.0,
    },
    "blockers": {
        "emit_on_bands": ["YELLOW", "RED"],
        "max_items": 20,
    },
    "validator": {
        "min_sections": 8,
        "min_line_count": 120,
    },
}

MIN_PYTHON = (3, 9)

OVERALL_SCORE_PATTERN = re.compile(r"^\*\*Overall Score:\*\*\s*([0-9]+(?:\.[0-9]+)?)\s*$")
BAND_PATTERN = re.compile(r"^\*\*Band:\*\*\s*(GREEN|YELLOW|RED)\s*$")
DATE_PATTERN = re.compile(r"^\*\*Date:\*\*\s*(.+?)\s*$")
TOTAL_ROW_PATTERN = re.compile(r"^\|\s*\*\*TOTAL\*\*\s*\|")


class StrategicReviewRuntimeError(Exception):
    """Raised for deterministic validation/configuration errors."""


@dataclass(frozen=True)
class ValidationResult:
    overall_score: float
    computed_band: str
    launch_blockers_path: Path | None
    blockers_written: int


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        raise StrategicReviewRuntimeError(
            f"Cannot parse YAML config at {path}: 'pyyaml' is not available."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise StrategicReviewRuntimeError(
            f"Config file {path} must contain a top-level mapping."
        )
    return dict(raw)


def _parse_env_value(raw: str) -> Any:
    if yaml is None:
        return raw
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw


def _set_nested_value(target: dict[str, Any], segments: list[str], value: Any) -> None:
    cursor = target
    for segment in segments[:-1]:
        if segment not in cursor or not isinstance(cursor[segment], dict):
            cursor[segment] = {}
        cursor = cursor[segment]
    cursor[segments[-1]] = value


def _fallback_load_raw_strategic_review_config(project_root: Path) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for rel_path in (".specify/spec-kit.yml", ".specify/spec-kit.local.yml"):
        file_config = _load_yaml_mapping(project_root / rel_path)
        strategic = file_config.get("strategic_review")
        if isinstance(strategic, Mapping):
            merged = _deep_merge(merged, dict(strategic))

    env_overrides: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(ENV_PREFIX):
            continue
        remainder = key[len(ENV_PREFIX):]
        if not remainder:
            continue
        segments = [segment.strip().lower() for segment in remainder.split("__") if segment.strip()]
        if len(segments) < 2 or segments[0] != "strategic_review":
            continue
        _set_nested_value(env_overrides, segments[1:], _parse_env_value(value))

    if env_overrides:
        merged = _deep_merge(merged, env_overrides)
    return merged


def _load_raw_strategic_review_config(project_root: Path) -> dict[str, Any]:
    try:
        from specify_cli.project_config import load_project_config
    except Exception:
        return _fallback_load_raw_strategic_review_config(project_root)

    try:
        loaded = load_project_config(project_root=project_root)
    except Exception:
        return _fallback_load_raw_strategic_review_config(project_root)

    strategic = loaded.get("strategic_review")
    if strategic is None:
        return {}
    if not isinstance(strategic, Mapping):
        raise StrategicReviewRuntimeError(
            "Merged configuration key 'strategic_review' must be a mapping."
        )
    return dict(strategic)


def _normalize_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise StrategicReviewRuntimeError(f"{field_name} must be numeric.")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            return float(text)
        except ValueError as exc:
            raise StrategicReviewRuntimeError(f"{field_name} must be numeric.") from exc
    raise StrategicReviewRuntimeError(f"{field_name} must be numeric.")


def _normalize_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise StrategicReviewRuntimeError(f"{field_name} must be an integer.")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise StrategicReviewRuntimeError(f"{field_name} must be an integer.")


def _normalize_bands(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        entries = [item.strip().upper() for item in value.split(",") if item.strip()]
    elif isinstance(value, (list, tuple)):
        entries = []
        for item in value:
            if not isinstance(item, str):
                raise StrategicReviewRuntimeError(f"{field_name} entries must be strings.")
            normalized = item.strip().upper()
            if normalized:
                entries.append(normalized)
    else:
        raise StrategicReviewRuntimeError(f"{field_name} must be a list or comma-separated string.")

    allowed = {"GREEN", "YELLOW", "RED"}
    invalid = sorted(set(entries) - allowed)
    if invalid:
        raise StrategicReviewRuntimeError(
            f"{field_name} contains unsupported values: {', '.join(invalid)}."
        )
    return entries


def resolve_strategic_review_config(project_root: Path) -> dict[str, Any]:
    merged = _deep_merge(DEFAULT_CONFIG, _load_raw_strategic_review_config(project_root))

    weights_raw = merged.get("weights")
    if not isinstance(weights_raw, Mapping):
        raise StrategicReviewRuntimeError("strategic_review.weights must be a mapping.")
    weights: dict[str, float] = {}
    for key in DIMENSION_LABELS:
        if key not in weights_raw:
            raise StrategicReviewRuntimeError(f"strategic_review.weights.{key} is required.")
        value = _normalize_float(weights_raw[key], f"strategic_review.weights.{key}")
        if value <= 0:
            raise StrategicReviewRuntimeError(
                f"strategic_review.weights.{key} must be greater than zero."
            )
        weights[key] = value

    total_weight = sum(weights.values())
    if not math.isclose(total_weight, 1.0, rel_tol=1e-9, abs_tol=1e-6):
        raise StrategicReviewRuntimeError(
            f"strategic_review.weights must sum to 1.0 (found {total_weight:.6f})."
        )

    thresholds_raw = merged.get("thresholds")
    if not isinstance(thresholds_raw, Mapping):
        raise StrategicReviewRuntimeError("strategic_review.thresholds must be a mapping.")
    green_min = _normalize_float(
        thresholds_raw.get("green_min_score"), "strategic_review.thresholds.green_min_score"
    )
    yellow_min = _normalize_float(
        thresholds_raw.get("yellow_min_score"), "strategic_review.thresholds.yellow_min_score"
    )
    if not (0 <= yellow_min <= 5 and 0 <= green_min <= 5):
        raise StrategicReviewRuntimeError(
            "strategic_review threshold scores must be between 0 and 5."
        )
    if yellow_min > green_min:
        raise StrategicReviewRuntimeError(
            "strategic_review.thresholds.yellow_min_score must be <= green_min_score."
        )

    blockers_raw = merged.get("blockers")
    if not isinstance(blockers_raw, Mapping):
        raise StrategicReviewRuntimeError("strategic_review.blockers must be a mapping.")
    emit_on_bands = _normalize_bands(
        blockers_raw.get("emit_on_bands"), "strategic_review.blockers.emit_on_bands"
    )
    max_items = _normalize_int(
        blockers_raw.get("max_items"), "strategic_review.blockers.max_items"
    )
    if max_items < 1 or max_items > 200:
        raise StrategicReviewRuntimeError(
            "strategic_review.blockers.max_items must be between 1 and 200."
        )

    validator_raw = merged.get("validator")
    if not isinstance(validator_raw, Mapping):
        raise StrategicReviewRuntimeError("strategic_review.validator must be a mapping.")
    min_sections = _normalize_int(
        validator_raw.get("min_sections"), "strategic_review.validator.min_sections"
    )
    min_line_count = _normalize_int(
        validator_raw.get("min_line_count"), "strategic_review.validator.min_line_count"
    )
    if min_sections < len(SECTION_PATTERNS):
        raise StrategicReviewRuntimeError(
            "strategic_review.validator.min_sections must be >= required section count."
        )
    if min_line_count < 40 or min_line_count > 5000:
        raise StrategicReviewRuntimeError(
            "strategic_review.validator.min_line_count must be between 40 and 5000."
        )

    return {
        "weights": weights,
        "thresholds": {
            "green_min_score": green_min,
            "yellow_min_score": yellow_min,
        },
        "blockers": {
            "emit_on_bands": emit_on_bands,
            "max_items": max_items,
        },
        "validator": {
            "min_sections": min_sections,
            "min_line_count": min_line_count,
        },
    }


def _extract_section(lines: list[str], start_pattern: str, end_pattern: str | None) -> list[str]:
    in_section = False
    collected: list[str] = []
    start_re = re.compile(start_pattern)
    end_re = re.compile(end_pattern) if end_pattern else None

    for line in lines:
        if not in_section and start_re.match(line):
            in_section = True
            continue
        if in_section and end_re and end_re.match(line):
            break
        if in_section:
            collected.append(line)
    return collected


def _determine_band(score: float, config: Mapping[str, Any]) -> str:
    thresholds = config["thresholds"]
    if score >= thresholds["green_min_score"]:
        return "GREEN"
    if score >= thresholds["yellow_min_score"]:
        return "YELLOW"
    return "RED"


def _parse_row_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    chunks = [chunk.strip() for chunk in stripped.strip("|").split("|")]
    return chunks


def validate_review_file(*, file_path: Path, project_root: Path, config: Mapping[str, Any]) -> ValidationResult:
    if not file_path.exists():
        raise StrategicReviewRuntimeError(f"Review file not found: {file_path}")

    resolved_project_root = project_root.resolve()
    resolved_file = file_path.resolve()
    if not resolved_file.is_relative_to(resolved_project_root):
        raise StrategicReviewRuntimeError(
            f"Refusing to validate file outside project root: {resolved_file}"
        )

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < config["validator"]["min_line_count"]:
        raise StrategicReviewRuntimeError(
            "Document depth is insufficient: "
            f"expected >= {config['validator']['min_line_count']} lines, found {len(lines)}."
        )
    if re.search(r"\bTODO:", text):
        raise StrategicReviewRuntimeError("Document still contains TODO placeholders.")

    for pattern in SECTION_PATTERNS:
        if not re.search(pattern, text, flags=re.MULTILINE):
            raise StrategicReviewRuntimeError(
                f"Missing required section matching pattern: {pattern}"
            )

    overall_score: float | None = None
    reported_band: str | None = None
    report_date = "unknown date"
    for line in lines:
        score_match = OVERALL_SCORE_PATTERN.match(line.strip())
        if score_match:
            overall_score = float(score_match.group(1))
        band_match = BAND_PATTERN.match(line.strip())
        if band_match:
            reported_band = band_match.group(1)
        date_match = DATE_PATTERN.match(line.strip())
        if date_match:
            report_date = date_match.group(1)

    if overall_score is None:
        raise StrategicReviewRuntimeError("Missing '**Overall Score:** <value>' header line.")
    if reported_band is None:
        raise StrategicReviewRuntimeError("Missing '**Band:** <GREEN|YELLOW|RED>' header line.")

    score_section = _extract_section(
        lines,
        r"^## 7\. Launch Readiness Scorecard$",
        r"^## 8\. Action Items$",
    )
    if not score_section:
        raise StrategicReviewRuntimeError("Launch Readiness Scorecard section is empty.")

    label_to_key = {label: key for key, label in DIMENSION_LABELS.items()}
    parsed_scores: dict[str, float] = {}
    parsed_weights: dict[str, float] = {}
    reported_total_weighted: float | None = None
    for line in score_section:
        cells = _parse_row_cells(line)
        if len(cells) < 4:
            continue
        first = cells[0]
        if first in ("Category", "---"):
            continue
        if TOTAL_ROW_PATTERN.match(line):
            try:
                reported_total_weighted = float(cells[3])
            except ValueError as exc:
                raise StrategicReviewRuntimeError(
                    "TOTAL row weighted value must be numeric."
                ) from exc
            continue
        key = label_to_key.get(first)
        if key is None:
            continue
        try:
            score_value = float(cells[1])
            weight_value = float(cells[2])
        except ValueError as exc:
            raise StrategicReviewRuntimeError(
                f"Scorecard row for '{first}' must contain numeric score and weight."
            ) from exc
        if score_value < 1 or score_value > 5:
            raise StrategicReviewRuntimeError(
                f"Score for '{first}' must be between 1 and 5."
            )
        parsed_scores[key] = score_value
        parsed_weights[key] = weight_value

    missing = [label for key, label in DIMENSION_LABELS.items() if key not in parsed_scores]
    if missing:
        raise StrategicReviewRuntimeError(
            f"Missing scorecard rows for categories: {', '.join(missing)}."
        )

    for key, configured_weight in config["weights"].items():
        reported_weight = parsed_weights[key]
        if not math.isclose(reported_weight, configured_weight, rel_tol=1e-9, abs_tol=1e-4):
            raise StrategicReviewRuntimeError(
                "Scorecard weight mismatch for "
                f"'{DIMENSION_LABELS[key]}': expected {configured_weight:.4f}, found {reported_weight:.4f}."
            )

    computed_score = sum(parsed_scores[key] * config["weights"][key] for key in DIMENSION_LABELS)
    if not math.isclose(overall_score, computed_score, rel_tol=1e-9, abs_tol=0.05):
        raise StrategicReviewRuntimeError(
            f"Overall score mismatch: header reports {overall_score:.2f}, "
            f"computed from scorecard is {computed_score:.2f}."
        )

    if reported_total_weighted is not None and not math.isclose(
        reported_total_weighted, computed_score, rel_tol=1e-9, abs_tol=0.05
    ):
        raise StrategicReviewRuntimeError(
            f"TOTAL weighted mismatch: table reports {reported_total_weighted:.2f}, "
            f"computed is {computed_score:.2f}."
        )

    computed_band = _determine_band(computed_score, config)
    if reported_band != computed_band:
        raise StrategicReviewRuntimeError(
            f"Band mismatch: header reports {reported_band}, expected {computed_band} from thresholds."
        )

    blockers_section = _extract_section(
        lines,
        r"^### Blockers \(MUST fix\)$",
        r"^### ",
    )
    blockers = []
    for line in blockers_section:
        match = re.match(r"^\d+\.\s+(.+?)\s*$", line)
        if match:
            blockers.append(match.group(1))

    blockers_path = resolved_project_root / ".ideas" / "launch-blockers.md"
    blockers_written = 0
    if computed_band in config["blockers"]["emit_on_bands"]:
        if not blockers:
            raise StrategicReviewRuntimeError(
                "Band requires blocker emission but no numbered blocker items were found "
                "under '### Blockers (MUST fix)'."
            )
        limited_blockers = blockers[: config["blockers"]["max_items"]]
        blockers_path.parent.mkdir(parents=True, exist_ok=True)
        content_lines = [
            "---",
            "artifact: launch_blockers",
            "phase: strategy",
            'schema_version: "1.0"',
            f"generated_from: {file_path.relative_to(resolved_project_root).as_posix()}",
            f"band: {computed_band}",
            f"overall_score: {computed_score:.2f}",
            "---",
            "",
            f"# Launch Blockers ({computed_band})",
            "",
            f"Date: {report_date}",
            "",
            "## Blocking Items",
            "",
        ]
        for idx, item in enumerate(limited_blockers, start=1):
            content_lines.append(f"{idx}. {item}")
        blockers_path.write_text("\n".join(content_lines) + "\n", encoding="utf-8")
        blockers_written = len(limited_blockers)
    else:
        if blockers_path.exists():
            blockers_path.unlink()

    return ValidationResult(
        overall_score=round(computed_score, 4),
        computed_band=computed_band,
        launch_blockers_path=blockers_path if blockers_written else None,
        blockers_written=blockers_written,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Runtime helpers for strategic-review config and validation."
    )
    parser.add_argument(
        "--mode",
        choices=("config", "validate"),
        required=True,
        help="Operation mode.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root path (default: current directory).",
    )
    parser.add_argument(
        "--file",
        default=".ideas/evaluation-results.md",
        help="Strategic-review artifact path for validation mode.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        print(
            f"Error: strategic-review runtime requires Python >= {required}.",
            file=sys.stderr,
        )
        return 1

    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    project_root = Path(args.project_root).resolve()

    try:
        config = resolve_strategic_review_config(project_root)
        if args.mode == "config":
            print(json.dumps(config, indent=2, sort_keys=True))
            return 0

        review_file = (project_root / args.file).resolve()
        result = validate_review_file(
            file_path=review_file,
            project_root=project_root,
            config=config,
        )
        print(
            "Strategic review validation passed "
            f"(score={result.overall_score:.2f}, band={result.computed_band})"
        )
        if result.launch_blockers_path is not None:
            print(
                f"Launch blockers artifact generated at "
                f"{result.launch_blockers_path.relative_to(project_root)} "
                f"with {result.blockers_written} item(s)."
            )
        return 0
    except StrategicReviewRuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error: unexpected strategic-review runtime failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
