# IntentProof — Promise Assurance Upgrade

This version retains the original deterministic `run` and `matrix` commands and adds:

- `audit`: mutation-test modeled step outcomes against declared warranty assertions.
- `diff`: compare two warranty versions for weakened approvals, removed protections or relaxed verification.
- `recovery`: verify changes remained inside an authorized scope and expected postconditions hold.

No paid API or Alexa integration is needed. This is a **simulation and developer test toolkit**.

```powershell
$env:PYTHONPATH = "src"
python -m intentproof audit examples/weak-warranty.json
python -m intentproof audit examples/strong-warranty.json
python -m intentproof diff examples/strong-warranty.json examples/unsafe-revision.json
python -m intentproof run examples/failed-ack-scenario.json
python -m unittest discover -s tests -v
```

`audit` exits 1 when blind spots survive; `diff` exits 1 on critical drift. **100% mutation coverage is not proof of safety:** only modeled actions and protections are analyzed. Novelty is the user-approved promise-to-test workflow, not invention of mutation testing or state verification.
