"""Dependencias tipadas, validación y pérdida de apoyos a escala arquitectónica."""
from collections import defaultdict, deque
import heapq

KINDS={'SUPPORTED_BY','CONNECTED_TO','HOSTED_BY','ARRIOSTRADO_POR'}


def validate(model):
    'IA: Detecta IDs repetidos, referencias, tipos, políticas y ciclos; apoyo declarado no implica contacto geométrico ni cálculo resistente.'
    issues=[];nodes={};seen=set()
    for element in model['elements']:
        key=element['id']
        if key in nodes:issues.append({'code':'DUPLICATE_ELEMENT','element':key})
        nodes[key]=element
        minimum=element.get('minimum_supports')
        if minimum is not None and (not isinstance(minimum,int) or isinstance(minimum,bool) or minimum<1):
            issues.append({'code':'INVALID_SUPPORT_POLICY','element':key})
    supports=defaultdict(set)
    for relation in model['relations']:
        a,b,kind=relation['source'],relation['target'],relation['kind']
        key=relation['id']
        if key in seen:issues.append({'code':'DUPLICATE_RELATION','element':a,'relation':key})
        seen.add(key)
        if model.get('schema',1)>=3 and relation.get('state') not in ('INTACTO','ASENTADO'):issues.append({'code':'INVALID_RELATION_STATE','element':a,'relation':key})
        if a not in nodes or b not in nodes:issues.append({'code':'MISSING_ELEMENT','element':a,'relation':key});continue
        if kind not in KINDS:issues.append({'code':'INVALID_RELATION','element':a,'relation':key});continue
        if a==b:issues.append({'code':'SELF_RELATION','element':a,'relation':key})
        if kind=='SUPPORTED_BY':
            supports[a].add(b)
            if nodes[b].get('kind') in ('OPENING','DOOR','DAMAGE_EVENT'):
                issues.append({'code':'INVALID_SUPPORT_KIND','element':a,'relation':key})
    for key,node in nodes.items():
        minimum=node.get('minimum_supports')
        if isinstance(minimum,int) and len(supports[key])<minimum:
            issues.append({'code':'INSUFFICIENT_DECLARED_SUPPORTS','element':key,'required':minimum,'available':len(supports[key])})
    _,unresolved=order(model)
    if unresolved:issues.append({'code':'DEPENDENCY_CYCLE_OR_BLOCKED','elements':unresolved})
    return issues


def order(model,subset=None):
    'IA: Orden determinista de anfitriones/apoyos antes de dependientes; conexiones laterales no introducen ciclos de regeneración.'
    nodes={e['id'] for e in model['elements']}
    selected=nodes if subset is None else nodes&set(subset)
    dependencies={key:set() for key in selected};children=defaultdict(set)
    for r in model['relations']:
        a,b=r['source'],r['target']
        if r['kind'] in ('SUPPORTED_BY','HOSTED_BY') and a in selected and b in selected:
            dependencies[a].add(b);children[b].add(a)
    ready=[key for key,parents in dependencies.items() if not parents];heapq.heapify(ready);result=[]
    while ready:
        key=heapq.heappop(ready);result.append(key)
        for child in sorted(children[key]):
            dependencies[child].discard(key)
            if not dependencies[child]:heapq.heappush(ready,child)
    return result,sorted(selected-set(result))


def affected(model,changed):
    'IA: Propaga invalidación por apoyo/anfitrión; conexiones solo invalidan su otro extremo, sin confundir unión lateral con transmisión de carga.'
    known={e['id'] for e in model['elements']};dirty=set(changed)&known
    children=defaultdict(set);connections=defaultdict(set)
    for r in model['relations']:
        a,b=r['source'],r['target']
        if r['kind'] in ('SUPPORTED_BY','HOSTED_BY','ARRIOSTRADO_POR'):children[b].add(a)
        elif r['kind']=='CONNECTED_TO':connections[a].add(b);connections[b].add(a)
    # Solo las conexiones de los cambios originales requieren revisar ambos extremos.
    for key in list(dirty):dirty.update(connections[key]&known)
    queue=deque(sorted(dirty))
    while queue:
        for child in sorted(children[queue.popleft()]):
            if child in known and child not in dirty:dirty.add(child);queue.append(child)
    sequence,blocked=order(model,dirty)
    return {'dirty':sorted(dirty),'order':sequence,'blocked':blocked}


def loss(model,removed):
    'IA: Evalúa pérdida discreta de apoyos únicos según mínimo explícito; política ausente produce revisión, nunca derrumbe automático.'
    nodes={e['id']:e for e in model['elements']};missing=set(removed)&nodes.keys();failed=set();review=set()
    supports=defaultdict(set)
    for r in model['relations']:
        if r['kind']=='SUPPORTED_BY' and r['source'] in nodes and r['target'] in nodes:supports[r['source']].add(r['target'])
    changed=True
    while changed:
        changed=False
        for key,parents in supports.items():
            if key in missing or not parents&missing:continue
            minimum=nodes[key].get('minimum_supports')
            if minimum is None:review.add(key);continue
            if not isinstance(minimum,int) or isinstance(minimum,bool) or minimum<1:raise ValueError('Política de apoyo inválida: '+key)
            if len(parents-missing)<minimum:
                failed.add(key);missing.add(key);changed=True
    return {'removed':sorted(set(removed)&nodes.keys()),'unsupported':sorted(failed),'requires_review':sorted(review-failed)}
