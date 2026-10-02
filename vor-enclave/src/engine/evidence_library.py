"""Vör Evidence Library — doctrinal sources for citation and traceability.

Each entry declares its source type, accessibility locator, substantive summary,
and the architectural commitments it underwrites. This library is static and
version-controlled; it does not learn or infer.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EvidenceEntry:
    id: str
    title: str
    source_type: str
    source_identification: str
    accessibility_locator: str
    substantive_summary: str
    architectural_commitments: List[str]
    date_entered: str
    date_of_last_review: str
    status: Optional[str] = None


GROUP_TITLES = {
    "A": "Framework Overview (§1)",
    "B": "Absolute-Prohibition Gate (§2)",
    "C": "Non-Compensatory Virtue Gates (§3)",
    "D": "Virtue Modelling Details (§4)",
    "E": "Disposition Rule (§5)",
    "F": "Known Limitations (§6)",
    "G": "Profile Pluggability and Dual-Use (§7)",
}

COMMITMENTS: List[dict] = [
    {"id": "C-A1", "group": "A", "section_title": GROUP_TITLES["A"],
     "text": "Ethical decision-support systems must operate under human authority; the system advises, it does not decide."},
    {"id": "C-A2", "group": "A", "section_title": GROUP_TITLES["A"],
     "text": "Ethical assessment is multi-dimensional and cannot be reduced to a single scalar score."},
    {"id": "C-A3", "group": "A", "section_title": GROUP_TITLES["A"],
     "text": "Some ethical considerations are non-compensatory: no aggregate score can override them."},
    {"id": "C-A4", "group": "A", "section_title": GROUP_TITLES["A"],
     "text": "Virtue ethics provides a defensible structural basis for machine-readable ethical assessment in high-stakes domains."},
    {"id": "C-B1", "group": "B", "section_title": GROUP_TITLES["B"],
     "text": "A defined set of actions constitutes categorical prohibitions whose violation halts assessment regardless of context, intention, or expected outcome."},
    {"id": "C-B2", "group": "B", "section_title": GROUP_TITLES["B"],
     "text": "Categorical prohibitions are grounded in established international humanitarian law and customary law, not in profile-specific preference."},
    {"id": "C-B3", "group": "B", "section_title": GROUP_TITLES["B"],
     "text": "The Absolute-Prohibition Gate is the first gate in disposition order; nothing downstream can release an action it blocks."},
    {"id": "C-B4", "group": "B", "section_title": GROUP_TITLES["B"],
     "text": "The gate's triggering conditions are enumerable, auditable, and version-controlled (not learned, not inferred)."},
    {"id": "C-C1", "group": "C", "section_title": GROUP_TITLES["C"],
     "text": "Designated virtues (in the CDRILS profile: Integrity, Selfless commitment, and where applicable Loyalty) operate as non-compensatory thresholds rather than scored contributions."},
    {"id": "C-C2", "group": "C", "section_title": GROUP_TITLES["C"],
     "text": "An action falling below the threshold on any non-compensatory virtue is blocked or escalated; high performance on other virtues cannot compensate."},
    {"id": "C-C3", "group": "C", "section_title": GROUP_TITLES["C"],
     "text": "The comparator for non-compensatory thresholds is >= (inclusive), not >."},
    {"id": "C-C4", "group": "C", "section_title": GROUP_TITLES["C"],
     "text": "The selection of which virtues are non-compensatory is profile-specific and must be justified per profile by reference to the profile's source doctrine."},
    {"id": "C-D1", "group": "D", "section_title": GROUP_TITLES["D"],
     "text": 'Each virtue is decomposed into named, defined sub-indicators ("value proxies") rather than assessed monolithically.'},
    {"id": "C-D2", "group": "D", "section_title": GROUP_TITLES["D"],
     "text": "Value proxies are drawn from the source doctrine of the profile in question (for CDRILS: the British Army's Values & Standards, etc.), not constructed by the system designer."},
    {"id": "C-D3", "group": "D", "section_title": GROUP_TITLES["D"],
     "text": "A profile's set of value proxies is auditable, enumerable, and version-controlled."},
    {"id": "C-D4", "group": "D", "section_title": GROUP_TITLES["D"],
     "text": "Scoring on value proxies feeds the relevant virtue score; the virtue score is the unit at which compensatory/non-compensatory logic operates."},
    {"id": "C-E1", "group": "E", "section_title": GROUP_TITLES["E"],
     "text": "Disposition (block / escalate / advise) is determined by a fixed gate order, not by aggregate score alone."},
    {"id": "C-E2", "group": "E", "section_title": GROUP_TITLES["E"],
     "text": "Escalation surfaces to a designated human decision-maker rather than auto-resolving."},
    {"id": "C-E3", "group": "E", "section_title": GROUP_TITLES["E"],
     "text": "The disposition rule is deterministic and reproducible given identical inputs."},
    {"id": "C-F1", "group": "F", "section_title": GROUP_TITLES["F"],
     "text": "The system's outputs are bounded by the quality of the profile and the quality of the input scoring; the architecture does not claim to resolve ethical disagreement."},
    {"id": "C-F2", "group": "F", "section_title": GROUP_TITLES["F"],
     "text": "The system explicitly does not address some classes of ethical question (e.g. ones outside its profile's source doctrine) and surfaces this rather than confabulating coverage."},
    {"id": "C-G1", "group": "G", "section_title": GROUP_TITLES["G"],
     "text": "The architecture is profile-pluggable: the same engine can host different ethical profiles drawn from different sectors' source doctrines."},
    {"id": "C-G2", "group": "G", "section_title": GROUP_TITLES["G"],
     "text": "Cross-sector deployment is mediated by consultancy with sector representatives to derive equivalent value/standard proxies from that sector's doctrine, not by translating CDRILS proxies."},
    {"id": "C-G3", "group": "G", "section_title": GROUP_TITLES["G"],
     "text": "Each deployed profile must declare its source doctrine and the chain of derivation from doctrine to proxies."},
]

ENTRIES: List[EvidenceEntry] = [
    EvidenceEntry(
        id="gc-ap1",
        title="GC-AP1 — Additional Protocol I to the Geneva Conventions (1977)",
        source_type="treaty",
        source_identification="Protocol Additional to the Geneva Conventions of 12 August 1949, and relating to the Protection of Victims of International Armed Conflicts (Protocol I), 8 June 1977.",
        accessibility_locator="https://ihl-databases.icrc.org/en/ihl-treaties/api-1977",
        substantive_summary="Additional Protocol I codifies the principles of distinction and proportionality as binding rules governing the conduct of hostilities in international armed conflict. Article 48 states the basic rule: parties shall at all times distinguish between the civilian population and combatants and between civilian objects and military objectives and direct operations only against military objectives. Article 51 prohibits attacks on the civilian population as such and on individual civilians, and prohibits indiscriminate attacks. Article 52 limits military objectives and establishes a presumption of civilian use in cases of doubt. Article 57 imposes precautionary obligations: feasible verification that targets are military objectives; feasible precautions to minimise civilian harm; the proportionality rule prohibiting attacks expected to cause incidental civilian harm excessive in relation to the concrete and direct military advantage anticipated; cancellation or suspension where these conditions are breached; and effective advance warning where circumstances permit.",
        architectural_commitments=["C-B1", "C-B2"],
        date_entered="2026-05-29",
        date_of_last_review="2026-05-29",
    ),
    EvidenceEntry(
        id="gc-iv",
        title="GC-IV — Fourth Geneva Convention (1949)",
        source_type="treaty",
        source_identification="Geneva Convention (IV) relative to the Protection of Civilian Persons in Time of War, 12 August 1949.",
        accessibility_locator="https://ihl-databases.icrc.org/en/ihl-treaties/gciv-1949",
        substantive_summary="Geneva Convention IV establishes the foundational regime for the protection of civilians during international armed conflict and occupation. Article 4 defines protected persons. Article 27 establishes that protected persons are entitled to respect for their persons, their honour, their family rights, their religious convictions and practices and shall at all times be humanely treated, and shall be protected especially against all acts of violence. Article 33 codifies individual responsibility and categorically prohibits collective penalties, intimidation, terrorism, pillage and reprisals against protected persons. Common Article 3 establishes a minimum floor of humane treatment in non-international armed conflict.",
        architectural_commitments=["C-B1"],
        date_entered="2026-05-29",
        date_of_last_review="2026-05-29",
    ),
    EvidenceEntry(
        id="icj-nuclear",
        title="ICJ Nuclear Weapons Advisory Opinion (1996)",
        source_type="case-law",
        source_identification="Legality of the Threat or Use of Nuclear Weapons, Advisory Opinion, ICJ Reports 1996, p. 226.",
        accessibility_locator="https://www.icj-cij.org/case/95",
        substantive_summary="In its 1996 Advisory Opinion the International Court of Justice identified the cardinal principles of international humanitarian law and established their status as binding on all States. At paragraph 78 the Court held that the first cardinal principle is aimed at the protection of the civilian population and establishes the distinction between combatants and non-combatants; States must never make civilians the object of attack. At paragraph 79 the Court characterised these rules as intransgressible principles of international customary law binding on all States whether or not they have ratified the conventions that contain them.",
        architectural_commitments=["C-B1", "C-B2"],
        date_entered="2026-05-29",
        date_of_last_review="2026-05-29",
    ),
    EvidenceEntry(
        id="icrc-cil",
        title="ICRC Customary IHL Study — Henckaerts & Doswald-Beck (2005)",
        source_type="customary-law",
        source_identification="International Committee of the Red Cross, Customary International Humanitarian Law, edited by Jean-Marie Henckaerts and Louise Doswald-Beck (Cambridge University Press, 2005).",
        accessibility_locator="https://ihl-databases.icrc.org/en/customary-ihl",
        substantive_summary="The ICRC Customary International Humanitarian Law Study identifies 161 rules of customary international humanitarian law, each derived from an extensive survey of state practice and opinio juris. The Study's per-rule framing is uniform: each rule is established by State practice as a norm of customary international law applicable in both international and non-international armed conflicts. Rule 70 prohibits means and methods of warfare which are of a nature to cause superfluous injury or unnecessary suffering. Rule 71 prohibits indiscriminate weapons. Rule 89 prohibits murder. Rule 14 supplies the proportionality rule. Rule 156 defines serious violations as war crimes.",
        architectural_commitments=["C-B1", "C-B2", "C-B3", "C-B4"],
        date_entered="2026-05-31",
        date_of_last_review="2026-05-31",
    ),
    EvidenceEntry(
        id="un-laws",
        title="UN Charter (1945)",
        source_type="treaty",
        source_identification="Charter of the United Nations, signed at San Francisco on 26 June 1945; entered into force on 24 October 1945.",
        accessibility_locator="https://www.un.org/en/about-us/un-charter",
        substantive_summary="The UN Charter is the foundational multilateral treaty of the modern international legal order. Under Article 103 it takes precedence over conflicting treaty obligations. Article 2(4) is the cornerstone prohibition: All Members shall refrain from the threat or use of force against the territorial integrity or political independence of any state. Article 51 preserves the inherent right of individual or collective self-defence if an armed attack occurs. Article 39 and 42 authorise collective military action by the Security Council.",
        architectural_commitments=["C-B1", "C-B2", "C-B3", "C-E2"],
        date_entered="2026-05-31",
        date_of_last_review="2026-05-31",
    ),
    EvidenceEntry(
        id="cdrils-def",
        title="British Army Values and Standards (2026)",
        source_type="institutional-doctrine",
        source_identification="Values and Standards of the British Army (iBooklet, January 2026 edition).",
        accessibility_locator="https://www.army.mod.uk/media/nbbnvnqs/values-standards-ibooklet-2026.pdf",
        substantive_summary="The British Army's Values and Standards defines the moral character expected of every soldier and officer. The Values are Courage, Discipline, Respect for Others, Integrity, Loyalty, and Selfless Commitment; the Standards are Lawful, Appropriate, Professional. Both are presented as constant, non-discretionary principles that define the behaviours expected of all members, whatever the circumstances. Respect for Others is explicitly extended to victims of conflict, the dead, the wounded, prisoners and civilians. Loyalty is bounded by a limit clause: wrong-doing should not be condoned or covered up.",
        architectural_commitments=["C-C1", "C-C4", "C-D2", "C-D3"],
        date_entered="2026-05-30",
        date_of_last_review="2026-05-30",
    ),
    EvidenceEntry(
        id="ajp-3_9",
        title="AJP-3.9 — Allied Joint Doctrine for Joint Targeting",
        source_type="institutional-doctrine",
        source_identification="AJP-3.9 (Edition B Version 1), Allied Joint Doctrine for Joint Targeting. NATO Standardization Office.",
        accessibility_locator="https://assets.publishing.service.gov.uk/media/618e7da28fa8f5037ffaa03f/AJP-3.9_EDB_V1_E.pdf",
        substantive_summary="AJP-3.9 is NATO's authoritative joint targeting doctrine. Section 1.5 establishes the six-phase Joint Targeting Cycle (Commander's intent → Target development → Capabilities analysis → Commander's decision and force planning → Mission planning and force execution → Assessment, closed loop). Section 1.5.2 mandates LEGAD presence on the targeting staff. Section 1.6 establishes the three-stack legal regime (NATO ROE + IHL/LOAC + domestic law) and the four IHL/LOAC principles: Humanity, Military Necessity, Distinction, and Proportionality. Section 1.7 covers PID, dual-use entity analysis, CDE methodology, and the delegated-authority escalation chain (NAC → SACEUR → JTF → CC).",
        architectural_commitments=["C-A1", "C-A3", "C-B1", "C-B2", "C-D3", "C-E2", "C-E3", "C-F1"],
        date_entered="2026-05-30",
        date_of_last_review="2026-05-30",
        status="foundational-reference",
    ),
    EvidenceEntry(
        id="ajp-5",
        title="AJP-5 — Allied Joint Doctrine for the Planning of Operations",
        source_type="institutional-doctrine",
        source_identification="NATO Standard AJP-5, Allied Joint Doctrine for the Planning of Operations, Edition A Version 2 with UK national elements (May 2019).",
        accessibility_locator="https://assets.publishing.service.gov.uk/media/6054d017e90e0724be025a8f/20210310-AJP_5_with_UK_elem_final_web.pdf",
        substantive_summary="AJP-5 establishes the doctrinal sequence by which strategic intent is translated into executable joint plans. Chapter 2: the commander's intent is the foundation of operations design. Chapter 3 binds human security into planning as a doctrinal requirement per UNSCR 1325. Chapter 4 specifies the planning sequence: mission analysis, COA development, COA review, operational planning directive. Mission analysis requires identification of limitations on operational freedom including constraints and restraints imposed by international law, the mandate, caveats of troop-contributing nations, and the commander's risk appetite and tolerance.",
        architectural_commitments=["C-A1", "C-B1", "C-B2", "C-D2", "C-E1"],
        date_entered="2026-05-29",
        date_of_last_review="2026-05-31",
        status="foundational-reference",
    ),
    EvidenceEntry(
        id="ajp-3",
        title="AJP-3 — Allied Joint Doctrine for the Conduct of Operations",
        source_type="institutional-doctrine",
        source_identification="NATO Standard AJP-3, Allied Joint Doctrine for the Conduct of Operations, Edition D Version 1 with UK national elements (August 2025).",
        accessibility_locator="https://assets.publishing.service.gov.uk/media/6964e72799fbdc498faecce2/AJP_3_Ed_D_V1-O.pdf",
        substantive_summary="AJP-3 is NATO's allied joint doctrine on operations conduct. Chapter 3 establishes mission command as NATO's philosophy for the command of military operations — decision authority with the human commander. Annex D establishes risk-management principles and the five-step ordered process (identify, analyse, evaluate, treat, monitor), and specifies that escalation surfaces to higher command and that outcomes should be documented and reported.",
        architectural_commitments=["C-A1", "C-D2", "C-D3", "C-E1", "C-E2"],
        date_entered="2026-05-31",
        date_of_last_review="2026-05-31",
    ),
    EvidenceEntry(
        id="jdp-0-01",
        title="JDP 0-01 — UK Defence Doctrine (6th Edition)",
        source_type="institutional-doctrine",
        source_identification="Joint Doctrine Publication 0-01, UK Defence Doctrine, 6th Edition (August 2022).",
        accessibility_locator="https://assets.publishing.service.gov.uk/media/63776f4de90e0728553b568b/UK_Defence_Doctrine_Ed6.pdf",
        substantive_summary="JDP 0-01 is the UK's capstone military doctrine. It establishes three core tenets: the manoeuvrist approach, mission command, and integrated action. Fighting power's hierarchy consists of a pre-eminent moral component (the will), a conceptual component (the thought process) and a physical component (the means). The effective employment of the military instrument is dependent on its legitimacy. Human security is an essential requirement to consider in operations.",
        architectural_commitments=["C-A1", "C-A3", "C-D3", "C-E2", "C-F1"],
        date_entered="2026-05-31",
        date_of_last_review="2026-05-31",
    ),
    EvidenceEntry(
        id="jdp-3-46",
        title="JDP 3-46 — Legal Support to Joint Operations (3rd Edition)",
        source_type="institutional-doctrine",
        source_identification="Joint Doctrine Publication 3-46, Legal Support to Joint Operations, 3rd Edition (June 2018).",
        accessibility_locator="https://assets.publishing.service.gov.uk/media/5b23ab59e5274a18fc321cad/20180614-doctrine_uk_legal_spt_jdp_3_46.pdf",
        substantive_summary="JDP 3-46 is the UK's joint doctrine on legal support to operations. Chapter 2: Armed Forces must obey all lawful orders, but must refuse to obey any manifestly unlawful order. Chapter 3 binds legality into the planning sequence at the earliest stage. Chapter 4 extends the same gate-discipline to targeting: at every stage, commanders and targeting staff must ensure that their actions are lawful. Chapter 5: the legal adviser's overriding duty is to provide timely, accurate, relevant, succinct and robust advice; decision authority resides with the commander.",
        architectural_commitments=["C-A1", "C-B1", "C-B2", "C-B3", "C-E1"],
        date_entered="2026-05-31",
        date_of_last_review="2026-05-31",
    ),
    EvidenceEntry(
        id="jdp-04",
        title="JDP 04 — Understanding and Decision-making (2nd Edition)",
        source_type="institutional-doctrine",
        source_identification="Joint Doctrine Publication 04, Understanding and Decision-making, 2nd Edition (December 2016).",
        accessibility_locator="https://assets.publishing.service.gov.uk/media/5a80b2f340f0b62305b8ca55/doctrine_uk_understanding_jdp_04.pdf",
        substantive_summary="JDP 04 is the UK's joint doctrine on how Defence develops understanding and converts it into decisions. Chapter 1 names four principles of understanding: self-awareness, critical analysis, creative thinking, and continuity. Chapter 2 binds understanding to decision: the better our understanding, the better-informed our decisions. It enumerates threats to sound team judgement — peer pressure, groupthink, social prejudice — and warns that unless we have some awareness of how we think, we cannot mitigate potentially adverse effects. Decision authority resides with the commander; teams advise.",
        architectural_commitments=["C-A1", "C-D2", "C-E2", "C-F1"],
        date_entered="2026-05-31",
        date_of_last_review="2026-05-31",
    ),
    EvidenceEntry(
        id="jsp-398",
        title="JSP 398 — UK Manual of National Rules of Engagement",
        source_type="institutional-doctrine",
        source_identification="JSP 398, United Kingdom Manual of National Rules of Engagement, Part 1: Directive (Edition Jul 19).",
        accessibility_locator="https://committees.parliament.uk/publications/42314/documents/210415/default/",
        substantive_summary="JSP 398 is the UK MOD's national policy directive for the use of force. It nests with JSP 900 and theatre-specific Targeting Directives. Commanders are individually responsible for ensuring only the degree of force which is lawful in the circumstances is used. UK forces must never apply force in such a way that it would constitute a breach of the law of England and Wales (para 16) — the UK national non-compensatory clause. Default-deny-on-doubt: if in any doubt, always seek legal advice. ROEAUTH delegated authority chain.",
        architectural_commitments=["C-A1", "C-A3", "C-B1", "C-D3", "C-E2", "C-E3", "C-F1"],
        date_entered="2026-05-30",
        date_of_last_review="2026-05-30",
    ),
    EvidenceEntry(
        id="jsp-936",
        title="JSP 936 Part 1 — Dependable AI in Defence",
        source_type="institutional-doctrine",
        source_identification="JSP 936 Part 1: Dependable Artificial Intelligence (AI) in Defence — Directive, V1.1 November 2024.",
        accessibility_locator="https://assets.publishing.service.gov.uk/media/6735fc89f6920bfb5abc7b62/JSP936_Part1.pdf",
        substantive_summary="JSP 936 Part 1 is the UK MOD's directive for the responsible use of AI in Defence. Five Ethical Principles: Human-centricity, Responsibility, Understanding, Bias and harm mitigation, Reliability. MOD frames its approach as building reliable systems operating under meaningful human control. AI in kinetic effects and novel or contentious applications receive automatic special attention. Where ethical risks become unacceptable, deployment or development must be halted in a safe manner. RAISO accountability chain and annual Statements of AI Ethical Assurance.",
        architectural_commitments=["C-A1", "C-A3", "C-B1", "C-D3", "C-E2", "C-E3", "C-F1"],
        date_entered="2026-05-30",
        date_of_last_review="2026-05-30",
    ),
]

SOURCE_ID_TO_ENTRY_ID = {
    "GC-AP1": "gc-ap1",
    "GC-IV": "gc-iv",
    "DOD-LOAC": "dod-loac",
    "ICJ-NUCLEAR": "icj-nuclear",
    "CDRILS-DEF": "cdrils-def",
    "UN-LAWS": "un-laws",
    "AJP-3.9": "ajp-3_9",
    "JDP-0-01": "jdp-0-01",
    "JDP-3-46": "jdp-3-46",
    "JSP-398": "jsp-398",
    "JSP-936": "jsp-936",
    "ICRC-CIL": "icrc-cil",
}


def get_evidence_entry(entry_id: str) -> Optional[EvidenceEntry]:
    for entry in ENTRIES:
        if entry.id == entry_id:
            return entry
    return None


def get_entries_by_commitment(commitment_id: str) -> List[EvidenceEntry]:
    return [e for e in ENTRIES if commitment_id in e.architectural_commitments]


def title_for_source_id(source_id: str) -> str:
    entry_id = SOURCE_ID_TO_ENTRY_ID.get(source_id)
    if entry_id:
        entry = get_evidence_entry(entry_id)
        if entry:
            return entry.title
    return source_id