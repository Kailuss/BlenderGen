"""Adaptación de lectura del grafo nominal existente; nunca fabrica contactos."""
from . import graph,schema,materials


def from_nominal(nominal):
    'IA: Traduce pertenencia, apoyos declarados y accesos; conserva IDs; no convierte daño/acceso en apoyo ni asigna resistencia no medida.'
    elements=[schema.element(n['id'],n['type'],**{k:v for k,v in n.items() if k not in ('id','type')}) for n in nominal['nodes']]
    relations=[];annotations=[]
    for a,b,kind in nominal['relations']:
        if kind=='contains':source,target,typed=b,a,'HOSTED_BY'
        elif kind in ('supports','nominal_support'):source,target,typed=b,a,'SUPPORTED_BY'
        elif kind=='access':source,target,typed=a,b,'CONNECTED_TO'
        else:annotations.append({'source':a,'target':b,'kind':kind});continue
        relations.append({'id':typed+':'+source+'>'+target,'source':source,'target':target,'kind':typed,'state':'INTACTO','evidence':'declared_nominal'})
    model={'schema':schema.VERSION,'units':dict(schema.UNITS),'elements':elements,'relations':relations,'annotations':annotations,'scope':'read_only_nominal; no measured contact or structural strength'}
    schema.synchronise_supports(model)
    model['materials_signature']=materials.signature()
    return model


def report(model):
    'IA: Resume cobertura real del adaptador y conflictos sin declarar estabilidad de elementos con apoyos desconocidos.'
    supported={r['source'] for r in model['relations'] if r['kind']=='SUPPORTED_BY'}
    structural={'WALL','FLOOR','ROOF','RAFTERS','BATTENS','TILES','TERRACE_BEAMS','DECK','PARAPET','MERLONS','STAIR'}
    return {'issues':graph.validate(model)+schema.validate(model),'unresolved_supports':sorted(e['id'] for e in model['elements'] if e['kind'] in structural and e['id'] not in supported),'unresolved_policies':sorted(e['id'] for e in model['elements'] if e['id'] in supported and 'minimum_supports' not in e),'regeneration_order':graph.order(model)[0],'geometry_changed':False}
