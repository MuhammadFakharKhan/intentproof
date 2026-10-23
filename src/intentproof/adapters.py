"""Framework-neutral, opt-in agent-tool adapter and readback contract.

No dynamic Python imports, network endpoints, or real external tools bundled.
Developers explicitly register callables. Runtime checks and human approval
are NOT a production sandbox; applications must enforce their own auth.
"""
from dataclasses import dataclass
from typing import Callable, Any
import copy
import json

@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict
    requires_approval: bool = False
    expected_change_fields: tuple[tuple[str,str],...] = ()

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, definition: ToolDefinition, invoke: Callable[[dict],Any], observe: Callable[[],dict]):
        if not isinstance(definition,ToolDefinition) or not definition.name or not isinstance(definition.input_schema,dict):
            raise ValueError('ToolDefinition requires a name and JSON input schema')
        if definition.name in self._tools:raise ValueError('Duplicate tool name')
        if not callable(invoke) or not callable(observe):raise ValueError('Tool requires invoke and independent observe callables')
        self._tools[definition.name]=(definition,invoke,observe)

    def manifest(self):
        return [{'name':d.name,'description':d.description,'inputSchema':copy.deepcopy(d.input_schema),
                 'approval_required':d.requires_approval,
                 'allowed_effects':[{'target':x,'field':y} for x,y in d.expected_change_fields]}
                for d,_,_ in self._tools.values()]

    def execute(self,name,args,*,approved=False,dry_run=True):
        if name not in self._tools:raise ValueError('Unregistered tool')
        d,invoke,observe=self._tools[name]
        if not isinstance(args,dict):raise ValueError('Tool arguments must be a JSON object')
        # Strict small subset of JSON Schema for demo: properties, required, additionalProperties and primitive types.
        schema=d.input_schema
        missing=set(schema.get('required',[]))-set(args)
        extra=set(args)-set(schema.get('properties',{}))
        if missing or (schema.get('additionalProperties') is False and extra):
            raise ValueError('Missing or unrecognized tool argument')
        for key,val in args.items():
            kind=schema.get('properties',{}).get(key,{}).get('type')
            checks={'string':lambda v:isinstance(v,str),'boolean':lambda v:type(v) is bool,
                    'integer':lambda v:type(v) is int,'number':lambda v:type(v) in (int,float)}
            if kind in checks and not checks[kind](val):raise ValueError(f'Invalid argument type: {key}')
        before=copy.deepcopy(observe())
        if not isinstance(before,dict):raise ValueError('Observation must be a state dictionary')
        if dry_run:
            return {'tool':name,'status':'DRY_RUN','before':before,'after':before,'approved':bool(approved)}
        if d.requires_approval and approved is not True:
            return {'tool':name,'status':'BLOCKED_APPROVAL','before':before,'after':before,'approved':False}
        ack=invoke(copy.deepcopy(args))
        after=copy.deepcopy(observe())
        if not isinstance(after,dict):raise ValueError('Observation must be a state dictionary')
        changes=[]
        for target in sorted(set(before)|set(after)):
            old=before.get(target,{}) or {}; new=after.get(target,{}) or {}
            for field in sorted(set(old)|set(new)):
                if old.get(field)!=new.get(field):
                    changes.append({'target':target,'field':field,'before':old.get(field),'after':new.get(field)})
        unexpected=[c for c in changes if (c['target'],c['field']) not in d.expected_change_fields]
        return {'tool':name,'status':'OBSERVED_OUT_OF_SCOPE' if unexpected else 'OBSERVED',
                'acknowledgement':ack,'before':before,'after':after,
                'changes':changes,'unexpected_changes':unexpected,
                'note':'Local observation only; the caller is responsible for independent real-device verification.'}

    def export_manifest(self):
        return json.dumps(self.manifest(),indent=2)

def definition_from_mcp_descriptor(descriptor, *, requires_approval=True, expected_change_fields=()):
    """Map the published MCP *tool metadata shape* to a registry definition.

    This is a descriptor bridge only, NOT an MCP client, transport, or permission
    system. The host supplies invocation and readback functions explicitly.
    """
    if not isinstance(descriptor,dict) or set(descriptor)-{'name','title','description','inputSchema','outputSchema','annotations','_meta'}:
        raise ValueError('Unsupported MCP descriptor fields')
    name=descriptor.get('name');schema=descriptor.get('inputSchema')
    if not isinstance(name,str) or not name or not isinstance(schema,dict):
        raise ValueError('MCP descriptor requires name and inputSchema')
    if schema.get('type')!='object':raise ValueError('MCP tool inputSchema must describe an object')
    return ToolDefinition(name,descriptor.get('description',name),copy.deepcopy(schema),
                          requires_approval=requires_approval,
                          expected_change_fields=tuple(expected_change_fields))
