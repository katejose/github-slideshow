from __future__ import annotations

import math
import warnings
from typing import Any, Dict, List, Tuple, Callable
import numpy as np

from .models import Concept, Facet, Indicator


class IndicatorEvalError(Exception):
    pass


def _default_registry() -> Dict[str, Callable[[Any], float]]:
    """Built-in indicator functions that can be referenced by name."""
    return {
        "identity": lambda x: float(x) if x is not None else math.nan,
        "bool_to_float": lambda x: 1.0 if x else 0.0,
        "ratio_clamp": lambda x: max(0.0, min(1.0, float(x))) if x is not None else math.nan,
        "inverse_latency": lambda x: 1.0 / (1.0 + float(x)) if x is not None else math.nan,
        "zscore_clip": lambda mu, sigma, val: max(0.0, min(1.0, 0.5 + (float(val) - float(mu)) / (2.0 * float(sigma))))
            if None not in (mu, sigma, val) and float(sigma) > 0 else math.nan,
    }


def _eval_indicator(indicator: Indicator, observation: Any, registry: Dict[str, Callable]) -> float:
    """Evaluate a single indicator against an observation.

    ``observation`` can be:
    - a scalar (for simple expression indicators)
    - a dict (for named function indicators that look up keys)
    """
    func_name = indicator.function.strip()

    # Named function reference
    if func_name in registry:
        fn = registry[func_name]
        if isinstance(observation, dict):
            # Attempt to extract the relevant key if it exists
            key = indicator.meta.get("observation_key", indicator.name)
            val = observation.get(key, observation.get("value"))
            # Some functions take multiple args from the dict
            sig = indicator.meta.get("args")
            if sig and isinstance(sig, list):
                args = [observation.get(k) for k in sig]
                return fn(*args)
            return fn(val)
        return fn(observation)

    # Simple literal expression (safe subset)
    if isinstance(observation, dict):
        key = indicator.meta.get("observation_key", indicator.name)
        val = observation.get(key, observation.get("value"))
    else:
        val = observation

    try:
        # We allow a very restricted expression syntax: only the variable `x` and math operators
        if func_name.startswith("lambda x:"):
            expr = func_name[len("lambda x:"):].strip()
            # VERY restricted eval: only math builtins and x
            safe = {"x": val, "math": math, "min": min, "max": max, "abs": abs}
            result = eval(expr, {"__builtins__": {}}, safe)
            return float(result)
    except Exception as exc:
        raise IndicatorEvalError(f"Indicator '{indicator.name}' eval failed: {exc}")

    raise IndicatorEvalError(f"Indicator '{indicator.name}' has unrecognized function '{func_name}'")


def _aggregate(values: List[float], weights: List[float], method: str) -> Tuple[float, float]:
    """Return (score, uncertainty) where uncertainty is a simple stddev proxy."""
    clean = [(v, w) for v, w in zip(values, weights) if not math.isnan(v) and w > 0]
    if not clean:
        return math.nan, math.nan

    vs, ws = zip(*clean)
    vs = np.array(vs, dtype=float)
    ws = np.array(ws, dtype=float)
    ws = ws / ws.sum()

    if method == "weighted_mean":
        score = float(np.dot(vs, ws))
        # variance proxy: weighted variance around the weighted mean
        var = float(np.dot(ws, (vs - score) ** 2))
        return score, math.sqrt(var)
    elif method == "geometric_mean":
        # weighted geometric mean via logs
        if np.any(vs <= 0):
            warnings.warn("geometric_mean with non-positive values; clamping to epsilon")
            vs = np.maximum(vs, 1e-12)
        log_score = float(np.dot(ws, np.log(vs)))
        score = math.exp(log_score)
        # crude uncertainty: geometric stddev approximation
        log_var = float(np.dot(ws, (np.log(vs) - log_score) ** 2))
        return score, score * math.sqrt(log_var)
    elif method == "min":
        score = float(np.min(vs))
        return score, 0.0  # deterministic
    elif method == "max":
        score = float(np.max(vs))
        return score, 0.0
    else:
        raise ValueError(f"Unknown aggregation method: {method}")


def compile_concept(concept: Concept, registry: Dict[str, Callable] | None = None) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Compile a Concept into a scoring function.

    The returned function accepts a dict of observations (facet_name -> indicator observations)
    and returns a report dict with scores, uncertainties, and provenance.
    """
    reg = {**_default_registry(), **(registry or {})}

    def score_fn(observations: Dict[str, Any]) -> Dict[str, Any]:
        facet_reports: List[Dict[str, Any]] = []
        facet_scores: List[float] = []
        facet_uncertainties: List[float] = []
        facet_weights: List[float] = []

        for facet in concept.facets:
            obs = observations.get(facet.name, {})
            ind_values: List[float] = []
            ind_weights: List[float] = []
            ind_provenance: List[Dict[str, Any]] = []

            for ind in facet.indicators:
                try:
                    val = _eval_indicator(ind, obs, reg)
                    # clamp to declared bounds
                    lo, hi = ind.bounds
                    val = max(lo, min(hi, val))
                except IndicatorEvalError as exc:
                    val = math.nan
                    ind_provenance.append({"indicator": ind.name, "error": str(exc)})
                    continue

                ind_values.append(val)
                ind_weights.append(ind.weight)
                ind_provenance.append({
                    "indicator": ind.name,
                    "signal_type": ind.signal_type,
                    "raw_value": obs if not isinstance(obs, dict) else obs.get(ind.meta.get("observation_key", ind.name)),
                    "computed_value": val,
                    "bounds": ind.bounds,
                    "weight": ind.weight,
                })

            f_score, f_unc = _aggregate(ind_values, ind_weights, concept.aggregation_method)
            facet_reports.append({
                "facet": facet.name,
                "weight": facet.weight,
                "score": f_score,
                "uncertainty": f_unc,
                "indicators": ind_provenance,
            })
            if not math.isnan(f_score):
                facet_scores.append(f_score)
                facet_uncertainties.append(f_unc)
                facet_weights.append(facet.weight)

        total_score, total_unc = _aggregate(facet_scores, facet_weights, concept.aggregation_method)

        return {
            "concept": concept.name,
            "version": concept.version,
            "aggregation_method": concept.aggregation_method,
            "score": total_score,
            "uncertainty": total_unc,
            "facets": facet_reports,
            "provenance": {
                "philosophy_note": concept.philosophy_note,
                "changelog": concept.changelog,
            },
        }

    return score_fn
