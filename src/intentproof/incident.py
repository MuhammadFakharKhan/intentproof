"""Strict v2 incident importer and compatibility boundary to v1 test scenarios."""
import hashlib
import json
from .engine import run_scenario

VERSION='2.0.0'
REQUIRED={'schema_version','incident_id','created_at','source','intent','contract','execution','failure','recovery','replay_scenario','replay_sha256','limitations'}

def checksum(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()

def validate_incident(data):
    if not isinstance(data,dict) or set(data)!=REQUIRED:raise ValueError('Incident envelope missing or contains unexpected fields')
    if data['schema_version']!=VERSION:raise ValueError('Unsupported incident schema version')
    if not isinstance(data['source'],dict) or data['source'].get('simulation') is not True:raise ValueError('Importer only supports explicitly simulated incidents')
    if not isinstance(data['replay_sha256'],str) or data['replay_sha256']!=checksum(data['replay_scenario']):raise ValueError('Replay scenario checksum mismatch')
    # Compare evidence after replay; mismatched evidence is rejected rather than silently trusted.
    expected=data['execution']
    if not isinstance(expected,dict) or not {'initial_state','final_state','events','outcome'}<=set(expected):raise ValueError('Incident execution is missing required evidence')
    scenario=data['replay_scenario']
    warranty=scenario.get('warranty',{})
    if data['source'].get('routine_id')!=warranty.get('routine_id') or data['source'].get('warranty_version')!=warranty.get('warranty_version','1.0.0'):
        raise ValueError('Incident metadata is inconsistent with the replay warranty')
    contract=data['contract']
    for key in ('postconditions','invariants','unchanged_fields'):
        if contract.get(key)!=warranty.get(key,[]):raise ValueError('Incident contract evidence differs from replay warranty')
    return data

def replay_incident(data):
    data=validate_incident(data)
    replay=run_scenario(data['replay_scenario'])
    keys=('initial_state','final_state','events','outcome')
    differs=[k for k in keys if replay[k]!=data['execution'][k]]
    if replay['violations']!=data['failure']['violations']:differs.append('violations')
    if replay.get('side_effects',[])!=data['failure'].get('side_effects',[]):differs.append('side_effects')
    return {'incident_id':data['incident_id'],'reproducible':not differs,'evidence_differences':differs,
            'workflow':{'outcome':replay['outcome']},
            'test':{'assertion':'PASS' if not differs else 'FAIL',
                    'reproduced_expected_failure':not differs and replay['outcome'] in ('DEGRADED','UNVERIFIED')},
            'replay':replay}
