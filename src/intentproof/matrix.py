"""Generate and run an offline, deterministic failure matrix for one warranty."""
import copy
from .engine import run_scenario


def run_matrix(source):
    """Create a synthetic case per step/fault, without any network/tool calls."""
    base = copy.deepcopy(source)
    base.pop("expected", None)
    base["faults"] = []
    rows = []
    good = run_scenario(base)
    rows.append({"case": "baseline", "fault": "none", "step": None, "outcome": good["outcome"], "violations": good["violations"]})
    for step in base["warranty"]["steps"]:
        for kind in ("ack_without_effect", "readback_unavailable", "permission_revoked", "timeout_after_commit", "partial_rollback"):
            case = copy.deepcopy(base)
            case["faults"] = [{"at_step_id": step["step_id"], "kind": kind, "occurrences": 2 if kind in ("ack_without_effect", "partial_rollback") else 1}]
            result = run_scenario(case)
            rows.append({"case": f"{step['step_id']}:{kind}", "fault": kind, "step": step["step_id"],
                         "outcome": result["outcome"], "violations": result["violations"]})
    return {"scenario_id": source.get("scenario_id", "unnamed"), "cases": len(rows), "results": rows}
