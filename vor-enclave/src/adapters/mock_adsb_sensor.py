"""Mock ADS-B Radar Feed Adapter

Generates synthetic air-traffic tracks and maps them to Vör scenario/action
inputs. In a real deployment this would replace the `generate_tracks()` stub
with a parser that reads from a Palantir Foundry OSDK Object or a UDP socket.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import random


@dataclass
class AdsbTrack:
    track_id: str
    callsign: str
    classification: str  # "civilian", "military", "unknown", "hostile"
    latitude: float
    longitude: float
    altitude_m: int
    speed_kts: int
    heading_deg: int
    squawk: str
    timestamp_iso: str
    proximity_km: float  # distance to protected airspace / ground asset
    civilian_proximity_km: float  # distance to nearest civilian area


def generate_tracks(seed: int = 42, count: int = 6) -> List[AdsbTrack]:
    """Synthetic radar-track generator for validation harness."""
    random.seed(seed)
    bases = [
        ("BAW249", "civilian", 51.47, -0.46, 8000, 450, 90, "7001", 12.0, 2.0),
        ("RCH452", "military", 51.51, -0.12, 15000, 380, 270, "4002", 45.0, 8.0),
        ("UNK001", "unknown", 51.55, 0.05, 3000, 220, 180, "7700", 3.0, 0.5),
        ("RED901", "hostile", 51.48, -0.30, 500, 150, 45, "0000", 1.5, 0.2),
        ("CFC01", "civilian", 51.40, -0.60, 12000, 480, 0, "7002", 80.0, 15.0),
        ("MILOPS", "military", 51.52, -0.20, 2000, 300, 135, "4001", 5.0, 1.0),
    ]
    tracks = []
    for i in range(min(count, len(bases))):
        cs, cls, lat, lon, alt, spd, hdg, sq, prox, civprox = bases[i]
        tracks.append(AdsbTrack(
            track_id=f"T{i+1:03d}",
            callsign=cs,
            classification=cls,
            latitude=lat,
            longitude=lon,
            altitude_m=alt,
            speed_kts=spd,
            heading_deg=hdg,
            squawk=sq,
            timestamp_iso="2026-10-02T16:00:00Z",
            proximity_km=prox,
            civilian_proximity_km=civprox,
        ))
    return tracks


def _threat_from_track(track: AdsbTrack) -> float:
    """Derive threat likelihood 0-1 from track features."""
    if track.classification == "hostile":
        return 0.95
    if track.classification == "unknown":
        return 0.6 if track.proximity_km < 5 else 0.3
    if track.classification == "military":
        return 0.4 if track.proximity_km < 10 else 0.1
    return 0.05


def _civilian_presence_from_track(track: AdsbTrack) -> int:
    """Derive civilian presence 0-100 from proximity to civilian areas."""
    if track.classification == "civilian":
        return 80
    if track.civilian_proximity_km < 1:
        return 90
    if track.civilian_proximity_km < 5:
        return 60
    if track.civilian_proximity_km < 15:
        return 30
    return 10


def _uncertainty_from_track(track: AdsbTrack) -> float:
    """Uncertainty 0-1: higher for unknown tracks, lower for confirmed."""
    if track.classification == "unknown":
        return 0.5
    if track.classification == "hostile":
        return 0.1
    return 0.2


def map_tracks_to_vor_input(tracks: List[AdsbTrack], proposed_response: str = "interception") -> Optional[Dict[str, Any]]:
    """Map a radar track batch to a single Vör scenario + action pair.

    In a real system the context engine would fuse multiple tracks into a
    consolidated situation picture. Here we take the highest-threat track
    as the focal scenario and build the action from the proposed response.
    """
    if not tracks:
        return None

    primary = max(tracks, key=_threat_from_track)
    threat = _threat_from_track(primary)
    civ_presence = _civilian_presence_from_track(primary)
    uncertainty = _uncertainty_from_track(primary)

    # Build scenario context
    scenario = {
        "id": f"scn-{primary.track_id}",
        "title": f"Airspace incursion: {primary.callsign} ({primary.classification})",
        "context": {
            "threatLikelihood": round(threat, 2),
            "uncertaintyLevel": round(uncertainty, 2),
            "civilianPresence": civ_presence,
            "timePressure": "critical" if threat > 0.7 else ("high" if threat > 0.4 else "normal"),
            "commandIntent": "Defend protected airspace; minimise civilian exposure",
            "commandIntentLawful": True,
            "commandIntentObjectives": ["defend airspace", "minimise civilian exposure", "positive identification"],
        },
    }

    # Build proposed action from response type
    if proposed_response == "interception":
        action = {
            "id": f"act-{primary.track_id}-intercept",
            "name": "Aircraft interception with fighter escort",
            "description": "Launch fighter aircraft to intercept and visually identify the target; force landing if non-compliant.",
            "lethality": "potentially-lethal",
            "preconditions": ["Positive identification attempted via radio", "ROE authorisation obtained", "Civilian area avoidance briefed"],
            "expectedEffects": ["visual contact established", "compliance or non-compliance determined"],
            "actorCost": {
                "institutional": 0.7,
                "professional": 0.6,
                "reputational": 0.4,
                "physical": 0.8,
            },
            "processCompliance": {
                "pidApplied": True,
                "roeFollowed": True,
                "escalationCorrect": True,
                "documented": True,
            },
            "riskBearers": [
                {"group": "own-unit", "share": 0.55},
                {"group": "civilian", "share": 0.30},
                {"group": "third-party", "share": 0.15},
            ],
            "directlyHarmed": [
                {"groupId": "nearby_civilians", "vulnerability": 0.4, "harmShare": 0.3, "inCustodyOrCare": False},
            ],
            "alignsWith": ["defend airspace", "positive identification"],
            "expectedCasualties": {
                "populationAtRisk": 120,
                "civilian": {"expected": 0, "min": 0, "max": 3},
            },
            "absoluteProhibitions": {},
        }
    elif proposed_response == "engage":
        action = {
            "id": f"act-{primary.track_id}-engage",
            "name": "Kinetic engagement of confirmed hostile aircraft",
            "description": "Fire air-to-air missile at confirmed hostile aircraft that has failed to comply with interception and poses imminent threat to ground assets.",
            "lethality": "lethal",
            "preconditions": ["Hostile intent confirmed", "PID established", "ROE kinetic threshold met", "Civilian area assessed"],
            "expectedEffects": ["aircraft neutralised", "debris field contained"],
            "actorCost": {
                "institutional": 0.8,
                "professional": 0.9,
                "reputational": 0.6,
                "physical": 0.9,
            },
            "processCompliance": {
                "pidApplied": True,
                "roeFollowed": True,
                "escalationCorrect": True,
                "documented": True,
            },
            "riskBearers": [
                {"group": "own-unit", "share": 0.50},
                {"group": "civilian", "share": 0.40},
                {"group": "third-party", "share": 0.10},
            ],
            "directlyHarmed": [
                {"groupId": "aircraft_crew", "vulnerability": 0.9, "harmShare": 0.85, "inCustodyOrCare": False},
                {"groupId": "ground_civilians", "vulnerability": 0.3, "harmShare": 0.15, "inCustodyOrCare": False},
            ],
            "alignsWith": ["defend airspace"],
            "expectedCasualties": {
                "populationAtRisk": 5,
                "civilian": {"expected": 1, "min": 0, "max": 3},
            },
            "absoluteProhibitions": {},
        }
    elif proposed_response == "warn":
        action = {
            "id": f"act-{primary.track_id}-warn",
            "name": "Radio warning broadcast only",
            "description": "Broadcast standard radio warning to unidentified aircraft requesting identification and compliance with airspace regulations. No physical action.",
            "lethality": "non-lethal",
            "preconditions": ["Aircraft within radio range", "Language protocol available"],
            "expectedEffects": ["compliance achieved or intent clarified"],
            "actorCost": {
                "institutional": 0.2,
                "professional": 0.3,
                "reputational": 0.1,
                "physical": 0.1,
            },
            "processCompliance": {
                "pidApplied": True,
                "roeFollowed": True,
                "escalationCorrect": False,
                "documented": True,
            },
            "riskBearers": [
                {"group": "own-unit", "share": 0.1},
                {"group": "civilian", "share": 0.05},
            ],
            "directlyHarmed": [],
            "alignsWith": ["defend airspace", "minimise civilian exposure", "positive identification"],
            "expectedCasualties": {
                "populationAtRisk": 0,
                "civilian": {"expected": 0, "min": 0, "max": 0},
            },
            "absoluteProhibitions": {},
        }
    else:
        raise ValueError(f"Unknown proposed_response: {proposed_response}")

    return {"scenario": scenario, "action": action, "tracks": [t.__dict__ for t in tracks]}