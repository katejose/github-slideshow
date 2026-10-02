"""Vör Evaluation Engine — deterministic ethical diode.

Three-arbitration architecture: consequentialist → deontological → virtue ethics.
Absolute-prohibition gate is first and non-overridable.
"""

import random
import string
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .virtue_profiles import get_virtues_by_profile_id, get_virtue_profile
from .evidence_library import title_for_source_id

# === Constants (exact values from JS bundle) ===
RESPECT_GATE_THRESHOLD = 0.6
SELFLESS_DISPLACED_GATE = 0.8
COMPOSITE_ALLOW = 0.5
COMPOSITE_BLOCK = 0.3

HARM_SCALE_RATE_THRESHOLD = 0.05
HARM_SCALE_ABSOLUTE_THRESHOLD = 1000
MAX_AUTONOMOUS_ALLOW_FATALITIES = 10
ABSOLUTE_PROHIBITION_RULE_ID = "IHRL-ABS-1"

CDRILS_V1_0_COMPOSITE_ALLOW = 5
CDRILS_V1_0_COMPOSITE_ESCALATE = 3
CDRILS_V1_0_TOTAL_VIRTUES = 6

FORCEFUL_NONLETHAL_KEYWORDS = [
    "munition", "gas", "net ", "nets", "rubber round", "baton",
    "taser", "stun", "pepper spray", "incapacitat",
    "less-lethal", "less lethal", "non-lethal round",
    "non-lethal weapon", "projectile",
]

DEFAULT_DISPOSITION_RULE_ID = "cdrils-v1.1-canonical"
LEGACY_DISPOSITION_RULE_ALIASES = {"cdrils-v1.1-shadow": "cdrils-v1.1-canonical"}


@dataclass
class TraceEntry:
    id: str
    phase: str
    description: str
    details: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class VirtueScore:
    virtue: str
    code: str
    score: float
    threshold: float
    status: str  # "pass", "fail", "na"
    reasoning: str
    inputs_sufficient: bool = True
    missing_inputs: List[str] = field(default_factory=list)
    components: Optional[Dict[str, Any]] = None


@dataclass
class ConsequentialistResult:
    score: float
    harm_avoided: float
    harm_caused: float
    confidence_lower: float
    confidence_upper: float
    factors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RuleEvaluation:
    rule_id: str
    rule_name: str
    passed: bool
    reason: str
    citations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DeontologicalResult:
    status: str  # "permitted", "prohibited", "conditional"
    rules_evaluated: List[RuleEvaluation] = field(default_factory=list)
    overall_reason: str = ""


@dataclass
class VirtueEthicsResult:
    triggered: bool
    trigger_reason: str
    virtue_scores: List[VirtueScore] = field(default_factory=list)
    composite_score: float = 0.0
    arbitration_decision: str = ""  # "allow", "block", "escalate"
    reasoning: str = ""


@dataclass
class Citation:
    id: str
    source_id: str
    title: str
    excerpt: str
    relevance: str


@dataclass
class VorResult:
    id: str
    scenario_id: str
    action_id: str
    timestamp: str
    model_version: str
    ruleset_id: str
    ruleset_version: str
    virtue_profile_id: str
    virtue_profile_version: str
    consequentialist: ConsequentialistResult
    deontological: DeontologicalResult
    virtue_ethics: VirtueEthicsResult
    shadow_virtue_ethics: Optional[VirtueEthicsResult] = None
    disposition_rule_id: str = ""
    disposition_rule_version: str = ""
    final_disposition: str = ""  # "allow", "block", "escalate"
    rationale: str = ""
    trace: List[TraceEntry] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)


def _generate_id() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=13))


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# === Consequentialist Evaluation ===

def evaluate_consequentialist(scenario: Dict[str, Any], action: Dict[str, Any]) -> ConsequentialistResult:
    ctx = scenario.get("context", {})
    lethality = action.get("lethality", "non-lethal")
    lethality_weight = 0.9 if lethality == "lethal" else (0.5 if lethality == "potentially-lethal" else 0.1)
    threat_mitigation = ctx.get("threatLikelihood", 0.0) * (1 - ctx.get("uncertaintyLevel", 0.0))

    ec = action.get("expectedCasualties")
    if ec:
        denom = max(1, ec.get("populationAtRisk", 1))
        civ_expected = ec.get("civilian", {}).get("expected", 0)
        civ_min = ec.get("civilian", {}).get("min", 0)
        civ_max = ec.get("civilian", {}).get("max", civ_expected)
        civ_fatality_rate = min(1.0, civ_expected / denom)
        civ_fatality_rate_min = min(1.0, civ_min / denom)
        civ_fatality_rate_max = min(1.0, civ_max / denom)

        harm_avoided = (1 - civ_fatality_rate) * threat_mitigation
        harm_caused = civ_fatality_rate * lethality_weight
        score = (harm_avoided - harm_caused) / (harm_avoided + harm_caused + 0.001)

        harm_caused_min = civ_fatality_rate_min * lethality_weight
        harm_caused_max = civ_fatality_rate_max * lethality_weight
        harm_avoided_min = (1 - civ_fatality_rate_max) * threat_mitigation
        harm_avoided_max = (1 - civ_fatality_rate_min) * threat_mitigation

        score_lower = (harm_avoided_min - harm_caused_max) / (harm_avoided_min + harm_caused_max + 0.001)
        score_upper = (harm_avoided_max - harm_caused_min) / (harm_avoided_max + harm_caused_min + 0.001)

        factors = [
            {"name": "Civilian Fatality Rate", "weight": 0.45, "value": civ_fatality_rate},
            {"name": "Threat Mitigation", "weight": 0.30, "value": threat_mitigation},
            {"name": "Lethality Factor", "weight": 0.15, "value": lethality_weight},
            {"name": "Casualty Range Width", "weight": 0.10, "value": civ_fatality_rate_max - civ_fatality_rate_min},
        ]
        return ConsequentialistResult(
            score=max(-1.0, min(1.0, score)),
            harm_avoided=harm_avoided,
            harm_caused=harm_caused,
            confidence_lower=max(-1.0, min(1.0, score_lower)),
            confidence_upper=max(-1.0, min(1.0, score_upper)),
            factors=factors,
        )

    civilian_risk = (ctx.get("civilianPresence", 0) / 100.0) * lethality_weight
    harm_avoided = threat_mitigation * 0.8
    harm_caused = civilian_risk * 0.6
    score = (harm_avoided - harm_caused) / (harm_avoided + harm_caused + 0.001)
    uncertainty = ctx.get("uncertaintyLevel", 0) * 0.3

    factors = [
        {"name": "Threat Mitigation", "weight": 0.40, "value": threat_mitigation},
        {"name": "Civilian Risk", "weight": 0.30, "value": civilian_risk},
        {"name": "Lethality Factor", "weight": 0.20, "value": lethality_weight},
        {"name": "Uncertainty Penalty", "weight": 0.10, "value": ctx.get("uncertaintyLevel", 0)},
    ]
    return ConsequentialistResult(
        score=max(-1.0, min(1.0, score)),
        harm_avoided=harm_avoided,
        harm_caused=harm_caused,
        confidence_lower=score - uncertainty,
        confidence_upper=score + uncertainty,
        factors=factors,
    )


# === Deontological Evaluation ===

def _applies_forceful_non_lethal(action: Dict[str, Any]) -> bool:
    haystack = " ".join(filter(None, [
        action.get("name", ""),
        action.get("description", ""),
        *action.get("expectedEffects", []),
    ])).lower()
    return any(k in haystack for k in FORCEFUL_NONLETHAL_KEYWORDS)


def _is_rule_applicable(rule_id: str, action: Dict[str, Any]) -> bool:
    civ_max = action.get("expectedCasualties", {}).get("civilian", {}).get("max", 0)
    civ_exp = action.get("expectedCasualties", {}).get("civilian", {}).get("expected", 0)
    lethal = action.get("lethality") == "lethal"
    forceful = _applies_forceful_non_lethal(action)
    if rule_id == "LOAC-1":
        return lethal or civ_max > 0 or forceful
    if rule_id == "LOAC-2":
        return lethal or civ_exp > 0
    if rule_id == "LOAC-3":
        return lethal or forceful
    if rule_id == "ROE-1":
        return len(action.get("preconditions", [])) > 0
    return True


def _list_absolute_prohibition_breaches(action: Dict[str, Any]) -> List[str]:
    ap = action.get("absoluteProhibitions")
    if not ap:
        return []
    breaches = []
    if ap.get("torture"):
        breaches.append("torture (UNCAT Art. 2(2); ECHR Art. 3; ICCPR Art. 7)")
    if ap.get("cruelInhumanTreatment"):
        breaches.append("cruel, inhuman or degrading treatment (UNCAT Art. 16; ECHR Art. 3)")
    if ap.get("targetingProtectedPersons"):
        breaches.append("attack on protected persons (GC I-IV; AP I)")
    if ap.get("collectivePunishment"):
        breaches.append("collective punishment (GC IV Art. 33; AP I Art. 75(2)(d))")
    if ap.get("genocidalIntent"):
        breaches.append("acts with genocidal intent (Genocide Convention Art. II)")
    return breaches


def evaluate_deontological(scenario: Dict[str, Any], action: Dict[str, Any]) -> DeontologicalResult:
    ec = action.get("expectedCasualties")
    civ_fatality_rate = None
    expected_civ_harm = None
    if ec:
        denom = max(1, ec.get("populationAtRisk", 1))
        civ_expected = ec.get("civilian", {}).get("expected", 0)
        civ_fatality_rate = civ_expected / denom
        expected_civ_harm = civ_expected

    def loac1_check():
        if civ_fatality_rate is not None:
            return not (action.get("lethality") == "lethal" and civ_fatality_rate > 0.5)
        return scenario.get("context", {}).get("civilianPresence", 0) < 80 or action.get("lethality") == "non-lethal"

    def loac2_check():
        if ec and expected_civ_harm is not None:
            lives_saved = max(0, ec.get("populationAtRisk", 0) - expected_civ_harm)
            advantage = scenario.get("context", {}).get("threatLikelihood", 0) * lives_saved
            return advantage > expected_civ_harm
        return scenario.get("context", {}).get("threatLikelihood", 0) > 0.5 or action.get("lethality") != "lethal"

    def loac3_check():
        return scenario.get("context", {}).get("threatLikelihood", 0) > 0.3

    def roe1_check():
        return len(action.get("preconditions", [])) > 0

    def abs_check():
        return len(_list_absolute_prohibition_breaches(action)) == 0

    rules = [
        {
            "rule_id": "LOAC-1",
            "rule_name": "Distinction Principle",
            "check": loac1_check,
            "sources": [
                {"source_id": "GC-AP1", "excerpt": "Articles 48 and 51(2) — the principle of distinction between civilians and combatants.", "relevance": "Primary treaty basis"},
                {"source_id": "ICRC-CIL", "excerpt": "Rule 1 — the parties to the conflict must at all times distinguish between civilians and combatants.", "relevance": "Customary international law restatement"},
                {"source_id": "JSP-398", "relevance": "UK targeting doctrine implementation"},
            ],
        },
        {
            "rule_id": "LOAC-2",
            "rule_name": "Proportionality Principle",
            "check": loac2_check,
            "sources": [
                {"source_id": "GC-AP1", "excerpt": "Article 51(5)(b) — prohibition of attacks expected to cause incidental civilian harm excessive in relation to the concrete and direct military advantage anticipated.", "relevance": "Primary treaty basis"},
                {"source_id": "ICRC-CIL", "excerpt": "Rule 14 — proportionality in attack.", "relevance": "Customary international law restatement"},
                {"source_id": "JSP-398", "relevance": "UK targeting doctrine implementation"},
            ],
        },
        {
            "rule_id": "LOAC-3",
            "rule_name": "Military Necessity",
            "check": loac3_check,
            "sources": [
                {"source_id": "DOD-LOAC", "excerpt": "Section 2.2 — military necessity as a justifying principle, constrained by humanity, distinction and proportionality.", "relevance": "Doctrinal articulation"},
                {"source_id": "ICRC-CIL", "excerpt": "Rule 50 — military necessity does not justify departures from rules of IHL.", "relevance": "Customary international law restatement"},
            ],
        },
        {
            "rule_id": "ROE-1",
            "rule_name": "Precaution in Attack",
            "check": roe1_check,
            "sources": [
                {"source_id": "GC-AP1", "excerpt": "Article 57 — constant care to spare the civilian population; verify targets; take all feasible precautions in choice of means and methods.", "relevance": "Primary treaty basis"},
                {"source_id": "AJP-3.9", "relevance": "NATO joint targeting doctrine — precaution operationalised"},
                {"source_id": "JSP-398", "relevance": "UK targeting doctrine implementation"},
            ],
        },
        {
            "rule_id": ABSOLUTE_PROHIBITION_RULE_ID,
            "rule_name": "Non-derogable Prohibitions",
            "check": abs_check,
            "sources": [
                {"source_id": "GC-IV", "excerpt": "Article 33 — prohibition of collective penalties; reprisals against protected persons and their property.", "relevance": "Treaty articulation of non-derogable protections"},
                {"source_id": "ICJ-NUCLEAR", "relevance": "ICJ on the intransgressible character of fundamental rules of IHL"},
                {"source_id": "UN-LAWS", "relevance": "UN deliberations on LAWS and non-derogable floor"},
                {"source_id": "CDRILS-DEF", "relevance": "Architectural commitment to categorical prohibitions"},
                {"source_id": "JDP-3-46", "relevance": "UK legal support to joint operations — non-derogable absolutes"},
            ],
        },
    ]

    evaluations: List[RuleEvaluation] = []
    for rule in rules:
        passed = rule["check"]()
        reason = ""
        if rule["rule_id"] == "LOAC-1":
            if civ_fatality_rate is not None:
                pct = f"{civ_fatality_rate * 100:.1f}%"
                reason = f"Distinction maintained: foreseen civilian fatalities {pct} of population at risk" if passed else f"Distinction violated: {pct} of population at risk are foreseen civilian fatalities under a lethal action"
            else:
                reason = "Adequate distinction between combatants and civilians maintained" if passed else "High civilian presence with lethal action violates distinction principle"
        elif rule["rule_id"] == "LOAC-2":
            if ec and expected_civ_harm is not None:
                lives_saved = max(0, ec.get("populationAtRisk", 0) - expected_civ_harm)
                advantage = scenario.get("context", {}).get("threatLikelihood", 0) * lives_saved
                reason = f"Proportional: concrete advantage ({advantage:.2f}) exceeds expected civilian harm ({expected_civ_harm})" if passed else f"Disproportionate: expected civilian harm ({expected_civ_harm}) exceeds concrete advantage ({advantage:.2f})"
            else:
                reason = "Response proportional to threat level" if passed else "Lethal response disproportionate to confirmed threat level"
        elif rule["rule_id"] == "LOAC-3":
            reason = "Military necessity threshold met" if passed else "Insufficient threat to justify military action"
        elif rule["rule_id"] == "ROE-1":
            reason = "Feasible precautions identified or non-lethal option selected" if passed else "No precautionary measures documented for lethal action"
        elif rule["rule_id"] == ABSOLUTE_PROHIBITION_RULE_ID:
            breaches = _list_absolute_prohibition_breaches(action)
            if passed:
                reason = "No engagement of non-derogable prohibitions (jus cogens / IHRL absolutes)"
            else:
                reason = f"Absolute prohibition engaged — non-derogable: {'; '.join(breaches)}. No balancing test is permitted."

        citations = []
        for src in rule.get("sources", []):
            citations.append({
                "id": _generate_id(),
                "source_id": src["source_id"],
                "title": title_for_source_id(src["source_id"]),
                "excerpt": src.get("excerpt", f"Primary source for {rule['rule_name']}."),
                "relevance": src.get("relevance", "Primary legal basis"),
            })

        evaluations.append(RuleEvaluation(
            rule_id=rule["rule_id"],
            rule_name=rule["rule_name"],
            passed=passed,
            reason=reason,
            citations=citations,
        ))

    all_passed = all(e.passed for e in evaluations)
    any_failed = any(not e.passed for e in evaluations)
    absolute_failed = any(e.rule_id == ABSOLUTE_PROHIBITION_RULE_ID and not e.passed for e in evaluations)

    if absolute_failed:
        status = "prohibited"
    elif all_passed:
        status = "permitted"
    elif any_failed and sum(1 for e in evaluations if not e.passed) >= 2:
        status = "prohibited"
    else:
        status = "conditional"

    overall_reason = ""
    if absolute_failed:
        overall_reason = "Non-derogable prohibition engaged — action is absolutely prohibited regardless of consequences"
    elif all_passed:
        overall_reason = "All deontological constraints satisfied"
    else:
        overall_reason = f"{sum(1 for e in evaluations if not e.passed)} rule(s) require attention"

    return DeontologicalResult(status=status, rules_evaluated=evaluations, overall_reason=overall_reason)


# === Virtue Ethics v1.1 ===

def _resolve_path(scenario: Dict[str, Any], action: Dict[str, Any], path: str) -> Any:
    segments = path.split(".")
    root = segments[0]
    cursor = scenario if root == "scenario" else (action if root == "action" else None)
    if cursor is None and root == "deontological":
        # Special: deontological result is not in scenario/action directly
        return None
    for seg in segments[1:]:
        if cursor is None or not isinstance(cursor, dict):
            return None
        cursor = cursor.get(seg)
    return cursor


def _derive_status(score: float, threshold: float, inputs_sufficient: bool) -> str:
    if not inputs_sufficient:
        return "na"
    return "pass" if score >= threshold else "fail"


def score_courage(scenario: Dict[str, Any], action: Dict[str, Any], _d: DeontologicalResult, defn) -> VirtueScore:
    ac = action.get("actorCost")
    if not ac:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="No actor-cost vector supplied; cannot score v1.1 Courage.",
            inputs_sufficient=False, missing_inputs=["action.actorCost"],
        )
    parts = [v for k, v in ac.items() if k in ("institutional", "professional", "reputational", "physical") and isinstance(v, (int, float))]
    if not parts:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="Actor-cost vector empty.",
            inputs_sufficient=False, missing_inputs=["action.actorCost.*"],
        )
    score = sum(parts) / len(parts)
    return VirtueScore(
        virtue=defn.name, code=defn.code, score=score, threshold=defn.default_threshold,
        status=_derive_status(score, defn.default_threshold, True),
        reasoning=f"Mean cost-to-actor {score:.2f} across {len(parts)} cost dimension(s).",
        inputs_sufficient=True,
        components={k: ac.get(k, 0) for k in ("institutional", "professional", "reputational", "physical")},
    )


def score_discipline(scenario: Dict[str, Any], action: Dict[str, Any], d: DeontologicalResult, defn) -> VirtueScore:
    rules = d.rules_evaluated
    rule_rate = sum(1 for r in rules if r.passed) / max(1, len(rules))
    pc = action.get("processCompliance")
    if not pc:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="No process-compliance flags supplied; Discipline unevaluable.",
            inputs_sufficient=False, missing_inputs=["action.processCompliance"],
            components={"ruleRate": rule_rate, "processRate": 0.0},
        )
    flag_values = [pc.get("pidApplied", False), pc.get("roeFollowed", False), pc.get("escalationCorrect", False), pc.get("documented", False)]
    process_rate = sum(1 for v in flag_values if v) / 4
    score = (rule_rate + process_rate) / 2
    return VirtueScore(
        virtue=defn.name, code=defn.code, score=score, threshold=defn.default_threshold,
        status=_derive_status(score, defn.default_threshold, True),
        reasoning=f"Rule pass-rate {rule_rate*100:.0f}%, process compliance {process_rate*100:.0f}% ({sum(1 for v in flag_values if v)}/4 flags); mean {score*100:.0f}%.",
        inputs_sufficient=True,
        components={"ruleRate": rule_rate, "processRate": process_rate},
    )


def score_respect(scenario: Dict[str, Any], action: Dict[str, Any], _d: DeontologicalResult, defn) -> VirtueScore:
    harmed = action.get("directlyHarmed", [])
    if not harmed:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="No directly-harmed groups declared; Respect gate not engaged.",
            inputs_sufficient=False, missing_inputs=["action.directlyHarmed"],
        )
    worst = max(harmed, key=lambda h: h.get("vulnerability", 0) * h.get("harmShare", 0))
    worst_exposure = worst.get("vulnerability", 0) * worst.get("harmShare", 0)
    if worst_exposure >= RESPECT_GATE_THRESHOLD or worst.get("inCustodyOrCare", False):
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="fail", reasoning=f"Non-compensatory Respect gate fired: {worst.get('groupId', 'unknown')} exposure {worst_exposure:.2f}{' (in custody/care)' if worst.get('inCustodyOrCare') else ''}.",
            inputs_sufficient=True, components={"worstExposure": worst_exposure},
        )
    score = 1 - worst_exposure
    return VirtueScore(
        virtue=defn.name, code=defn.code, score=score, threshold=defn.default_threshold,
        status=_derive_status(score, defn.default_threshold, True),
        reasoning=f"Worst-case exposure {worst_exposure:.2f} below gate; Respect score {score:.2f}.",
        inputs_sufficient=True, components={"worstExposure": worst_exposure},
    )


def score_integrity(scenario: Dict[str, Any], action: Dict[str, Any], d: DeontologicalResult, defn) -> VirtueScore:
    pre = action.get("preconditions", [])
    pre_set = set(s.lower().strip() for s in pre if s.strip())
    if not pre_set:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="No preconditions declared; Integrity unevaluable.",
            inputs_sufficient=False, missing_inputs=["action.preconditions"],
        )
    candidate_rules = [r for r in d.rules_evaluated if r.rule_id != ABSOLUTE_PROHIBITION_RULE_ID]
    applicable_rules = [r for r in candidate_rules if _is_rule_applicable(r.rule_id, action)]
    not_applicable = [r.rule_id for r in candidate_rules if not _is_rule_applicable(r.rule_id, action)]
    if not applicable_rules:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="No deontological rules apply to this action; Integrity unevaluable.",
            inputs_sufficient=False, missing_inputs=["applicable-rules"],
            components={"satisfiedRuleCount": 0, "applicableRuleCount": 0, "preconditionCount": len(pre_set), "candidateRuleCount": len(candidate_rules)},
        )
    satisfied = sum(1 for r in applicable_rules if r.passed)
    if satisfied == 0:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="fail", reasoning=f"Integrity gate: none of the {len(applicable_rules)} applicable deontological rule(s) passed.",
            inputs_sufficient=True,
            components={"satisfiedRuleCount": 0, "applicableRuleCount": len(applicable_rules), "preconditionCount": len(pre_set), "candidateRuleCount": len(candidate_rules)},
        )
    score = satisfied / len(applicable_rules)
    return VirtueScore(
        virtue=defn.name, code=defn.code, score=score, threshold=defn.default_threshold,
        status=_derive_status(score, defn.default_threshold, True),
        reasoning=f"Integrity: {satisfied}/{len(applicable_rules)} applicable deontological rule(s) passed{f' (not applicable: {', '.join(not_applicable)})' if not_applicable else ''}.",
        inputs_sufficient=True,
        components={"satisfiedRuleCount": satisfied, "applicableRuleCount": len(applicable_rules), "preconditionCount": len(pre_set), "candidateRuleCount": len(candidate_rules)},
    )


def score_loyalty(scenario: Dict[str, Any], action: Dict[str, Any], _d: DeontologicalResult, defn) -> VirtueScore:
    if scenario.get("context", {}).get("commandIntentLawful") is False:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="fail", reasoning="Non-compensatory Loyalty gate: standing command intent declared unlawful.",
            inputs_sufficient=True,
        )
    explicit = scenario.get("context", {}).get("commandIntentObjectives")
    objectives = explicit if explicit and len(explicit) > 0 else []
    if not objectives:
        ci = scenario.get("context", {}).get("commandIntent")
        if ci and isinstance(ci, dict):
            objectives = ci.get("objectives", [])
        elif ci and isinstance(ci, str):
            objectives = []
    if not objectives:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="Command intent lacks enumerated objectives; Loyalty unevaluable.",
            inputs_sufficient=False, missing_inputs=["scenario.context.commandIntentObjectives"],
        )
    aligns = set(s.lower() for s in action.get("alignsWith", []))
    objs = [o.lower() for o in objectives]
    matched = sum(1 for o in objs if o in aligns)
    score = matched / len(objs)
    return VirtueScore(
        virtue=defn.name, code=defn.code, score=score, threshold=defn.default_threshold,
        status=_derive_status(score, defn.default_threshold, True),
        reasoning=f"Action aligns with {matched}/{len(objs)} stated command objectives.",
        inputs_sufficient=True,
        components={"matched": matched, "objectives": len(objs)},
    )


def score_selfless(scenario: Dict[str, Any], action: Dict[str, Any], _d: DeontologicalResult, defn) -> VirtueScore:
    rb = action.get("riskBearers", [])
    if not rb:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="na", reasoning="No risk-bearer distribution supplied; Selfless Commitment unevaluable.",
            inputs_sufficient=False, missing_inputs=["action.riskBearers"],
        )
    selfless_share = sum(b.get("share", 0) for b in rb if b.get("group") in ("own-unit", "patient-in-care"))
    displaced_share = sum(b.get("share", 0) for b in rb if b.get("group") in ("civilian", "third-party"))
    if displaced_share >= SELFLESS_DISPLACED_GATE:
        return VirtueScore(
            virtue=defn.name, code=defn.code, score=0.0, threshold=defn.default_threshold,
            status="fail", reasoning=f"Non-compensatory Selfless gate: displaced share {displaced_share:.2f} meets or exceeds {SELFLESS_DISPLACED_GATE}.",
            inputs_sufficient=True,
            components={"selflessShare": selfless_share, "displacedShare": displaced_share},
        )
    return VirtueScore(
        virtue=defn.name, code=defn.code, score=selfless_share, threshold=defn.default_threshold,
        status=_derive_status(selfless_share, defn.default_threshold, True),
        reasoning=f"Selfless share {selfless_share:.2f}, displaced share {displaced_share:.2f}.",
        inputs_sufficient=True,
        components={"selflessShare": selfless_share, "displacedShare": displaced_share},
    )


SCORERS = {
    "C": score_courage,
    "D": score_discipline,
    "R": score_respect,
    "I": score_integrity,
    "L": score_loyalty,
    "S": score_selfless,
}


def _harden(s: VirtueScore, defn, scenario: Dict[str, Any], action: Dict[str, Any]) -> VirtueScore:
    required = [i for i in defn.inputs if i.required]
    missing = []
    for spec in required:
        v = _resolve_path(scenario, action, spec.path)
        is_absent = v is None or (isinstance(v, list) and len(v) == 0) or (isinstance(v, str) and v.strip() == "")
        if is_absent:
            missing.append(spec.path)
    if not missing:
        return s
    all_missing = list(dict.fromkeys([*(s.missing_inputs or []), *missing]))
    return VirtueScore(
        virtue=s.virtue, code=s.code, score=0.0, threshold=s.threshold, status="na",
        reasoning=f"Hardening layer: required input(s) absent ({', '.join(missing)}). {s.reasoning}",
        inputs_sufficient=False, missing_inputs=all_missing,
        components=s.components,
    )


def evaluate_virtue_ethics_v1_1(scenario: Dict[str, Any], action: Dict[str, Any], _c: ConsequentialistResult, d: DeontologicalResult, virtues) -> VirtueEthicsResult:
    scores: List[VirtueScore] = []
    for v in virtues:
        fn = SCORERS.get(v.code)
        if fn:
            raw = fn(scenario, action, d, v)
        else:
            raw = VirtueScore(
                virtue=v.name, code=v.code, score=0.0, threshold=v.default_threshold,
                status="na", reasoning="No v1.1 scorer registered for this virtue code.",
                inputs_sufficient=False, missing_inputs=[f"scorer:{v.code}"],
            )
        scores.append(_harden(raw, v, scenario, action))

    fired_gates = [s for s in scores
                   if any(v.code == s.code and v.gate_mode == "non-compensatory" for v in virtues)
                   and s.inputs_sufficient and s.score == 0]

    usable = [s for s in scores if s.inputs_sufficient]
    composite_score = sum(s.score for s in usable) / max(1, len(usable))

    if len(fired_gates) == 1:
        arbitration_decision = "block"
        reasoning = f"Non-compensatory gate on {fired_gates[0].virtue} forces block. {fired_gates[0].reasoning}"
    elif len(fired_gates) >= 2:
        arbitration_decision = "block"
        names = ", ".join(g.virtue for g in fired_gates)
        per_virtue = " ".join(g.reasoning for g in fired_gates)
        reasoning = f"Gates fired: {names} — any one forces block. {per_virtue}"
    elif composite_score >= COMPOSITE_ALLOW:
        arbitration_decision = "allow"
        reasoning = f"v1.1 composite {(composite_score*10):.1f}/10 meets allow threshold (≥ {COMPOSITE_ALLOW*10:.0f})."
    elif composite_score >= COMPOSITE_BLOCK:
        arbitration_decision = "escalate"
        reasoning = f"v1.1 composite {(composite_score*10):.1f}/10 in escalate band ({COMPOSITE_BLOCK*10:.0f}–{COMPOSITE_ALLOW*10:.0f})."
    else:
        arbitration_decision = "block"
        reasoning = f"v1.1 composite {(composite_score*10):.1f}/10 below block threshold (< {COMPOSITE_BLOCK*10:.0f})."

    insufficient = [s.code for s in scores if not s.inputs_sufficient]
    trigger_reason = f"v1.1 shadow run; {len(insufficient)} virtue(s) had insufficient inputs: {', '.join(insufficient)}." if insufficient else "v1.1 shadow run; all virtue inputs sufficient."

    return VirtueEthicsResult(
        triggered=True, trigger_reason=trigger_reason, virtue_scores=scores,
        composite_score=composite_score, arbitration_decision=arbitration_decision,
        reasoning=reasoning,
    )


# === Legacy Virtue Ethics v1.0 ===

def evaluate_virtue_ethics(scenario: Dict[str, Any], action: Dict[str, Any], c: ConsequentialistResult, d: DeontologicalResult, virtues, profile_id: str = "CDRILS_V1_1") -> VirtueEthicsResult:
    if profile_id == "CDRILS_V1_1":
        return evaluate_virtue_ethics_v1_1(scenario, action, c, d, virtues)

    c_favors = c.score > 0.2
    d_favors = d.status == "permitted"
    ec = action.get("expectedCasualties")
    civ_harm_absolute = ec.get("civilian", {}).get("expected", 0) if ec else 0
    civ_harm_rate = (ec.get("civilian", {}).get("expected", 0) / max(1, ec.get("populationAtRisk", 1))) if ec else 0
    harm_scale_trigger = civ_harm_rate >= HARM_SCALE_RATE_THRESHOLD or civ_harm_absolute >= HARM_SCALE_ABSOLUTE_THRESHOLD
    cd_misalignment = c_favors != d_favors

    trigger_reasons = []
    if cd_misalignment:
        trigger_reasons.append("C/D divergence")
    if d.status == "conditional":
        trigger_reasons.append("deontological status conditional")
    if d.status == "prohibited":
        trigger_reasons.append("deontological status prohibited")
    if harm_scale_trigger:
        trigger_reasons.append(f"harm-scale threshold exceeded ({civ_harm_absolute:,.0f} expected civilian fatalities, {civ_harm_rate*100:.1f}% of population at risk)")

    triggered = cd_misalignment or d.status in ("conditional", "prohibited") or harm_scale_trigger
    if not triggered:
        return VirtueEthicsResult(
            triggered=False,
            trigger_reason="C and D evaluations align and harm scale below threshold; VE arbitration not required",
            virtue_scores=[], composite_score=0.0,
            arbitration_decision="allow" if d_favors else "block",
            reasoning="Decision follows aligned C/D evaluation",
        )

    ctx = scenario.get("context", {})
    virtue_scores: List[VirtueScore] = []
    for virtue in virtues:
        if profile_id == "CDRILS":
            if virtue.code == "C":
                score = 0.9 if ctx.get("timePressure") == "critical" else (0.7 if ctx.get("timePressure") == "high" else 0.5)
                reasoning = f"Time pressure ({ctx.get('timePressure')}) {'justifies' if score >= virtue.default_threshold else 'does not justify'} action under uncertainty"
            elif virtue.code == "D":
                passed_rules = sum(1 for r in d.rules_evaluated if r.passed)
                score = passed_rules / max(1, len(d.rules_evaluated))
                reasoning = f"{int(score*100)}% rule compliance demonstrated"
            elif virtue.code == "R":
                score = 1 - (ctx.get("civilianPresence", 0) / 100) * (1 if action.get("lethality") == "lethal" else 0.3)
                reasoning = f"Civilian protection weight: {int(score*100)}%"
            elif virtue.code == "I":
                score = 0.8 if len(action.get("preconditions", [])) > 0 else 0.5
                reasoning = "Documented preconditions show deliberation" if len(action.get("preconditions", [])) > 0 else "Limited precondition documentation"
            elif virtue.code == "L":
                score = 0.85 if ctx.get("commandIntent") else 0.6
                reasoning = "Action aligns with stated command intent" if ctx.get("commandIntent") else "Command intent unclear"
            elif virtue.code == "S":
                score = 0.8 if ctx.get("threatLikelihood", 0) > 0.5 else 0.6
                reasoning = f"Collective protection priority {'evident' if score >= virtue.default_threshold else 'unclear'}"
            else:
                score = 0.5
                reasoning = "Default evaluation"
        else:
            score = 0.5
            reasoning = "Unknown profile - using default evaluation"

        virtue_scores.append(VirtueScore(
            virtue=virtue.name, code=virtue.code, score=score, threshold=virtue.default_threshold,
            status="pass" if score >= virtue.default_threshold else "fail",
            reasoning=reasoning,
        ))

    composite_score = sum(v.score for v in virtue_scores) / max(1, len(virtue_scores))
    passed_count = sum(1 for v in virtue_scores if v.status == "pass")
    total = len(virtue_scores)

    if passed_count >= (total * 0.8).__ceil__():
        arbitration_decision = "allow"
        reasoning = f"Strong virtue alignment: {passed_count}/{total} principles satisfied"
    elif passed_count >= (total * 0.5).__ceil__():
        arbitration_decision = "escalate"
        reasoning = f"Mixed signals require human judgement: {passed_count}/{total} principles satisfied"
    else:
        arbitration_decision = "block"
        reasoning = f"Insufficient virtue alignment: only {passed_count}/{total} principles satisfied"

    return VirtueEthicsResult(
        triggered=True,
        trigger_reason="; ".join(trigger_reasons) or "Virtue arbitration required",
        virtue_scores=virtue_scores, composite_score=composite_score,
        arbitration_decision=arbitration_decision, reasoning=reasoning,
    )


# === Disposition Rules ===

def _resolve_disposition_rule_id(rule_id: str) -> str:
    return LEGACY_DISPOSITION_RULE_ALIASES.get(rule_id, rule_id)


def _get_disposition_rule(rule_id: str) -> Optional[Dict[str, Any]]:
    rid = _resolve_disposition_rule_id(rule_id)
    DISPOSITION_RULES = {
        "cdrils-v1.0-canonical": {
            "id": "cdrils-v1.0-canonical",
            "version": "1.0",
            "description": "Absolute-prohibition gate first; if not engaged, virtue arbitration if triggered, with harm-scale escalation override; otherwise C/D alignment.",
        },
        "cdrils-v1.1-canonical": {
            "id": "cdrils-v1.1-canonical",
            "version": "1.1",
            "description": f"Action-feature-based virtue scoring with non-compensatory gates on Respect, Integrity, and Loyalty. Composite ≥ {CDRILS_V1_0_COMPOSITE_ALLOW} → allow, {CDRILS_V1_0_COMPOSITE_ESCALATE}–{CDRILS_V1_0_COMPOSITE_ALLOW-1} → escalate, < {CDRILS_V1_0_COMPOSITE_ESCALATE} → block. Any non-compensatory gate firing forces block.",
        },
    }
    return DISPOSITION_RULES.get(rid)


# === Top-Level Orchestrator ===

def run_evaluation(scenario: Dict[str, Any], action: Dict[str, Any], virtues=None, profile_id: str = "CDRILS_V1_1") -> VorResult:
    if virtues is None:
        virtues = get_virtues_by_profile_id(profile_id)

    run_id = _generate_id()
    ts = _now()
    trace: List[TraceEntry] = []
    profile = get_virtue_profile(profile_id)

    trace.append(TraceEntry(
        id=_generate_id(), phase="input", description="Scenario and action parameters loaded",
        details=f"Scenario: {scenario.get('title', 'untitled')}\nAction: {action.get('name', 'unnamed')}\nLethality: {action.get('lethality', 'non-lethal')}\nVirtue Profile: {profile.name if profile else profile_id}",
        parameters={"scenarioId": scenario.get("id"), "actionId": action.get("id"), "profileId": profile_id},
        timestamp=ts,
    ))

    c_result = evaluate_consequentialist(scenario, action)
    trace.append(TraceEntry(
        id=_generate_id(), phase="consequentialist", description="Consequentialist evaluation complete",
        details=f"Score: {c_result.score:.3f}\nHarm Avoided: {c_result.harm_avoided:.3f}\nHarm Caused: {c_result.harm_caused:.3f}",
        parameters={f["name"]: f["value"] for f in c_result.factors},
        timestamp=ts,
    ))

    d_result = evaluate_deontological(scenario, action)
    trace.append(TraceEntry(
        id=_generate_id(), phase="deontological", description="Deontological evaluation complete",
        details=f"Status: {d_result.status}\n" + "\n".join(f"{r.rule_id}: {'✓' if r.passed else '✗'}" for r in d_result.rules_evaluated),
        parameters={"status": d_result.status, "rulesPassed": sum(1 for r in d_result.rules_evaluated if r.passed)},
        timestamp=ts,
    ))

    ve_result = evaluate_virtue_ethics(scenario, action, c_result, d_result, virtues, profile_id)
    trace.append(TraceEntry(
        id=_generate_id(), phase="virtue",
        description="Virtue ethics arbitration triggered" if ve_result.triggered else "Virtue ethics arbitration skipped",
        details=ve_result.reasoning if ve_result.triggered else ve_result.trigger_reason,
        parameters={"triggered": ve_result.triggered, "compositeScore": ve_result.composite_score, "profileId": profile_id},
        timestamp=ts,
    ))

    # Final disposition
    absolute_failure = next((r for r in d_result.rules_evaluated if r.rule_id == ABSOLUTE_PROHIBITION_RULE_ID and not r.passed), None)
    ec = action.get("expectedCasualties")
    civ_harm_absolute = ec.get("civilian", {}).get("expected", 0) if ec else 0
    civ_harm_rate = (ec.get("civilian", {}).get("expected", 0) / max(1, ec.get("populationAtRisk", 1))) if ec else 0
    harm_scale_trigger = civ_harm_rate >= HARM_SCALE_RATE_THRESHOLD or civ_harm_absolute >= HARM_SCALE_ABSOLUTE_THRESHOLD

    if absolute_failure:
        final_disposition = "block"
        rationale = f"Non-derogable prohibition engaged: {absolute_failure.reason} The virtue layer was reported for transparency but cannot override an absolute legal floor."
    elif ve_result.triggered:
        final_disposition = ve_result.arbitration_decision
        rationale = ve_result.reasoning
        if profile_id == "CDRILS_V1_1":
            if final_disposition == "allow" and civ_harm_absolute >= MAX_AUTONOMOUS_ALLOW_FATALITIES:
                final_disposition = "escalate"
                rationale = f"Lawful and virtue-consistent, but expected civilian fatalities ({civ_harm_absolute:,.0f}) reach the autonomous-allow ceiling — routed to human judgement."
        else:
            if final_disposition == "allow" and harm_scale_trigger and ve_result.composite_score < 0.75:
                final_disposition = "escalate"
                rationale = f"Lawful on the rules but harm scale ({civ_harm_absolute:,.0f} expected civilian fatalities) requires human judgement; virtue composite {ve_result.composite_score:.2f} below auto-allow threshold."
    elif d_result.status == "prohibited":
        final_disposition = "block"
        rationale = "Deontological constraints prohibit this action"
    elif d_result.status == "permitted" and c_result.score > 0:
        final_disposition = "allow"
        rationale = "C and D evaluations align in favour of action"
    else:
        final_disposition = "escalate"
        rationale = "Insufficient confidence for autonomous decision"

    trace.append(TraceEntry(
        id=_generate_id(), phase="output", description=f"Final disposition: {final_disposition.upper()}",
        details=rationale, parameters={"disposition": final_disposition}, timestamp=ts,
    ))

    citations = [Citation(
        id=c["id"], source_id=c["source_id"], title=c["title"],
        excerpt=c["excerpt"], relevance=c["relevance"],
    ) for r in d_result.rules_evaluated for c in r.citations]

    disposition_rule = _get_disposition_rule(DEFAULT_DISPOSITION_RULE_ID)

    return VorResult(
        id=run_id,
        scenario_id=scenario.get("id", ""),
        action_id=action.get("id", ""),
        timestamp=ts,
        model_version="1.0.0-alpha",
        ruleset_id=scenario.get("rulesetId", ""),
        ruleset_version="1.0.0",
        virtue_profile_id=profile_id,
        virtue_profile_version=f"{profile_id}-{profile.version if profile else '1.0'}",
        consequentialist=c_result,
        deontological=d_result,
        virtue_ethics=ve_result,
        disposition_rule_id=DEFAULT_DISPOSITION_RULE_ID,
        disposition_rule_version=disposition_rule.get("version", "1.0") if disposition_rule else "1.0",
        final_disposition=final_disposition,
        rationale=rationale,
        trace=trace,
        citations=citations,
    )