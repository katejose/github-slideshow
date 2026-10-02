# Vör Enclave Edition

Deterministic ethical diode for military decision-support, packaged for
accredited, air-gapped, or Palantir Foundry OSDK-compatible environments.

## What this is

A Python port of the [vorethics.com](https://vorethics.com) JS engine that
sits between sensor-fusion context and proposed military action. It outputs
one of three dispositions:

- **allow** — the action is non-contentious on all three ethical frameworks
- **block** — an absolute prohibition or non-compensatory virtue gate fired
- **escalate** — ambiguity or division between the frameworks; human decides

## Architecture

```
Sensor Feed → Adapter → Vor Engine → Disposition (allow / block / escalate)
                  ↓
           Provenance Log (trace + citations + model version)
```

## Directory

| Path | Purpose |
|------|---------|
| `src/engine/` | Core deterministic evaluator: consequentialist, deontological (LOAC/ROE), virtue ethics (CDRILS), disposition gate |
| `src/adapters/` | Feed adapters: turn raw sensor data into Vor `scenario` + `action` inputs |
| `src/validation/` | Golden harness and continuous regression checks |
| `tests/` | Smoke tests and golden regression |
| `docs/` | Evidence library, disposition rules, architectural commitments |

## Quick start

```bash
# Run the golden harness
python tests/test_golden_harness.py

# Run the end-to-end smoke test
python tests/test_end_to_end.py
```

## Key design choices

- **No dependencies** — pure Python 3.10+, no pip install needed in an air gap
- **Evidence library is static** — citations to Geneva Conventions, NATO AJP-3.9, UK JSP 936, etc. are baked in, not inferred
- **Profile pluggable** — `CDRILS` (British Army) ships; other doctrines load by id
- **Deterministic** — identical inputs produce identical dispositions; no randomness in scoring
- **Palantir OSDK ready** — data classes map cleanly to Ontology Objects; transforms are thin wrappers

## For Signal Bureau teams

This repository follows the [ai-native-sdlc](https://github.com/evolutionlabs-dev/ai-native-sdlc)
discipline:
- `VOR_ENCLAVE.md` is the standing brief — read before every session
- Issues are working/episodic memory — file design decisions there
- Every adapter change must pass golden harness + smoke test before merge
- See the Signal Bureau `CLAUDE.md` template for full ritual set