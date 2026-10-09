from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional, TextIO

from .models import Concept


def format_report(report: Dict[str, Any], fmt: str = "json") -> str:
    if fmt == "json":
        return json.dumps(report, indent=2, default=str)
    if fmt == "markdown":
        return _to_markdown(report)
    if fmt == "text":
        return _to_text(report)
    raise ValueError(f"Unknown format: {fmt}")


def _to_markdown(report: Dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {report['concept']} (v{report['version']})")
    lines.append("")
    score = report.get("score")
    unc = report.get("uncertainty")
    if score is not None and not isinstance(score, float) or (isinstance(score, float) and not score != score):  # not NaN
        lines.append(f"**Score:** {score:.3f} ± {unc:.3f}" if isinstance(unc, float) else f"**Score:** {score:.3f}")
    lines.append(f"**Method:** {report['aggregation_method']}")
    lines.append("")
    prov = report.get("provenance", {})
    note = prov.get("philosophy_note", "")
    if note:
        lines.append(f"> {note}")
        lines.append("")
    lines.append("## Facets")
    for f in report.get("facets", []):
        lines.append(f"### {f['facet']} (weight {f['weight']})")
        fs = f.get("score")
        fu = f.get("uncertainty")
        if fs is not None and not (isinstance(fs, float) and fs != fs):
            lines.append(f"- **Facet score:** {fs:.3f} ± {fu:.3f}" if isinstance(fu, float) else f"- **Facet score:** {fs:.3f}")
        lines.append("- **Indicators:**")
        for i in f.get("indicators", []):
            if "error" in i:
                lines.append(f"  - `{i['indicator']}` — ERROR: {i['error']}")
            else:
                lines.append(f"  - `{i['indicator']}` ({i['signal_type']}) → {i['computed_value']:.3f} [bounds {i['bounds']}, weight {i['weight']}]")
        lines.append("")
    return "\n".join(lines)


def _to_text(report: Dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"Concept: {report['concept']} v{report['version']}")
    score = report.get("score")
    unc = report.get("uncertainty")
    if score is not None and not (isinstance(score, float) and score != score):
        lines.append(f"Score: {score:.3f} ± {unc:.3f}" if isinstance(unc, float) else f"Score: {score:.3f}")
    for f in report.get("facets", []):
        fs = f.get("score")
        fu = f.get("uncertainty")
        if fs is not None and not (isinstance(fs, float) and fs != fs):
            lines.append(f"  {f['facet']}: {fs:.3f} ± {fu:.3f}" if isinstance(fu, float) else f"  {f['facet']}: {fs:.3f}")
        for i in f.get("indicators", []):
            if "error" in i:
                lines.append(f"    {i['indicator']} ERR {i['error']}")
            else:
                lines.append(f"    {i['indicator']}: {i['computed_value']:.3f}")
    return "\n".join(lines)


def write_report(report: Dict[str, Any], fmt: str = "json", out: Optional[TextIO] = None) -> None:
    out = out or sys.stdout
    out.write(format_report(report, fmt))
    out.write("\n")
