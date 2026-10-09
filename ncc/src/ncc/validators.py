from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .models import Concept, Facet, Indicator


@dataclass
class ValidationIssue:
    severity: str  # 'error', 'warning', 'info'
    code: str
    message: str
    path: str  # e.g. 'facets[0].indicators[2]'


@dataclass
class ValidationResult:
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)


def validate_concept(concept: Concept) -> ValidationResult:
    issues: List[ValidationIssue] = []

    if not concept.facets:
        issues.append(ValidationIssue("error", "E001", "Concept has no facets.", "facets"))

    seen_facet_names: set[str] = set()
    for fi, facet in enumerate(concept.facets):
        fpath = f"facets[{fi}]"
        if not facet.indicators:
            issues.append(ValidationIssue("error", "E002", f"Facet '{facet.name}' has no indicators.", fpath))
        if facet.name in seen_facet_names:
            issues.append(ValidationIssue("error", "E003", f"Duplicate facet name '{facet.name}'.", fpath))
        seen_facet_names.add(facet.name)

        seen_ind_names: set[str] = set()
        for ii, ind in enumerate(facet.indicators):
            ipath = f"{fpath}.indicators[{ii}]"
            if ind.name in seen_ind_names:
                issues.append(ValidationIssue("error", "E004", f"Duplicate indicator name '{ind.name}' in facet '{facet.name}'.", ipath))
            seen_ind_names.add(ind.name)

            if ind.weight < 0:
                issues.append(ValidationIssue("error", "E005", f"Indicator '{ind.name}' has negative weight.", ipath))

            lo, hi = ind.bounds
            if lo >= hi:
                issues.append(ValidationIssue("error", "E006", f"Indicator '{ind.name}' bounds are invalid ({lo}, {hi}).", ipath))

            if ind.signal_type not in ("boolean", "count", "ratio", "latency", "self_report", "frequency", "proportion"):
                issues.append(ValidationIssue("warning", "W001", f"Indicator '{ind.name}' uses unknown signal_type '{ind.signal_type}'.", ipath))

    # Coverage heuristic: at least 2 facets or 3 indicators total for a non-trivial concept
    total_indicators = sum(len(f.indicators) for f in concept.facets)
    if len(concept.facets) < 2 and total_indicators < 3:
        issues.append(ValidationIssue("warning", "W002", "Concept is under-specified (fewer than 2 facets or 3 total indicators).", "facets"))

    # Redundancy heuristic: warn if all indicators in a facet use the exact same signal_type and function
    for fi, facet in enumerate(concept.facets):
        if len(facet.indicators) >= 2:
            first = facet.indicators[0]
            if all(i.signal_type == first.signal_type and i.function == first.function for i in facet.indicators):
                issues.append(ValidationIssue(
                    "warning", "W003",
                    f"Facet '{facet.name}' indicators appear redundant (same signal_type + function).",
                    f"facets[{fi}]"
                ))

    # Gaming / Goodhart risk heuristic
    for fi, facet in enumerate(concept.facets):
        for ii, ind in enumerate(facet.indicators):
            if ind.signal_type in ("self_report", "boolean") and "audit" not in ind.meta.get("tags", []):
                issues.append(ValidationIssue(
                    "info", "I001",
                    f"Indicator '{ind.name}' is potentially gameable (self_report / boolean without audit tag). Consider adding an independent audit indicator.",
                    f"facets[{fi}].indicators[{ii}]"
                ))

    errors = [i for i in issues if i.severity == "error"]
    return ValidationResult(passed=len(errors) == 0, issues=issues)
