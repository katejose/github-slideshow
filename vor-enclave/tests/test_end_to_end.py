"""End-to-end Smoke Test: Sensor Feed → Adapter → Engine → Disposition

Verifies that the mock ADS-B adapter produces valid Vor inputs and that the
engine runs without error, producing an auditable result with trace.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapters.mock_adsb_sensor import generate_tracks, map_tracks_to_vor_input
from engine.evaluation_engine import run_evaluation
from engine.virtue_profiles import get_virtues_by_profile_id


def smoke_interception():
    tracks = generate_tracks(seed=42, count=3)
    vor_input = map_tracks_to_vor_input(tracks, proposed_response="interception")
    if vor_input is None:
        print("FAIL  adapter returned None")
        return False
    scenario = vor_input["scenario"]
    action = vor_input["action"]
    result = run_evaluation(scenario, action, get_virtues_by_profile_id("CDRILS_V1_1"), "CDRILS_V1_1")

    print(f"Smoke test: interception")
    print(f"  Primary track: {tracks[2].callsign} ({tracks[2].classification})")
    print(f"  Threat: {scenario['context']['threatLikelihood']}")
    print(f"  Disposition: {result.final_disposition}")
    print(f"  Rationale: {result.rationale[:120]}...")
    print(f"  Trace phases: {', '.join(t.phase for t in result.trace)}")
    print(f"  Citations: {len(result.citations)}")

    ok = result.final_disposition in ("allow", "escalate", "block")
    ok = ok and len(result.trace) >= 5
    ok = ok and len(result.citations) > 0
    ok = ok and result.virtue_profile_id == "CDRILS_V1_1"
    return ok


def smoke_engage():
    tracks = generate_tracks(seed=99, count=6)
    # With seed 99 the hostile track (RED901 at T004) is still max threat
    vor_input = map_tracks_to_vor_input(tracks, proposed_response="engage")
    scenario = vor_input["scenario"]
    action = vor_input["action"]
    result = run_evaluation(scenario, action, get_virtues_by_profile_id("CDRILS_V1_1"), "CDRILS_V1_1")

    print(f"\nSmoke test: engage")
    print(f"  Primary track: {tracks[3].callsign} ({tracks[3].classification})")
    print(f"  Disposition: {result.final_disposition}")
    print(f"  Rationale: {result.rationale[:120]}...")

    return result.final_disposition in ("allow", "escalate", "block")


def smoke_warn():
    tracks = generate_tracks(seed=7, count=2)
    vor_input = map_tracks_to_vor_input(tracks, proposed_response="warn")
    result = run_evaluation(vor_input["scenario"], vor_input["action"],
                            get_virtues_by_profile_id("CDRILS_V1_1"), "CDRILS_V1_1")

    print(f"\nSmoke test: warn")
    print(f"  Primary track: {tracks[0].callsign} ({tracks[0].classification})")
    print(f"  Disposition: {result.final_disposition}")

    return result.final_disposition in ("allow", "escalate", "block")


if __name__ == "__main__":
    ok = smoke_interception() and smoke_engage() and smoke_warn()
    print(f"\n{'PASS' if ok else 'FAIL'} — all smoke tests complete")
    sys.exit(0 if ok else 1)