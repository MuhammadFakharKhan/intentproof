"""Human-readable, escaped Markdown summaries from structured IntentProof reports."""
import json

def esc(x):
    return str(x).replace('|','\\|').replace('\n',' ').replace('\r',' ').replace('`',"'")

def markdown(report, label='IntentProof Analysis'):
    lines=[f'# {esc(label)}','','Generated from a deterministic local test; not a physical safety certification.','']
    if 'coverage_percent' in report:
        lines+=['## Promise mutation coverage',f"- Killed: **{report['killed']} / {report['mutants']}**",f"- Survived: **{report['survived']}**",f"- Coverage: **{report['coverage_percent']}%**",'','| Kind | Field | Mutation | Result |','|---|---|---|---|']
        lines += [f"| {esc(f.get('kind','outcome'))} | {esc(f['target'])}.{esc(f['field'])} | {esc(json.dumps(f['mutated']))} | **{esc(f['status'])}** |" for f in report['findings']]
    elif 'verdict' in report:
        lines+=['## Contract drift',f"Verdict: **{esc(report['verdict'])}**",'','| Severity | Path | Finding |','|---|---|---|']
        lines += [f"| {esc(f['severity'])} | {esc(f['path'])} | {esc(f['message'])} |" for f in report['findings']]
    elif 'reproducible' in report:
        lines+=['## Incident reproduction',f"- Reproducible: **{report['reproducible']}**",f"- Evidence differences: {esc(report['evidence_differences'])}",f"- Outcome: {esc(report['workflow']['outcome'])}"]
    elif 'scenario_id' in report:
        lines+=['## Execution',f"- Scenario: {esc(report['scenario_id'])}",f"- Outcome: **{esc(report['outcome'])}**",f"- Violations: {len(report['violations'])}",f"- Unexpected side effects: {len(report.get('side_effects',[]))}"]
    elif 'unexpected_changes' in report:
        lines+=['## Recovery verification',f"- Verified: **{report['verified']}**",f"- Unexpected changes: {len(report['unexpected_changes'])}"]
    else:lines+=['## Structured result','```json',json.dumps(report,indent=2),'```']
    lines+=['','## Limitations','The result covers only declared and simulated conditions; unmodeled states and dishonest sensors are outside scope.','']
    return '\n'.join(lines)
