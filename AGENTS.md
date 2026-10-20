# Coding Agent Instructions — IntentProof

1. This is an independent open-source developer library; never import `routine-rescue-ai` or require Alexa accounts.
2. Preserve portable scenario schema v1.0.0, explicit approval gates and outcome semantics.
3. Do not treat ACK as postcondition verification, and never report an unavailable readback as success.
4. Keep fault injection synthetic, deterministic and confined to copied in-memory state.
5. No eval/exec, dynamic code loading, untrusted API invocation or arbitrary file writes from scenario payloads.
6. Add unit tests and README examples for each new feature.
7. Do not claim true rollback or compensating transactions until implemented.
8. Keep package useful beyond RoutineRescue with independent examples.
9. Before submission read `docs/rule.md` and verify license, public repository and contribution evidence.
