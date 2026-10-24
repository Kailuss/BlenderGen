"""Adaptación de lectura del grafo nominal existente; nunca fabrica contactos."""
from . import graph,schema,materials,units


def measured_element(identifier,kind,material,volume_model_mm3,area_model_mm2,definition):
    'IA: Frontera única del adaptador para medidas de malla en modelo; requiere model_scale explícito y entrega magnitudes de mundo.'
    scale=definition.get('model_scale')
    result=schema.element(identifier,kind,material,units.to_world(volume_model_mm3,3,scale))
    result['exposed_area_mm2']=units.to_world(area_model_mm2,2,scale)
    return result


def relation(source,target,kind,contacts=None,state='INTACTO'):
    'IA: Relación por pareja y tipo, con lista de contactos; None representa medida ausente.'
    return {'id':kind+':'+source+'>'+target,'source':source,'target':target,'kind':kind,'state':state,
            'contacts':contacts if contacts is not None else [{'point_mm':None,'area_mm2':None,'seat_mm':None,'load_share':None}]}


def merge_relations(relations):
    'IA: Agrupa contactos al mismo apoyo sin contarlo dos veces; estados distintos no se mezclan silenciosamente.'
    result={}
    for r in relations:
        key=(r['source'],r['target'],r['kind'])
        if key not in result:result[key]=dict(r,contacts=list(r['contacts']))
        else:
            if result[key]['state']!=r['state']:raise ValueError('Estados de contacto incompatibles')
            for contact in r['contacts']:
                if contact not in result[key]['contacts']:result[key]['contacts'].append(contact)
    return list(result.values())


def from_nominal(nominal):
    'IA: Traduce pertenencia, apoyos declarados y accesos; conserva IDs; no convierte daño/acceso en apoyo ni asigna resistencia no medida.'
    elements=[schema.element(n['id'],n['type'],**{k:v for k,v in n.items() if k not in ('id','type')}) for n in nominal['nodes']]
    relations=[];annotations=[]
    for a,b,kind in nominal['relations']:
        if kind=='contains':source,target,typed=b,a,'HOSTED_BY'
        elif kind in ('supports','nominal_support'):source,target,typed=b,a,'SUPPORTED_BY'
        elif kind=='access':source,target,typed=a,b,'CONNECTED_TO'
        else:annotations.append({'source':a,'target':b,'kind':kind});continue
        relations.append(dict(relation(source,target,typed),evidence='declared_nominal'))
    relations=merge_relations(relations)
    model={'schema':schema.VERSION,'units':dict(schema.UNITS),'elements':elements,'relations':relations,'annotations':annotations,'scope':'read_only_nominal; no measured contact or structural strength'}
    schema.synchronise_supports(model)
    model['materials_signature']=materials.signature()
    return model


def report(model):
    'IA: Resume cobertura real del adaptador y conflictos sin declarar estabilidad de elementos con apoyos desconocidos.'
    supported={r['source'] for r in model['relations'] if r['kind']=='SUPPORTED_BY'}
    structural={'WALL','FLOOR','ROOF','RAFTERS','BATTENS','TILES','TERRACE_BEAMS','DECK','PARAPET','MERLONS','STAIR'}
    return {'issues':graph.validate(model)+schema.validate(model),'unresolved_supports':sorted(e['id'] for e in model['elements'] if e['kind'] in structural and e['id'] not in supported),'unresolved_policies':sorted(e['id'] for e in model['elements'] if e['id'] in supported and 'minimum_supports' not in e),'regeneration_order':graph.order(model)[0],'geometry_changed':False}
