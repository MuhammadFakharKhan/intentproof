"""Independent, deterministic, stdlib-only routine warranty test engine.

Only local simulated state is handled; no actual IoT/Alexa integrations.
"""
import copy
from collections import defaultdict

SUPPORTED_OPERATIONS = {"LIGHT_ON", "LIGHT_OFF", "LOCK", "UNLOCK", "SET_ALARM"}
SUPPORTED_FAULTS = {
    "ack_without_effect", "readback_unavailable", "permission_revoked",
    "timeout_after_commit", "partial_rollback",
}
SUPPORTED_OUTCOMES = {"VERIFIED", "DEGRADED", "UNVERIFIED", "RECOVERED", "CANCELLED"}

# Generous limits keep the local runner predictable without changing the v1
# document format. They prevent malformed fixtures from creating huge reports.
MAX_STEPS = 1_000
MAX_POSTCONDITIONS = 1_000
MAX_FAULTS = 1_000


def _fail(message):
    raise ValueError(message)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(value, name, required, optional=()):
    if not isinstance(value, dict):
        _fail(f"{name} must be an object")
    required = set(required)
    allowed = required | set(optional)
    missing = required - set(value)
    unknown = set(value) - allowed
    if missing:
        _fail(f"{name} missing {', '.join(sorted(missing))}")
    if unknown:
        _fail(f"{name} has unsupported field {sorted(unknown)[0]}")


def _require_string(value, name):
    if not isinstance(value, str) or not value:
        _fail(f"{name} must be a non-empty string")


def _require_operation(value, name):
    if not isinstance(value, str) or value not in SUPPORTED_OPERATIONS:
        _fail(f"{name} must be a supported operation")


def _require_operation_list(value, name):
    if not isinstance(value, list):
        _fail(f"{name} must be an array")
    for index, operation in enumerate(value):
        _require_operation(operation, f"{name}[{index}]")
    if len(value) != len(set(value)):
        _fail(f"{name} must not contain duplicates")


def _validate(scenario):
    """Validate the supported, declarative v1 input subset before execution."""
    _require_object(
        scenario, "Scenario",
        {"schema_version", "scenario_id", "description", "warranty", "initial_state", "approvals", "seed", "faults"},
        {"expected"},
    )
    if scenario["schema_version"] != "1.0.0":
        _fail("Scenario schema_version must be 1.0.0")
    _require_string(scenario["scenario_id"], "scenario_id")
    if not isinstance(scenario["description"], str):
        _fail("description must be a string")
    if not _is_int(scenario["seed"]):
        _fail("seed must be an integer")
    if not isinstance(scenario["initial_state"], dict):
        _fail("initial_state must be an object")
    for target, fields in scenario["initial_state"].items():
        if not isinstance(target, str):
            _fail("initial_state target must be a string")
        if not isinstance(fields, dict):
            _fail("each initial_state target must contain an object")
    _require_operation_list(scenario["approvals"], "approvals")

    warranty = scenario["warranty"]
    _require_object(
        warranty, "warranty",
        {"schema_version", "warranty_id", "routine_id", "name", "aliases", "steps", "postconditions", "forbidden_operations", "recovery", "verification"},
    )
    if warranty["schema_version"] != "1.0.0":
        _fail("Warranty schema_version must be 1.0.0")
    for key in ("warranty_id", "routine_id", "name"):
        _require_string(warranty[key], f"warranty.{key}")
    aliases = warranty["aliases"]
    if not isinstance(aliases, list) or not aliases:
        _fail("warranty.aliases must be a non-empty array")
    for index, alias in enumerate(aliases):
        _require_string(alias, f"warranty.aliases[{index}]")
    if len(aliases) != len(set(aliases)):
        _fail("warranty.aliases must not contain duplicates")

    steps = warranty["steps"]
    if not isinstance(steps, list) or not steps:
        _fail("warranty.steps must be a non-empty array")
    if len(steps) > MAX_STEPS:
        _fail(f"warranty.steps exceeds the {MAX_STEPS} step limit")
    for index, step in enumerate(steps):
        _require_object(step, f"warranty.steps[{index}]", {"step_id", "operation", "target", "field", "value", "risk", "requires_approval"})
        for key in ("step_id", "target", "field"):
            _require_string(step[key], f"warranty.steps[{index}].{key}")
        _require_operation(step["operation"], f"warranty.steps[{index}].operation")
        if not isinstance(step["risk"], str) or step["risk"] not in {"low", "sensitive"}:
            _fail(f"warranty.steps[{index}].risk must be low or sensitive")
        if not isinstance(step["requires_approval"], bool):
            _fail(f"warranty.steps[{index}].requires_approval must be boolean")
    ids = [step["step_id"] for step in steps]
    if len(ids) != len(set(ids)):
        _fail("Duplicate step IDs")

    postconditions = warranty["postconditions"]
    if not isinstance(postconditions, list) or not postconditions:
        _fail("warranty.postconditions must be a non-empty array")
    if len(postconditions) > MAX_POSTCONDITIONS:
        _fail(f"warranty.postconditions exceeds the {MAX_POSTCONDITIONS} postcondition limit")
    for index, postcondition in enumerate(postconditions):
        _require_object(postcondition, f"warranty.postconditions[{index}]", {"target", "field", "equals"})
        _require_string(postcondition["target"], f"warranty.postconditions[{index}].target")
        _require_string(postcondition["field"], f"warranty.postconditions[{index}].field")

    _require_operation_list(warranty["forbidden_operations"], "warranty.forbidden_operations")
    recovery = warranty["recovery"]
    _require_object(recovery, "warranty.recovery", {"auto_retry_operations", "max_auto_retries", "sensitive_retry_requires_approval"})
    _require_operation_list(recovery["auto_retry_operations"], "warranty.recovery.auto_retry_operations")
    if not _is_int(recovery["max_auto_retries"]) or recovery["max_auto_retries"] not in (0, 1):
        _fail("warranty.recovery.max_auto_retries must be 0 or 1")
    if recovery["sensitive_retry_requires_approval"] is not True:
        _fail("warranty.recovery.sensitive_retry_requires_approval must be true")
    verification = warranty["verification"]
    _require_object(verification, "warranty.verification", {"require_readback", "unknown_is_success"})
    if verification["require_readback"] is not True or verification["unknown_is_success"] is not False:
        _fail("warranty verification must require readback and treat unknown as non-success")

    faults = scenario["faults"]
    if not isinstance(faults, list):
        _fail("faults must be an array")
    if len(faults) > MAX_FAULTS:
        _fail(f"faults exceeds the {MAX_FAULTS} fault limit")
    for index, fault in enumerate(faults):
        _require_object(fault, f"faults[{index}]", {"at_step_id", "kind", "occurrences"})
        _require_string(fault["at_step_id"], f"faults[{index}].at_step_id")
        if not isinstance(fault["kind"], str) or fault["kind"] not in SUPPORTED_FAULTS:
            _fail("Unrecognized fault " + str(fault["kind"]))
        if fault["at_step_id"] not in ids:
            _fail("Fault references missing step " + fault["at_step_id"])
        if not _is_int(fault["occurrences"]) or fault["occurrences"] < 1:
            _fail("Fault occurrences must be a positive integer")

    if "expected" in scenario:
        expectation = scenario["expected"]
        _require_object(expectation, "expected", {"workflow_outcome", "violations"})
        if not isinstance(expectation["workflow_outcome"], str) or expectation["workflow_outcome"] not in SUPPORTED_OUTCOMES:
            _fail("expected.workflow_outcome is not supported")
        if not isinstance(expectation["violations"], list):
            _fail("expected.violations must be an array")
        for index, violation in enumerate(expectation["violations"]):
            _require_object(violation, f"expected.violations[{index}]", {"target", "field", "expected", "actual"})
            _require_string(violation["target"], f"expected.violations[{index}].target")
            _require_string(violation["field"], f"expected.violations[{index}].field")
    return warranty


def run_scenario(scenario):
    """Run an isolated scenario; return a reproducible, serializable report.

    ACK is never sufficient evidence of success; separate readback determines
    VERIFIED / DEGRADED / UNVERIFIED. Supports at most one policy-approved retry.
    """
    warranty = _validate(scenario)
    state = copy.deepcopy(scenario.get("initial_state", {}))
    approvals = set(scenario.get("approvals", []))
    remaining_faults = defaultdict(int)
    for f in scenario.get("faults", []):
        remaining_faults[(f["at_step_id"], f["kind"])] += f["occurrences"]
    initial = copy.deepcopy(state)
    events = []
    unknown_fields = set()
    retries = 0
    forbidden = set(warranty["forbidden_operations"])
    recovery = warranty["recovery"]
    auto_retry = set(recovery.get("auto_retry_operations", []))

    def take_fault(step_id):
        for kind in ("permission_revoked", "ack_without_effect", "timeout_after_commit", "readback_unavailable", "partial_rollback"):
            key = (step_id, kind)
            if remaining_faults[key] > 0:
                remaining_faults[key] -= 1
                return kind
        return None

    def perform(step, retry=False):
        step_id = step["step_id"]
        operation = step["operation"]
        target, field, value = step["target"], step["field"], step["value"]
        entry = {"step_id": step_id, "operation": operation, "retry": retry, "target": target}
        if operation in forbidden:
            entry.update(ack="BLOCKED", readback="UNVERIFIED", reason="forbidden_operation")
            events.append(entry)
            return "BLOCKED"
        if step.get("requires_approval") and operation not in approvals:
            entry.update(ack="BLOCKED", readback="UNVERIFIED", reason="approval_required")
            events.append(entry)
            return "BLOCKED"
        fault = take_fault(step_id)
        if fault == "permission_revoked":
            entry.update(ack="BLOCKED", readback="UNVERIFIED", reason="permission_revoked")
            events.append(entry)
            return "BLOCKED"
        target_existed = target in state
        field_existed = field in state.get(target, {})
        previous_value = copy.deepcopy(state.get(target, {}).get(field))
        if fault not in ("ack_without_effect",):
            state.setdefault(target, {})[field] = value
        if fault == "partial_rollback":
            if field_existed:
                state[target][field] = previous_value
            else:
                del state[target][field]
                if not target_existed and not state[target]:
                    del state[target]
        entry["ack"] = "TIMEOUT" if fault == "timeout_after_commit" else "SUCCESS"
        if fault == "readback_unavailable":
            unknown_fields.add((target, field))
            entry["readback"] = "UNKNOWN"
        else:
            unknown_fields.discard((target, field))
            observed = state.get(target, {}).get(field)
            entry["readback"] = "VERIFIED" if observed == value else "MISMATCH"
        entry["fault"] = fault
        events.append(entry)
        return entry["readback"]

    for step in warranty["steps"]:
        outcome = perform(step)
        if (outcome == "MISMATCH" and step["operation"] in auto_retry and
                not step.get("requires_approval") and retries < min(1, int(recovery.get("max_auto_retries", 0)))):
            retries += 1
            perform(step, retry=True)

    violations = []
    unknown = False
    for p in warranty["postconditions"]:
        target, field, expected = p["target"], p["field"], p["equals"]
        if (target, field) in unknown_fields:
            unknown = True
            violations.append({"target": target, "field": field, "expected": expected, "actual": "UNKNOWN"})
        else:
            observed = state.get(target, {}).get(field)
            if observed != expected:
                violations.append({"target": target, "field": field, "expected": expected, "actual": observed})
    blocked = any(e["ack"] == "BLOCKED" for e in events)
    if any(v["actual"] != "UNKNOWN" for v in violations) or blocked:
        outcome = "DEGRADED"
    elif unknown:
        outcome = "UNVERIFIED"
    elif retries:
        outcome = "RECOVERED"
    else:
        outcome = "VERIFIED"

    expectation = scenario.get("expected")
    check = None
    if expectation is not None:
        check = (outcome == expectation["workflow_outcome"] and violations == expectation["violations"])
    return {"scenario_id": scenario.get("scenario_id", "unnamed"),
            "outcome": outcome, "expected_matched": check, "retries": retries,
            "initial_state": initial, "final_state": state,
            "violations": violations, "events": events}
