"""CLI: intentproof run FILE [--output FILE] [--strict]."""
import argparse
import json
import sys
from pathlib import Path
from .engine import run_scenario
from .matrix import run_matrix


def main(argv=None):
    parser = argparse.ArgumentParser(prog="intentproof", description="Run a deterministic intent/warranty regression scenario")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Replay a scenario and check expected outcomes")
    run.add_argument("scenario", help="JSON scenario path")
    run.add_argument("--output", "-o", help="Optional JSON report output path")
    run.add_argument("--strict", action="store_true", help="Exit non-zero if outcome is not VERIFIED/RECOVERED (as well as assertion failures)")
    matrix = subparsers.add_parser("matrix", help="Explore healthy and synthetic failure combinations")
    matrix.add_argument("scenario", help="JSON scenario path")
    matrix.add_argument("--output", "-o", help="Optional JSON matrix report path")
    args = parser.parse_args(argv)
    try:
        scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
        report = run_matrix(scenario) if args.command == "matrix" else run_scenario(scenario)
        rendered = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print(f"intentproof error: {exc}", file=sys.stderr)
        return 2
    print(rendered)
    if args.command == "matrix":
        return 0
    if report["expected_matched"] is False:
        return 1
    if args.strict and report["outcome"] not in ("VERIFIED", "RECOVERED"):
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
