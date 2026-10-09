from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import load_concept_from_yaml, compile_concept, validate_concept, format_report


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """Normative Construct Compiler (NCC) — build mathematical proxies for normative concepts."""
    pass


@main.command()
@click.argument("spec_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json", "markdown"]))
def score(spec_path: Path, fmt: str) -> None:
    """Compile a spec and run a demo observation set (built-in smoke test)."""
    concept = load_concept_from_yaml(str(spec_path))
    v = validate_concept(concept)
    if not v.passed:
        click.echo("Validation FAILED:", err=True)
        for issue in v.issues:
            if issue.severity == "error":
                click.echo(f"  [{issue.code}] {issue.path}: {issue.message}", err=True)
        sys.exit(1)

    # Demo observations: all indicators get a 0.7 value by default for smoke test
    score_fn = compile_concept(concept)
    demo_obs: dict[str, dict[str, float]] = {}
    for facet in concept.facets:
        demo_obs[facet.name] = {}
        for ind in facet.indicators:
            key = ind.meta.get("observation_key", ind.name)
            demo_obs[facet.name][key] = 0.7

    report = score_fn(demo_obs)
    click.echo(format_report(report, fmt))


@main.command()
@click.argument("spec_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("obs_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json", "markdown"]))
def run(spec_path: Path, obs_path: Path, fmt: str) -> None:
    """Compile a spec and score it against a JSON observation file."""
    concept = load_concept_from_yaml(str(spec_path))
    v = validate_concept(concept)
    if not v.passed:
        click.echo("Validation FAILED:", err=True)
        for issue in v.issues:
            if issue.severity == "error":
                click.echo(f"  [{issue.code}] {issue.path}: {issue.message}", err=True)
        sys.exit(1)

    with open(obs_path, "r", encoding="utf-8") as fh:
        observations = json.load(fh)

    score_fn = compile_concept(concept)
    report = score_fn(observations)
    click.echo(format_report(report, fmt))


@main.command()
@click.argument("spec_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def validate(spec_path: Path) -> None:
    """Validate a concept spec without running it."""
    concept = load_concept_from_yaml(str(spec_path))
    v = validate_concept(concept)
    for issue in v.issues:
        click.echo(f"[{issue.severity.upper()}] {issue.code} @ {issue.path}: {issue.message}")
    if v.passed:
        click.echo("Validation passed.")
    else:
        click.echo("Validation failed.", err=True)
        sys.exit(1)
