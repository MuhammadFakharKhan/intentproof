# IntentProof — independent open-source outcome and recovery test kit

**Status:** runnable Python standard-library prototype (not certified or integrated with Alexa+). The package tests **simulated workflows** defined in portable JSON.

## The developer problem

Ordinary mocks and tool-return checks can report that calls succeeded even while final state is wrong, unknowable, or permission-prohibited. Those issues can be expensive to reproduce manually, especially when a failure depends on retries or a changing permission state.

## Implemented features

- **Portable v1 JSON outcome contracts**: ordered steps, postconditions, forbidden operations, approvals, retry restrictions.
- **Deterministic local execution**: no paid tokens, external API calls, IoT hardware, or cloud account.
- **Synthetic fault injection**: false acknowledgements, unknown readbacks, revoked permissions, timeouts after commit, and synthetic post-write reversions.
- **Outcome verification**: `VERIFIED`, `RECOVERED`, `DEGRADED`, `UNVERIFIED`, with step traces and mismatched postconditions.
- **Regression assertions**: compare an exported incident's expected outcome and violations with the replayed result.
- **Failure matrix**: generate/run a baseline plus one fault type per workflow step, producing JSON results.
- **Fail-closed v1 contract checks**: rejects malformed/unknown fields and bounds steps, postconditions and faults before execution.
- **Standalone Python library** (`run_scenario`) and CLI, with unit tests.

## Run with zero dependencies

Python 3.10+:

```bash
cd intentproof
PYTHONPATH=src python -m intentproof run examples/failed-ack-scenario.json
PYTHONPATH=src python -m intentproof matrix examples/failed-ack-scenario.json
PYTHONPATH=src python -m intentproof run examples/maintenance-window-scenario.json
python -m unittest discover -s tests -v
```

On Windows PowerShell, set `$env:PYTHONPATH='src'` and then run the same `python -m intentproof ...` commands.

Optional local editable install (uses pip/setuptools; internet may be needed if build tooling is missing):

```bash
python -m pip install -e .
intentproof run examples/failed-ack-scenario.json --output report.json
intentproof matrix examples/failed-ack-scenario.json --output matrix.json
```

`intentproof run ...` exits 0 when the recorded `expected` outcome matches the observed replay, even if the scenario intentionally demonstrates a failure. Add `--strict` to exit nonzero when the resulting simulated workflow is not `VERIFIED` or `RECOVERED`. A test that expects a failure is a passing regression test when the failure is correctly reproduced.

`examples/maintenance-window-scenario.json` is a generic CI maintenance-window workflow, written independently of RoutineRescue. It demonstrates that the schema is a reusable local workflow contract rather than a smart-home-only fixture.

## Reproduce an issue exported by RoutineRescue

1. Run the separate `routine-rescue-ai` web demo.
2. Trigger a synthetic problem and export `exported-scenario.json`.
3. Run `PYTHONPATH=src python -m intentproof run /path/to/exported-scenario.json` in **this** repository.
4. Compare `expected_matched`, violation list and step trace. Run `matrix` to explore additional simulated faults.

## Why this is an additional project

IntentProof works on its own against `examples/failed-ack-scenario.json`, has a reusable `src/intentproof` package, a CLI and unit tests, and depends neither on RoutineRescue nor Amazon. Its JSON schema can be adopted by other agent developers. The main app is a consumer and export source, not the entire Open Source mini-challenge contribution.

## Known limitations

- Purely deterministic and uses **synthetic state**; no real Alexa+ tests, real hardware verification, live agent model calls, production-ready sandboxing or regulatory compliance.
- Only a constrained set of virtual step operations and at most one policy-approved retry are implemented.
- `partial_rollback` is a synthetic post-write reversion used to test readback and recovery handling. It is **not** a genuine compensating transaction or rollback guarantee.
- `matrix` explores single-fault synthetic cases, not exhaustive combinatorial coverage.
- The schema stores a declared `seed` for forward compatibility; this release is deterministic without randomness.

MIT licensed. See `docs/architecture.md`, `docs/efd.md`, `docs/implementation-plan.md`, and `docs/rule.md` for exact boundaries and submission requirements.
