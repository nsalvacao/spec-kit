"""Program/Epic/Feature hierarchy metadata contract (issue #107)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
import re
from typing import Any, Mapping


HIERARCHY_CONTRACT_VERSION = "program-epic-feature.v1"
HIERARCHY_ALLOWED_TOP_LEVEL_FIELDS = frozenset({"contract_version", "mode", "program", "epics", "features"})


class HierarchyMode(str, Enum):
    """Supported orchestration hierarchy modes."""

    FEATURE = "feature"
    EPIC = "epic"
    PROGRAM = "program"


@dataclass(frozen=True)
class ArtifactRefs:
    """Canonical artifact references for a feature execution unit."""

    spec: str
    plan: str
    tasks: str

    def to_dict(self) -> dict[str, str]:
        return {"spec": self.spec, "plan": self.plan, "tasks": self.tasks}


@dataclass(frozen=True)
class LineageMetadata:
    """Lineage metadata for decomposition traceability."""

    origin: str
    parent_id: str | None
    depth: int
    source_decision: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "source_decision": self.source_decision,
        }


@dataclass(frozen=True)
class ProgramMetadata:
    """Top-level Program metadata."""

    id: str
    title: str
    status: str
    owner: str
    epic_ids: list[str]
    lineage: LineageMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "owner": self.owner,
            "epic_ids": self.epic_ids,
            "lineage": self.lineage.to_dict(),
        }


@dataclass(frozen=True)
class EpicMetadata:
    """Epic metadata and its parent/children relations."""

    id: str
    title: str
    status: str
    owner: str
    program_id: str
    feature_ids: list[str]
    lineage: LineageMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "owner": self.owner,
            "program_id": self.program_id,
            "feature_ids": self.feature_ids,
            "lineage": self.lineage.to_dict(),
        }


@dataclass(frozen=True)
class FeatureMetadata:
    """Feature metadata and canonical artifact references."""

    id: str
    title: str
    status: str
    owner: str
    program_id: str | None
    epic_id: str | None
    artifacts: ArtifactRefs
    lineage: LineageMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "owner": self.owner,
            "program_id": self.program_id,
            "epic_id": self.epic_id,
            "artifacts": self.artifacts.to_dict(),
            "lineage": self.lineage.to_dict(),
        }


@dataclass(frozen=True)
class HierarchyMetadataContract:
    """Versioned Program/Epic/Feature hierarchy metadata contract."""

    contract_version: str
    mode: HierarchyMode
    features: list[FeatureMetadata]
    epics: list[EpicMetadata] = field(default_factory=list)
    program: ProgramMetadata | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_version": self.contract_version,
            "mode": self.mode.value,
            "epics": [epic.to_dict() for epic in self.epics],
            "features": [feature.to_dict() for feature in self.features],
        }
        if self.program is not None:
            payload["program"] = self.program.to_dict()
        return payload


def build_feature_hierarchy_contract(
    *,
    feature_id: str,
    title: str,
    owner: str,
    status: str = "draft",
    source_decision: str = "feature_mode",
) -> HierarchyMetadataContract:
    """Build a canonical contract for standalone feature execution."""
    normalized_feature_id = _normalize_identifier(feature_id, field_name="feature.id")
    feature = FeatureMetadata(
        id=normalized_feature_id,
        title=_normalize_non_empty_string(title, field_name="feature.title"),
        status=_normalize_non_empty_string(status, field_name="feature.status"),
        owner=_normalize_non_empty_string(owner, field_name="feature.owner"),
        program_id=None,
        epic_id=None,
        artifacts=_normalize_artifact_refs({}, feature_id=normalized_feature_id),
        lineage=LineageMetadata(
            origin="specify",
            parent_id=None,
            depth=0,
            source_decision=_normalize_non_empty_string(source_decision, field_name="feature.lineage.source_decision"),
        ),
    )
    return HierarchyMetadataContract(
        contract_version=HIERARCHY_CONTRACT_VERSION,
        mode=HierarchyMode.FEATURE,
        features=[feature],
    )


def normalize_hierarchy_contract_payload(
    raw_payload: Mapping[str, Any],
    *,
    strict: bool = False,
) -> HierarchyMetadataContract:
    """Normalize external hierarchy payload into canonical contract."""
    if not isinstance(raw_payload, Mapping):
        raise TypeError("hierarchy payload must be a mapping")

    if strict:
        unknown_keys = sorted(set(raw_payload.keys()) - HIERARCHY_ALLOWED_TOP_LEVEL_FIELDS)
        if unknown_keys:
            raise ValueError(f"Unknown hierarchy contract fields: {', '.join(unknown_keys)}")

    contract_version = raw_payload.get("contract_version", HIERARCHY_CONTRACT_VERSION)
    if not isinstance(contract_version, str) or not contract_version.strip():
        raise ValueError("contract_version must be a non-empty string")
    contract_version = contract_version.strip()

    mode = _coerce_mode(raw_payload.get("mode", HierarchyMode.FEATURE.value))
    program = _normalize_program(raw_payload.get("program"))
    epics = _normalize_epics(raw_payload.get("epics"))
    features = _normalize_features(raw_payload.get("features"))

    contract = HierarchyMetadataContract(
        contract_version=contract_version,
        mode=mode,
        program=program,
        epics=epics,
        features=features,
    )
    _validate_invariants(contract)
    return contract


def validate_hierarchy_contract_payload(
    payload: Mapping[str, Any],
    *,
    strict: bool = True,
) -> list[str]:
    """Validate hierarchy contract payload and return error list."""
    try:
        normalize_hierarchy_contract_payload(payload, strict=strict)
        return []
    except (TypeError, ValueError) as exc:
        if strict:
            raise
        return [str(exc)]


def _normalize_program(raw_program: Any) -> ProgramMetadata | None:
    if raw_program is None:
        return None
    if not isinstance(raw_program, Mapping):
        raise TypeError("program must be a mapping")

    program_id = _normalize_identifier(raw_program.get("id"), field_name="program.id")
    lineage = _normalize_lineage(
        raw_program.get("lineage"),
        default_parent_id=None,
        default_depth=0,
        field_name_prefix="program.lineage",
    )
    if lineage.depth != 0:
        raise ValueError("program.lineage.depth must be 0")

    return ProgramMetadata(
        id=program_id,
        title=_normalize_non_empty_string(raw_program.get("title"), field_name="program.title"),
        status=_normalize_non_empty_string(raw_program.get("status", "draft"), field_name="program.status"),
        owner=_normalize_non_empty_string(raw_program.get("owner", "unassigned"), field_name="program.owner"),
        epic_ids=_normalize_identifier_list(raw_program.get("epic_ids", []), field_name="program.epic_ids"),
        lineage=lineage,
    )


def _normalize_epics(raw_epics: Any) -> list[EpicMetadata]:
    if raw_epics is None:
        return []
    if not isinstance(raw_epics, list):
        raise TypeError("epics must be a list")

    normalized: list[EpicMetadata] = []
    for index, raw_epic in enumerate(raw_epics):
        field_prefix = f"epics[{index}]"
        if not isinstance(raw_epic, Mapping):
            raise TypeError(f"{field_prefix} must be a mapping")
        epic_id = _normalize_identifier(raw_epic.get("id"), field_name=f"{field_prefix}.id")
        program_id = _normalize_identifier(raw_epic.get("program_id"), field_name=f"{field_prefix}.program_id")
        lineage = _normalize_lineage(
            raw_epic.get("lineage"),
            default_parent_id=program_id,
            default_depth=1,
            field_name_prefix=f"{field_prefix}.lineage",
        )
        normalized.append(
            EpicMetadata(
                id=epic_id,
                title=_normalize_non_empty_string(raw_epic.get("title"), field_name=f"{field_prefix}.title"),
                status=_normalize_non_empty_string(raw_epic.get("status", "draft"), field_name=f"{field_prefix}.status"),
                owner=_normalize_non_empty_string(raw_epic.get("owner", "unassigned"), field_name=f"{field_prefix}.owner"),
                program_id=program_id,
                feature_ids=_normalize_identifier_list(raw_epic.get("feature_ids", []), field_name=f"{field_prefix}.feature_ids"),
                lineage=lineage,
            )
        )
    return normalized


def _normalize_features(raw_features: Any) -> list[FeatureMetadata]:
    if raw_features is None:
        return []
    if not isinstance(raw_features, list):
        raise TypeError("features must be a list")

    normalized: list[FeatureMetadata] = []
    for index, raw_feature in enumerate(raw_features):
        field_prefix = f"features[{index}]"
        if not isinstance(raw_feature, Mapping):
            raise TypeError(f"{field_prefix} must be a mapping")
        feature_id = _normalize_identifier(raw_feature.get("id"), field_name=f"{field_prefix}.id")
        epic_id = _normalize_optional_identifier(raw_feature.get("epic_id"), field_name=f"{field_prefix}.epic_id")
        program_id = _normalize_optional_identifier(raw_feature.get("program_id"), field_name=f"{field_prefix}.program_id")
        default_parent_id = epic_id or program_id
        default_depth = 2 if epic_id else (1 if program_id else 0)
        lineage = _normalize_lineage(
            raw_feature.get("lineage"),
            default_parent_id=default_parent_id,
            default_depth=default_depth,
            field_name_prefix=f"{field_prefix}.lineage",
        )
        normalized.append(
            FeatureMetadata(
                id=feature_id,
                title=_normalize_non_empty_string(raw_feature.get("title"), field_name=f"{field_prefix}.title"),
                status=_normalize_non_empty_string(
                    raw_feature.get("status", "draft"),
                    field_name=f"{field_prefix}.status",
                ),
                owner=_normalize_non_empty_string(
                    raw_feature.get("owner", "unassigned"),
                    field_name=f"{field_prefix}.owner",
                ),
                program_id=program_id,
                epic_id=epic_id,
                artifacts=_normalize_artifact_refs(raw_feature.get("artifacts", {}), feature_id=feature_id),
                lineage=lineage,
            )
        )
    return normalized


def _normalize_artifact_refs(raw_artifacts: Any, *, feature_id: str) -> ArtifactRefs:
    if raw_artifacts is None:
        raw_artifacts = {}
    if not isinstance(raw_artifacts, Mapping):
        raise TypeError("feature.artifacts must be a mapping")

    return ArtifactRefs(
        spec=_normalize_artifact_path(
            raw_artifacts.get("spec", f"specs/{feature_id}/spec.md"),
            feature_id=feature_id,
            artifact_name="spec",
        ),
        plan=_normalize_artifact_path(
            raw_artifacts.get("plan", f"specs/{feature_id}/plan.md"),
            feature_id=feature_id,
            artifact_name="plan",
        ),
        tasks=_normalize_artifact_path(
            raw_artifacts.get("tasks", f"specs/{feature_id}/tasks.md"),
            feature_id=feature_id,
            artifact_name="tasks",
        ),
    )


def _normalize_artifact_path(value: Any, *, feature_id: str, artifact_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"feature.artifacts.{artifact_name} must be a non-empty string")
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute():
        raise ValueError(f"feature.artifacts.{artifact_name} must be relative")
    if ".." in path.parts:
        raise ValueError(f"feature.artifacts.{artifact_name} cannot contain parent traversal")

    expected = {
        "spec": f"specs/{feature_id}/spec.md",
        "plan": f"specs/{feature_id}/plan.md",
        "tasks": f"specs/{feature_id}/tasks.md",
    }[artifact_name]
    if path.as_posix() != expected:
        raise ValueError(
            f"feature.artifacts.{artifact_name} must be canonical path '{expected}'"
        )
    return path.as_posix()


def _normalize_lineage(
    raw_lineage: Any,
    *,
    default_parent_id: str | None,
    default_depth: int,
    field_name_prefix: str,
) -> LineageMetadata:
    if raw_lineage is None:
        raw_lineage = {}
    if not isinstance(raw_lineage, Mapping):
        raise TypeError(f"{field_name_prefix} must be a mapping")

    origin = _normalize_non_empty_string(raw_lineage.get("origin", "specify"), field_name=f"{field_name_prefix}.origin")
    source_decision = _normalize_non_empty_string(
        raw_lineage.get("source_decision", "unspecified"),
        field_name=f"{field_name_prefix}.source_decision",
    )
    parent_id = raw_lineage.get("parent_id", default_parent_id)
    parent_id = _normalize_optional_identifier(parent_id, field_name=f"{field_name_prefix}.parent_id")

    depth_value = raw_lineage.get("depth", default_depth)
    if isinstance(depth_value, bool) or not isinstance(depth_value, int):
        raise TypeError(f"{field_name_prefix}.depth must be an integer")
    if depth_value < 0:
        raise ValueError(f"{field_name_prefix}.depth must be >= 0")

    return LineageMetadata(
        origin=origin,
        parent_id=parent_id,
        depth=depth_value,
        source_decision=source_decision,
    )


def _validate_invariants(contract: HierarchyMetadataContract) -> None:
    if not contract.features:
        raise ValueError("Hierarchy contract must include at least one feature")

    feature_ids = [feature.id for feature in contract.features]
    if len(set(feature_ids)) != len(feature_ids):
        raise ValueError("Feature IDs must be unique")

    epic_ids = [epic.id for epic in contract.epics]
    if len(set(epic_ids)) != len(epic_ids):
        raise ValueError("Epic IDs must be unique")

    if contract.mode == HierarchyMode.FEATURE and len(contract.features) != 1:
        raise ValueError("feature mode requires exactly one feature")

    if contract.mode in {HierarchyMode.EPIC, HierarchyMode.PROGRAM}:
        if contract.program is None:
            raise ValueError("epic/program mode requires program metadata")
        if not contract.epics:
            raise ValueError("epic/program mode requires at least one epic")

    if contract.program is not None:
        program_id = contract.program.id
        if contract.program.epic_ids and set(contract.program.epic_ids) != set(epic_ids):
            raise ValueError("program.epic_ids must match declared epics")
        for epic in contract.epics:
            if epic.program_id != program_id:
                raise ValueError(f"Epic '{epic.id}' must reference parent program '{program_id}'")
        for feature in contract.features:
            if feature.program_id and feature.program_id != program_id:
                raise ValueError(f"Feature '{feature.id}' must reference parent program '{program_id}'")
    elif contract.epics:
        raise ValueError("epics require a parent program")

    epic_id_set = set(epic_ids)
    features_by_epic: dict[str, set[str]] = {epic.id: set() for epic in contract.epics}
    for feature in contract.features:
        if feature.epic_id is not None:
            if feature.epic_id not in epic_id_set:
                raise ValueError(f"Feature '{feature.id}' references unknown epic '{feature.epic_id}'")
            features_by_epic[feature.epic_id].add(feature.id)

    for epic in contract.epics:
        if epic.feature_ids and set(epic.feature_ids) != features_by_epic.get(epic.id, set()):
            raise ValueError(f"epic.feature_ids for '{epic.id}' must match declared feature links")


def _coerce_mode(value: Any) -> HierarchyMode:
    if isinstance(value, HierarchyMode):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for mode in HierarchyMode:
            if normalized == mode.value:
                return mode
    raise ValueError("mode must be one of: feature, epic, program")


def _normalize_identifier(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise ValueError(f"{field_name} must include at least one alphanumeric character")
    return normalized


def _normalize_optional_identifier(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _normalize_identifier(value, field_name=field_name)


def _normalize_identifier_list(value: Any, *, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    return [_normalize_identifier(item, field_name=f"{field_name}[]") for item in value]


def _normalize_non_empty_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()
