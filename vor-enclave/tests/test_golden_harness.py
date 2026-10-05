"""Golden Validation Harness

Deterministic regression tests for the Vör engine. Each test asserts that a
canonical input produces the *expected* final disposition. If any test fails,
the engine has drifted from its certified behaviour and must not deploy.

Cases are drawn from the original JS engine's stress-test scenarios and
represent the boundary conditions that accreditation will scrutinise:
- absolute prohibitions must always block
- lawful non-lethal with good virtue scores must allow
- ambiguous lethal with mixed signals must escalate
- non-compensatory virtue gate firing must block regardless of other scores
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engine.evaluation_engine import run_evaluation
from engine.virtue_profiles import get_virtues_by_profile_id


def _make_scenario(title: str, threat: float, uncertainty: float, civ: int, time_pressure: str,
                   intent: str, objectives: list, lawful: bool = True) -> dict:
    return {
        "id": f"scn-{title.lower().replace(' ', '-')}",
        "title": title,
        "context": {
            "threatLikelihood": threat,
            "uncertaintyLevel": uncertainty,
            "civilianPresence": civ,
            "timePressure": time_pressure,
            "commandIntent": intent,
            "commandIntentLawful": lawful,
            "commandIntentObjectives": objectives,
        },
    }


def _make_action(name: str, lethality: str, preconditions: list, effects: list,
                 actor_cost: dict, proc_comp: dict, risk_bearers: list, harmed: list,
                 aligns: list, casualties: Optional[dict], abs_prohibs: dict) -> dict:
    action = {
        "id": f"act-{name.lower().replace(' ', '-')[:20]}",
        "name": name,
        "description": name,
        "lethality": lethality,
        "preconditions": preconditions,
        "expectedEffects": effects,
        "actorCost": actor_cost,
        "processCompliance": proc_comp,
        "riskBearers": risk_bearers,
        "directlyHarmed": harmed,
        "alignsWith": aligns,
        "absoluteProhibitions": abs_prohibs,
    }
    if casualties is not None:
        action["expectedCasualties"] = casualties
    return action


CASES = [
    # 1. Absolute prohibition: torture is always block
    {
        "name": "TORTURE_ALWAYS_BLOCKS",
        "profile": "CDRILS_V1_1",
        "scenario": _make_scenario(
            "Hostile detainee interrogation", threat=0.8, uncertainty=0.2, civ=0,
            time_pressure="critical", intent="Extract time-critical intelligence",
            objectives=["intelligence extraction"],
        ),
        "action": _make_action(
            "Enhanced interrogation with waterboarding", lethality="non-lethal",
            preconditions=["Detainee confirmed hostile", "Legal advice obtained"],
            effects=["intelligence obtained"],
            actor_cost={"institutional": 0.9, "professional": 0.8, "reputational": 0.9, "physical": 0.2},
            proc_comp={"pidApplied": True, "roeFollowed": True, "escalationCorrect": True, "documented": True},
            risk_bearers=[{"group": "own-unit", "share": 0.1}, {"group": "patient-in-care", "share": 0.9}],
            harmed=[{"groupId": "detainee", "vulnerability": 0.9, "harmShare": 0.9, "inCustodyOrCare": True}],
            aligns=["intelligence extraction"],
            casualties={"populationAtRisk": 1, "civilian": {"expected": 0, "min": 0, "max": 0}},
            abs_prohibs={"torture": True, "cruelInhumanTreatment": False},
        ),
        "expected": "block",
        "reason_contains": "Non-derogable prohibition engaged",
    },
    # 2. Unambiguous non-lethal warning (v1.1) → allow (high composite)
    {
        "name": "WARN_UNKNOWN_ALLOW",
        "profile": "CDRILS_V1_1",
        "scenario": _make_scenario(
            "Unknown aircraft near border", threat=0.3, uncertainty=0.4, civ=30,
            time_pressure="normal", intent="Establish airspace sovereignty",
            objectives=["defend airspace", "positive identification"],
        ),
        "action": _make_action(
            "Radio warning to unknown aircraft", lethality="non-lethal",
            preconditions=["Radio contact attempted", "Language available"],
            effects=["compliance or clarification"],
            actor_cost={"institutional": 0.2, "professional": 0.3, "reputational": 0.1, "physical": 0.1},
            proc_comp={"pidApplied": True, "roeFollowed": True, "escalationCorrect": True, "documented": True},
            risk_bearers=[{"group": "own-unit", "share": 0.1}, {"group": "civilian", "share": 0.05}],
            harmed=[],
            aligns=["defend airspace", "positive identification", "minimise civilian exposure"],
            casualties={"populationAtRisk": 0, "civilian": {"expected": 0, "min": 0, "max": 0}},
            abs_prohibs={},
        ),
        "expected": "allow",
        "reason_contains": "v1.1 composite",
    },
    # 2b. C/D aligned without virtue arbitration → allow (only under v1.0 profile)
    {
        "name": "WARN_UNKNOWN_V10_ALLOW",
        "profile": "CDRILS",
        "scenario": _make_scenario(
            "Friendly drone routine transit", threat=0.4, uncertainty=0.1, civ=10,
            time_pressure="normal", intent="Routine airspace management",
            objectives=["routine transit"],
        ),
        "action": _make_action(
            "Routine drone transit authorisation", lethality="non-lethal",
            preconditions=["Flight plan filed", "Transponder on"],
            effects=["transit completed"],
            actor_cost={"institutional": 0.1, "professional": 0.2, "reputational": 0.0, "physical": 0.0},
            proc_comp={"pidApplied": True, "roeFollowed": True, "escalationCorrect": True, "documented": True},
            risk_bearers=[{"group": "own-unit", "share": 0.0}, {"group": "civilian", "share": 0.0}],
            harmed=[],
            aligns=["routine transit"],
            casualties=None,
            abs_prohibs={},
        ),
        "expected": "allow",
        "reason_contains": "C and D evaluations align",
    },
    # 3. Interception near civilians with genuinely mixed signals → escalate band
    {
        "name": "INTERCEPT_UNKNOWN_ESCALATE",
        "profile": "CDRILS_V1_1",
        "scenario": _make_scenario(
            "Low-flying unidentified aircraft over village", threat=0.35, uncertainty=0.5, civ=80,
            time_pressure="high", intent="Defend airspace; avoid civilian harm",
            objectives=["defend airspace", "minimise civilian exposure", "positive identification"],
        ),
        "action": _make_action(
            "Low-altitude fighter interception over village", lethality="potentially-lethal",
            preconditions=["PID attempted", "ROE obtained", "Civilian briefing"],
            effects=["visual contact", "compliance determination"],
            actor_cost={"institutional": 0.2, "professional": 0.2, "reputational": 0.2, "physical": 0.2},
            proc_comp={"pidApplied": True, "roeFollowed": False, "escalationCorrect": False, "documented": True},
            risk_bearers=[{"group": "own-unit", "share": 0.25}, {"group": "civilian", "share": 0.55}, {"group": "third-party", "share": 0.20}],
            harmed=[{"groupId": "village_residents", "vulnerability": 0.4, "harmShare": 0.5, "inCustodyOrCare": False}],
            aligns=["defend airspace"],
            casualties={"populationAtRisk": 100, "civilian": {"expected": 30, "min": 10, "max": 50}},
            abs_prohibs={},
        ),
        "expected": "escalate",
        "reason_contains": "in escalate band",
    },
    # 4. Confirmed hostile, low civilian risk, full virtue → allow
    {
        "name": "ENGAGE_HOSTILE_ALLOW",
        "profile": "CDRILS_V1_1",
        "scenario": _make_scenario(
            "Confirmed hostile drone over desert", threat=0.9, uncertainty=0.1, civ=5,
            time_pressure="critical", intent="Neutralise imminent threat",
            objectives=["defend airspace", "neutralise threat"],
        ),
        "action": _make_action(
            "Kinetic engagement of hostile drone", lethality="lethal",
            preconditions=["Hostile confirmed", "PID established", "ROE kinetic met", "Desert clear"],
            effects=["drone neutralised"],
            actor_cost={"institutional": 0.8, "professional": 0.9, "reputational": 0.6, "physical": 0.9},
            proc_comp={"pidApplied": True, "roeFollowed": True, "escalationCorrect": True, "documented": True},
            risk_bearers=[{"group": "own-unit", "share": 0.65}, {"group": "civilian", "share": 0.10}, {"group": "third-party", "share": 0.25}],
            harmed=[{"groupId": "drone_operator", "vulnerability": 0.7, "harmShare": 0.85, "inCustodyOrCare": False}],
            aligns=["defend airspace", "neutralise threat"],
            casualties={"populationAtRisk": 2, "civilian": {"expected": 0, "min": 0, "max": 1}},
            abs_prohibs={},
        ),
        "expected": "allow",
        "reason_contains": "allow",
    },
    # 5. High displaced risk with in-custody/care → Respect gate fires → block
    {
        "name": "HIGH_DISPLACED_BLOCK",
        "profile": "CDRILS_V1_1",
        "scenario": _make_scenario(
            "Artillery suppression near refugee camp", threat=0.7, uncertainty=0.3, civ=95,
            time_pressure="high", intent="Suppress enemy mortar",
            objectives=["force protection", "minimise civilian exposure"],
        ),
        "action": _make_action(
            "Artillery barrage near camp", lethality="lethal",
            preconditions=["Mortar located", "Camp coordinates known", "ROE checked"],
            effects=["mortar suppressed"],
            actor_cost={"institutional": 0.7, "professional": 0.6, "reputational": 0.3, "physical": 0.8},
            proc_comp={"pidApplied": True, "roeFollowed": True, "escalationCorrect": True, "documented": True},
            risk_bearers=[{"group": "own-unit", "share": 0.2}, {"group": "civilian", "share": 0.7}, {"group": "third-party", "share": 0.1}],
            harmed=[{"groupId": "camp_residents", "vulnerability": 0.9, "harmShare": 0.7, "inCustodyOrCare": True}],
            aligns=["force protection"],
            casualties={"populationAtRisk": 2000, "civilian": {"expected": 50, "min": 20, "max": 120}},
            abs_prohibs={},
        ),
        "expected": "block",
        "reason_contains": "Respect",
    },
    # 6. Deliberately weak inputs across all virtues → low composite → escalate
    {
        "name": "LOW_COMPOSITE_ESCALATE",
        "profile": "CDRILS_V1_1",
        "scenario": _make_scenario(
            "Suspected IED emplacement", threat=0.6, uncertainty=0.4, civ=40,
            time_pressure="high", intent="Prevent IED attack",
            objectives=["force protection", "positive identification"],
        ),
        "action": _make_action(
            "Pre-emptive strike on suspected emplacer", lethality="lethal",
            preconditions=[],
            effects=["emplacer neutralised"],
            actor_cost={"institutional": 0.2, "professional": 0.2, "reputational": 0.2, "physical": 0.2},
            proc_comp={"pidApplied": False, "roeFollowed": False, "escalationCorrect": False, "documented": False},
            risk_bearers=[{"group": "own-unit", "share": 0.3}, {"group": "civilian", "share": 0.5}, {"group": "third-party", "share": 0.2}],
            harmed=[{"groupId": "suspect", "vulnerability": 0.5, "harmShare": 0.8, "inCustodyOrCare": False}],
            aligns=["force protection"],
            casualties={"populationAtRisk": 1, "civilian": {"expected": 0, "min": 0, "max": 0}},
            abs_prohibs={},
        ),
        "expected": "escalate",
        "reason_contains": "in escalate band",
    },
    # 7. Lawful but high expected fatalities → escalate (autonomous-allow ceiling)
    {
        "name": "HIGH_CIV_FAT_ESCALATE",
        "profile": "CDRILS_V1_1",
        "scenario": _make_scenario(
            "Urban close air support", threat=0.8, uncertainty=0.2, civ=90,
            time_pressure="critical", intent="Extract besieged unit",
            objectives=["force protection", "minimise civilian exposure"],
        ),
        "action": _make_action(
            "Precision strike on urban strongpoint", lethality="lethal",
            preconditions=["PID confirmed", "ROE obtained", "Collateral estimate reviewed"],
            effects=["strongpoint destroyed", "unit extracted"],
            actor_cost={"institutional": 0.9, "professional": 0.9, "reputational": 0.7, "physical": 0.9},
            proc_comp={"pidApplied": True, "roeFollowed": True, "escalationCorrect": True, "documented": True},
            risk_bearers=[{"group": "own-unit", "share": 0.45}, {"group": "civilian", "share": 0.40}, {"group": "third-party", "share": 0.15}],
            harmed=[{"groupId": "building_occupants", "vulnerability": 0.6, "harmShare": 0.4, "inCustodyOrCare": False}],
            aligns=["force protection", "minimise civilian exposure"],
            casualties={"populationAtRisk": 150, "civilian": {"expected": 15, "min": 5, "max": 30}},
            abs_prohibs={},
        ),
        "expected": "escalate",
        "reason_contains": "autonomous-allow ceiling",
    },
]


def run_all():
    passed = 0
    failed = 0
    for case in CASES:
        profile = case.get("profile", "CDRILS_V1_1")
        virtues = get_virtues_by_profile_id(profile)
        result = run_evaluation(case["scenario"], case["action"], virtues, profile)
        ok = result.final_disposition == case["expected"]
        reason_ok = case["reason_contains"].lower() in result.rationale.lower()
        if ok and reason_ok:
            print(f"PASS  {case['name']:30s}  profile={profile:12s}  disp={result.final_disposition:8s}  rationale matched")
            passed += 1
        else:
            print(f"FAIL  {case['name']:30s}  profile={profile:12s}  expected={case['expected']:8s}  got={result.final_disposition:8s}")
            if not reason_ok:
                print(f"      rationale expected to contain '{case['reason_contains']}' but got:")
                print(f"      {result.rationale[:120]}...")
            failed += 1
    print(f"\n{passed}/{len(CASES)} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)