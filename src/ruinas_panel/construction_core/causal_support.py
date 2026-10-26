"""Reproducción conservadora de apoyos desde operaciones confirmadas."""
import copy
import math
from . import graph


def cuts_miss_contact(events,relation):
    'IA: Certifica solo cortes de caja cuyo intervalo Z no toca el rayo horizontal del contacto; planos u otros cortes siguen inciertos.'
    z=relation.get('contact_z_mm')
    if not isinstance(z,(float,int)) or not math.isfinite(z):return False
    for event in events:
        box=event['details'].get('box')
        if not isinstance(box,list) or len(box)!=6:return False
        lo,hi=box[4:]
        if not all(isinstance(v,(float,int)) and math.isfinite(v) for v in (lo,hi)) or lo>hi:return False
        if lo<=z<=hi:return False
    return bool(events)


def replay(model,ledger):
    'IA: Propaga REMOVE; CUT permanece incierto entre conservar y perder la pieza. No consulta geometría final ni ignora IDs causales ausentes.'
    known={node['id'] for node in model['elements']}
    missing=set(ledger.elements)-known
    if missing:raise ValueError('Inventario sin nodos causales: '+', '.join(sorted(missing)))
    removed=ledger.removed()
    modified={e['element_id'] for e in ledger.events if e['operation']=='CUT'}-removed
    low=graph.loss(model,removed)
    # Una pieza raíz recortada fuera del asiento conserva ese contacto. No se
    # permite este atajo para piezas con dependencias: podrían perder apoyo.
    upper=copy.deepcopy(model)
    dependent={r['source'] for r in model['relations'] if r['kind']=='SUPPORTED_BY'}
    for index,relation in enumerate(upper['relations']):
        target=relation['target']
        if relation['kind']!='SUPPORTED_BY' or target not in modified or target in dependent:continue
        cuts=[e for e in ledger.events if e['element_id']==target and e['operation']=='CUT']
        if cuts_miss_contact(cuts,relation):
            key='$causal/contact/'+str(index)
            if key in known:raise ValueError('ID reservado para reproducción causal: '+key)
            upper['elements'].append({'id':key})
            relation['target']=key
    high=graph.loss(upper,removed|modified)
    definite=set(low['unsupported'])
    possible=set(high['unsupported'])|set(high['requires_review'])|modified|set(low['requires_review'])
    return {'removed':sorted(removed),'unsupported':sorted(definite),
            'requires_review':sorted(possible-definite-removed),
            'events':len(ledger.events),'criterion':'REMOVE confirmed; CUT bounded, no residual contact assumed'}
