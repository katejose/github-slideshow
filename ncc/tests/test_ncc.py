from __future__ import annotations

import math
from pathlib import Path

import pytest

from ncc.models import load_concept_from_yaml, Concept, Facet, Indicator
from ncc.compiler import compile_concept, _eval_indicator, _aggregate, _default_registry
from ncc.validators import validate_concept
from ncc.report import format_report


EXAMPLES = Path(__file__).parent.parent / "examples"


def test_load_honesty() -> None:
    c = load_concept_from_yaml(str(EXAMPLES / "honesty.yaml"))
    assert c.name == "Honesty"
    assert len(c.facets) == 3
    assert c.aggregation_method == "weighted_mean"


def test_validate_honesty_passes() -> None:
    c = load_concept_from_yaml(str(EXAMPLES / "honesty.yaml"))
    v = validate_concept(c)
    assert v.passed
    # should have at least one info about gameability of self_report
    infos = [i for i in v.issues if i.severity == "info"]
    assert any("gameable" in i.message for i in infos)


def test_validate_catches_duplicate_facet() -> None:
    c = Concept(
        name="Bad",
        version="0.1.0",
        description="",
        philosophy_note="",
        facets=[
            Facet(name="A", description="", weight=1.0, indicators=[Indicator(name="i1", description="", signal_type="ratio", function="ratio_clamp")]),
            Facet(name="A", description="", weight=1.0, indicators=[Indicator(name="i2", description="", signal_type="ratio", function="ratio_clamp")]),
        ],
    )
    v = validate_concept(c)
    assert not v.passed
    assert any(i.code == "E003" for i in v.issues)


def test_indicator_eval_named_function() -> None:
    ind = Indicator(name="x", description="", signal_type="ratio", function="ratio_clamp", meta={"observation_key": "val"})
    reg = _default_registry()
    assert _eval_indicator(ind, {"val": 1.2}, reg) == 1.0
    assert _eval_indicator(ind, {"val": -0.3}, reg) == 0.0
    assert _eval_indicator(ind, {"val": 0.5}, reg) == 0.5


def test_indicator_eval_lambda() -> None:
    ind = Indicator(name="x", description="", signal_type="count", function="lambda x: max(0.0, 1.0 - x)")
    reg = _default_registry()
    assert _eval_indicator(ind, 0.0, reg) == 1.0
    assert _eval_indicator(ind, 1.5, reg) == 0.0


def test_aggregate_weighted_mean() -> None:
    s, u = _aggregate([0.8, 0.6, 0.9], [1.0, 1.0, 1.0], "weighted_mean")
    assert pytest.approx(s, 0.01) == 0.7667
    assert u >= 0


def test_aggregate_geometric_mean() -> None:
    s, u = _aggregate([0.8, 0.6, 0.9], [1.0, 1.0, 1.0], "geometric_mean")
    # geometric mean of 0.8, 0.6, 0.9
    expected = math.exp((math.log(0.8) + math.log(0.6) + math.log(0.9)) / 3)
    assert pytest.approx(s, 0.001) == expected


def test_compile_and_score_honesty() -> None:
    c = load_concept_from_yaml(str(EXAMPLES / "honesty.yaml"))
    score_fn = compile_concept(c)
    with open(EXAMPLES / "honesty_obs.json", "r") as fh:
        import json
        obs = json.load(fh)
    report = score_fn(obs)
    assert report["concept"] == "Honesty"
    assert isinstance(report["score"], float)
    assert not math.isnan(report["score"])
    assert report["uncertainty"] >= 0
    assert len(report["facets"]) == 3
    # check each facet has indicators
    for f in report["facets"]:
        assert "indicators" in f
        assert len(f["indicators"]) > 0


def test_report_markdown_format() -> None:
    c = load_concept_from_yaml(str(EXAMPLES / "honesty.yaml"))
    score_fn = compile_concept(c)
    with open(EXAMPLES / "honesty_obs.json", "r") as fh:
        import json
        obs = json.load(fh)
    report = score_fn(obs)
    md = format_report(report, "markdown")
    assert "# Honesty" in md
    assert "Veracity" in md
    assert "Transparency" in md


def test_patient_spec_validation() -> None:
    c = load_concept_from_yaml(str(EXAMPLES / "patience.yaml"))
    v = validate_concept(c)
    assert v.passed


def test_discipline_spec_validation() -> None:
    c = load_concept_from_yaml(str(EXAMPLES / "discipline.yaml"))
    v = validate_concept(c)
    assert v.passed
    # geometric mean should be flagged just by existing (no warning needed here)
    assert c.aggregation_method == "geometric_mean"
