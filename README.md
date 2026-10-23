# IntentProof — Test the Promise, Not Just the Agent

**A separate, offline open-source developer toolkit** for mutation-auditing action contracts, detecting safety-relevant warranty drift, simulating failure scenarios, verifying recovery scope, and replaying exported RoutineRescue incidents.

> IntentProof is **not** a production security sandbox, full MCP client, Alexa SDK, or a substitute for real hardware testing. No paid model or API is required.

## Install / run

Requires Python **3.11+**. No runtime dependencies.

From the `intentproof` checkout (Windows PowerShell):

```powershell
$env:PYTHONPATH="src"
python -m intentproof audit examples/strong-warranty.json
python -m intentproof audit examples/side-effect-blind-spot.json
python -m intentproof diff examples/strong-warranty.json examples/unsafe-revision.json
python -m intentproof run examples/failed-ack-scenario.json
python -m intentproof matrix examples/failed-ack-scenario.json
```

`audit` intentionally exits `1` if it finds surviving mutants or internally inconsistent action/postconditions. `diff` exits `1` for critical drift, `run` exits `1` for failed test expectations, and `incident` exits `1` when its evidence fails reproduction. Errors/invalid inputs return `2`.

Generate **human-readable Markdown reports**:

```powershell
python -m intentproof audit examples/side-effect-blind-spot.json --format markdown -o audit-report.md
python -m intentproof diff examples/strong-warranty.json examples/unsafe-revision.json --format markdown -o drift-report.md
python -m intentproof incident path/to/exported-incident-v2.json --format markdown -o incident-report.md
```

`report` can convert a saved JSON report too:

```powershell
python -m intentproof report saved-report.json --format markdown -o report.md
```

## Unique workflow we are targeting

Conventional tests often ask whether the implementation passed the contract. IntentProof also asks whether the **contract itself would detect modeled bad behavior**:

1. Generate wrong-value mutations for each action outcome.
2. Mutate other explicitly declared potential **side-effect fields**.
3. Check whether postconditions, invariants, and unchanged-field guards kill these mutations.
4. Show **survived** mutations as missing coverage and detect internally inconsistent baseline assertions.
5. Compare warranty versions for removed approval requirements, forbidden operations, invariants, or unchanged-field guarantees.
6. Replay synthetic runtime failures and compare deterministic execution evidence.
7. Evaluate whether recovery changed **only allowed fields**.

**Coverage is bounded**: declaring too few candidate fields can artificially increase the score. Never claim that 100% means all dangerous actions are caught.

## Developer integration: tool adapters

`intentproof.adapters.ToolRegistry` accepts **explicitly registered Python callables** with a readback callback, an input-schema description, an approval policy and permitted effect fields. A generic `ToolDefinition` describes the metadata, and `definition_from_mcp_descriptor()` can translate the **tool description only** from MCP-shaped metadata.

```powershell
$env:PYTHONPATH="src"
python examples/adapter_demo.py
```

This is a **bring-your-own tool adapter**, not an MCP network transport, and it provides no actual permission boundary for unsafe external code. The host app must authenticate users, sandbox dangerous tools, and enforce approval for consequential operations. Untrusted JSON never triggers dynamic imports or network calls in this package.

## Portable incident interchange

- **Scenario v1.0.0**: deterministic test fixture and warranty, still supported by `run`.
- **Incident v2.0.0**: evidence envelope plus a `replay_scenario` and SHA-256 checksum, used by `incident`.
- Version 2 import verifies required fields, source simulation metadata, checksum, contract consistency, and replayed observed results.
- Checksums detect accidental changes, **not malicious tampering** (they are not signed).
- JSON Schema 2020-12 files are in `schemas/`; runtime validation uses a conservative built-in subset for standard-library portability.

## Test suite

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## Docs and maintenance

- [Engineering v3 spec](docs/ENGINEERING_V3.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

IntentProof can be used independently of RoutineRescue with local examples and embedded test scenarios. Both codebases are MIT licensed.

### Deeper inventory-based mutation coverage

By default `audit` examines explicitly listed step outcomes, invariants, and `side_effect_candidates`. To test **every field in an available simulated environment inventory**, add `--inventory`:

```powershell
python -m intentproof audit examples/strong-warranty.json --inventory examples/virtual-home-inventory.json --format markdown
python -m intentproof audit examples/fully-protected-warranty.json --inventory examples/virtual-home-inventory.json --format markdown
```

The first should identify an unprotected `desk_light.power` field; the second includes an unchanged-field guarantee to catch it. The inventory is an *explicit model*, not magical discovery of real physical state.
