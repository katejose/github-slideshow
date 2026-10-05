"""Vör Virtue Profiles — CDRILS and pluggable profile system.

Profiles define the virtues, their proxy logic, thresholds, and whether each
gate is compensatory (weighted) or non-compensatory (veto).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VirtueInput:
    path: str
    required: bool = False


@dataclass
class Virtue:
    code: str
    name: str
    description: str
    proxy_logic: str
    default_threshold: float
    proxy_version: str
    gate_mode: str  # "weighted" or "non-compensatory"
    threshold_rationale: Dict[str, str] = field(default_factory=dict)
    inputs: List[VirtueInput] = field(default_factory=list)


@dataclass
class VirtueProfile:
    id: str
    name: str
    version: str
    description: str
    virtues: List[Virtue]


CDRILS_VIRTUES: List[Virtue] = [
    Virtue(
        code="C",
        name="Courage",
        description="Willingness to act under uncertainty when duty demands",
        proxy_logic="risk_acceptance_under_duty",
        default_threshold=0.6,
        proxy_version="1.0",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "Courage should be demonstrated when operational tempo genuinely demands action, not routinely.",
            "derived_from": "British Army Values and Standards",
        },
        inputs=[VirtueInput(path="scenario.context.timePressure")],
    ),
    Virtue(
        code="D",
        name="Discipline",
        description="Adherence to rules, chain of command, and self-control",
        proxy_logic="rule_compliance_score",
        default_threshold=0.8,
        proxy_version="1.0",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "80% rule compliance reflects that most rules should be satisfied with limited tolerance for justified exceptions.",
            "derived_from": "UK JSP 830 / LOAC ruleset",
        },
        inputs=[VirtueInput(path="deontological.rulesEvaluated")],
    ),
    Virtue(
        code="R",
        name="Respect for Others",
        description="Recognition of human dignity and rights of all persons",
        proxy_logic="civilian_protection_weight",
        default_threshold=0.7,
        proxy_version="1.0",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "Actions with high civilian exposure and lethal force must face significant scrutiny.",
            "derived_from": "GC IV / AP I Art. 51",
        },
        inputs=[
            VirtueInput(path="scenario.context.civilianPresence"),
            VirtueInput(path="action.lethality"),
        ],
    ),
    Virtue(
        code="I",
        name="Integrity",
        description="Consistency between stated values and actions",
        proxy_logic="consistency_check",
        default_threshold=0.75,
        proxy_version="1.0",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "Actions should have documented preconditions, reflecting transparent decision-making.",
            "derived_from": "AJP-3.9 documentation requirements",
        },
        inputs=[VirtueInput(path="action.preconditions")],
    ),
    Virtue(
        code="L",
        name="Loyalty",
        description="Commitment to mission, colleagues, and institution",
        proxy_logic="mission_alignment_score",
        default_threshold=0.65,
        proxy_version="1.0",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "Allows flexibility when command intent is ambiguous, but expects alignment when intent is clear.",
            "derived_from": "JDP 0-01 chain-of-command guidance",
        },
        inputs=[VirtueInput(path="scenario.context.commandIntent")],
    ),
    Virtue(
        code="S",
        name="Selfless Commitment",
        description="Prioritizing collective good over personal interest",
        proxy_logic="altruism_indicator",
        default_threshold=0.7,
        proxy_version="1.0",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "Action should be motivated by genuine collective benefit, not convenience.",
            "derived_from": "British Army Values and Standards — Selfless Commitment",
        },
        inputs=[VirtueInput(path="scenario.context.threatLikelihood")],
    ),
]

CDRILS_V1_1_VIRTUES: List[Virtue] = [
    Virtue(
        code="C",
        name="Courage",
        description="Willingness to act under uncertainty when duty demands",
        proxy_logic="risk_acceptance_under_duty",
        default_threshold=0.45,
        proxy_version="1.1",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "Courage should be demonstrated when operational tempo genuinely demands action, not routinely.",
            "derived_from": "British Army Values and Standards",
        },
        inputs=[VirtueInput(path="action.actorCost", required=True)],
    ),
    Virtue(
        code="D",
        name="Discipline",
        description="Adherence to rules, chain of command, and self-control",
        proxy_logic="rule_compliance_score",
        default_threshold=0.8,
        proxy_version="1.1",
        gate_mode="weighted",
        threshold_rationale={
            "basis": "80% rule compliance reflects that most rules should be satisfied with limited tolerance for justified exceptions.",
            "derived_from": "UK JSP 830 / LOAC ruleset",
        },
        inputs=[
            VirtueInput(path="deontological.rulesEvaluated"),
            VirtueInput(path="action.processCompliance", required=True),
        ],
    ),
    Virtue(
        code="R",
        name="Respect for Others",
        description="Recognition of human dignity and rights of all persons",
        proxy_logic="civilian_protection_weight",
        default_threshold=0.6,
        proxy_version="1.1",
        gate_mode="non-compensatory",
        threshold_rationale={
            "basis": "Actions with high civilian exposure and lethal force must face significant scrutiny.",
            "derived_from": "GC IV / AP I Art. 51",
        },
        inputs=[VirtueInput(path="action.directlyHarmed")],
    ),
    Virtue(
        code="I",
        name="Integrity",
        description="Consistency between stated values and actions",
        proxy_logic="consistency_check",
        default_threshold=0.7,
        proxy_version="1.1",
        gate_mode="non-compensatory",
        threshold_rationale={
            "basis": "Actions should have documented preconditions, reflecting transparent decision-making.",
            "derived_from": "AJP-3.9 documentation requirements",
        },
        inputs=[
            VirtueInput(path="action.preconditions", required=True),
            VirtueInput(path="deontological.rulesEvaluated"),
        ],
    ),
    Virtue(
        code="L",
        name="Loyalty",
        description="Commitment to mission, colleagues, and institution",
        proxy_logic="mission_alignment_score",
        default_threshold=0.65,
        proxy_version="1.1",
        gate_mode="non-compensatory",
        threshold_rationale={
            "basis": "Allows flexibility when command intent is ambiguous, but expects alignment when intent is clear.",
            "derived_from": "JDP 0-01 chain-of-command guidance",
        },
        inputs=[
            VirtueInput(path="scenario.context.commandIntentObjectives", required=True),
            VirtueInput(path="scenario.context.commandIntentLawful"),
            VirtueInput(path="action.alignsWith"),
        ],
    ),
    Virtue(
        code="S",
        name="Selfless Commitment",
        description="Prioritizing collective good over personal interest",
        proxy_logic="altruism_indicator",
        default_threshold=0.65,
        proxy_version="1.1",
        gate_mode="non-compensatory",
        threshold_rationale={
            "basis": "Action should be motivated by genuine collective benefit, not convenience.",
            "derived_from": "British Army Values and Standards — Selfless Commitment",
        },
        inputs=[VirtueInput(path="action.riskBearers", required=True)],
    ),
]

VIRTUE_PROFILES: List[VirtueProfile] = [
    VirtueProfile(
        id="CDRILS",
        name="CDRILS",
        version="1.0",
        description="British Army Core Values Framework - Courage, Discipline, Respect, Integrity, Loyalty, Selfless Commitment",
        virtues=CDRILS_VIRTUES,
    ),
    VirtueProfile(
        id="CDRILS_V1_1",
        name="CDRILS (v1.1)",
        version="1.1",
        description="CDRILS rebuilt as functions of action features. Canonical profile as of v1.1.",
        virtues=CDRILS_V1_1_VIRTUES,
    ),
]


def get_virtue_profile(profile_id: str) -> Optional[VirtueProfile]:
    for profile in VIRTUE_PROFILES:
        if profile.id == profile_id:
            return profile
    return None


def get_virtues_by_profile_id(profile_id: str = "CDRILS_V1_1") -> List[Virtue]:
    profile = get_virtue_profile(profile_id)
    if profile:
        return profile.virtues
    return CDRILS_VIRTUES