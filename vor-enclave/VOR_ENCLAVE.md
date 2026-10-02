# VOR_ENCLAVE.md — Standing Brief for Vör Enclave Edition

Read this first on every cold-start session. This file is the universal
attachment point; task-specific guidance lives in `docs/` or in issues.

## What you may touch

- `src/adapters/` — add or modify feed adapters (thin schema-mapping layer)
- `tests/` — extend golden harness with new canonical cases
- `docs/` — add evidence-library entries or disposition-rule rationales

## What you must not touch without a human decision

- `src/engine/evaluation_engine.py` — the deterministic scoring logic
- `src/engine/virtue_profiles.py` — thresholds, gate modes, or virtue definitions
- `src/engine/evidence_library.py` — source citations and architectural commitments

These files are the **certified surface**. A change here is a ruleset version
bump, which triggers re-accreditation. Open an issue, label `needs-human-decision`,
and stop.

## How to add a new sensor adapter

1. Copy `src/adapters/mock_adsb_sensor.py` as your template
2. Replace `generate_tracks()` with your real parser or OSDK Object read
3. Implement `map_<feed>_to_vor_input()` producing a dict with keys:
   - `scenario` — must contain `context.threatLikelihood`, `context.civilianPresence`, `context.uncertaintyLevel`, `context.timePressure`, `context.commandIntent`, `context.commandIntentLawful`, `context.commandIntentObjectives`
   - `action` — must contain `name`, `lethality`, `preconditions`, `actorCost`, `processCompliance`, `riskBearers`, `directlyHarmed`, `alignsWith`
4. Run `python tests/test_end_to_end.py` and `python tests/test_golden_harness.py`
5. Only when both pass, commit and push

## Gate before you build

- Search closed issues for the sensor type before designing
- Check `src/engine/virtue_profiles.py` for the exact `inputs` each virtue expects
- If a required input is missing from your feed, the virtue scores `na` — this
  is by design and may lower the composite into `escalate` or `block`

## Verification discipline

Every commit that changes `src/` must run:

```bash
python tests/test_golden_harness.py
python tests/test_end_to_end.py
```

Golden harness failures mean the engine has drifted from certified behaviour.
That is a deployment blocker, not a test bug.

## Provenance

Every `run_evaluation()` call returns a `VorResult` with:
- `model_version` — pinned engine version
- `virtue_profile_version` — profile + version stamp
- `disposition_rule_version` — rule id + version
- `trace` — ordered gate log
- `citations` — every LOAC/ROE rule cites its evidence-library source

This is the audit payload for accreditation. Do not strip or truncate it.

## Palantir OSDK note

For Foundry deployment, wrap the adapter in a `@transform` that:
1. Reads the sensor Object set
2. Calls `map_..._to_vor_input()`
3. Passes the dicts directly to `run_evaluation()`
4. Writes the `VorResult` fields back as an output Object

No PySpark scoring logic inside the transform — the engine is the
authoritative evaluator; the transform is plumbing only.

## Closing note

Keep this file lean. If it grows past what a sharp new teammate absorbs in
one sitting, something belongs in an attachment point or an issue, not here.