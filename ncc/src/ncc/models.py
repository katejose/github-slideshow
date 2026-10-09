from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import yaml


@dataclass
class Indicator:
    """A single observable proxy for a facet of a normative concept."""
    name: str
    description: str
    signal_type: str  # e.g. 'boolean', 'count', 'ratio', 'latency', 'self_report'
    # The function can be a literal Python expression (evaluated later) or a named plugin
    function: str
    weight: float = 1.0  # relative weight within its facet
    bounds: tuple[float, float] = (0.0, 1.0)
    uncertainty_model: str = "uniform"  # placeholder for future Bayesian backends
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Facet:
    """A sub-dimension of a normative concept."""
    name: str
    description: str
    weight: float = 1.0  # relative weight within the concept
    indicators: List[Indicator] = field(default_factory=list)


@dataclass
class Concept:
    """A versioned, opinionated formalization of a normative construct."""
    name: str
    version: str
    description: str
    philosophy_note: str  # explicitly states the assumptions / school of thought
    facets: List[Facet] = field(default_factory=list)
    aggregation_method: str = "weighted_mean"  # or 'min', 'geometric_mean', etc.
    changelog: List[str] = field(default_factory=list)


def _load_indicator(raw: dict) -> Indicator:
    return Indicator(
        name=raw["name"],
        description=raw.get("description", ""),
        signal_type=raw["signal_type"],
        function=raw["function"],
        weight=raw.get("weight", 1.0),
        bounds=tuple(raw.get("bounds", [0.0, 1.0])),
        uncertainty_model=raw.get("uncertainty_model", "uniform"),
        meta=raw.get("meta", {}),
    )


def _load_facet(raw: dict) -> Facet:
    return Facet(
        name=raw["name"],
        description=raw.get("description", ""),
        weight=raw.get("weight", 1.0),
        indicators=[_load_indicator(i) for i in raw.get("indicators", [])],
    )


def load_concept_from_yaml(path: str) -> Concept:
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return Concept(
        name=raw["name"],
        version=raw.get("version", "0.1.0"),
        description=raw.get("description", ""),
        philosophy_note=raw.get("philosophy_note", ""),
        facets=[_load_facet(f) for f in raw.get("facets", [])],
        aggregation_method=raw.get("aggregation_method", "weighted_mean"),
        changelog=raw.get("changelog", []),
    )
