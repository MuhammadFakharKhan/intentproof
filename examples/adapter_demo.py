"""Offline demonstration of third-party callable tool integration; no network."""
from intentproof.adapters import ToolRegistry, ToolDefinition
state={'desk_light':{'power':'off'},'front_door':{'locked':True}}
registry=ToolRegistry()
registry.register(ToolDefinition(
    'desk_light_on','Turn a simulated desk light on',
    {'type':'object','properties':{},'required':[],'additionalProperties':False},
    expected_change_fields=(('desk_light','power'),)),
    lambda args: state['desk_light'].update(power='on') or {'ok':True},
    lambda:state)
print('TOOLS:',registry.export_manifest())
print('PREVIEW:',registry.execute('desk_light_on',{},dry_run=True))
print('OBSERVED:',registry.execute('desk_light_on',{},dry_run=False))
