"""Dependencias tipadas, validación y pérdida de apoyos a escala arquitectónica."""
from collections import defaultdict, deque
import heapq

KINDS={'SUPPORTED_BY','CONNECTED_TO','HOSTED_BY','ARRIOSTRADO_POR'}


def support_policy(node,parents):
    'IA: Grupos explícitos exigen k de n en cada grupo; minimum_supports es abreviatura de un único grupo y None conserva apoyo desconocido.'
    if 'support_groups' in node and 'minimum_supports' in node:
        raise ValueError('support_groups y minimum_supports son excluyentes')
    if 'support_groups' not in node:
        minimum=node.get('minimum_supports')
        if minimum is None:return None
        if not isinstance(minimum,int) or isinstance(minimum,bool) or minimum<1:
            raise ValueError('Mínimo de apoyos inválido')
        return [{'id':'all','members':sorted(parents),'minimum':minimum}]
    groups=node['support_groups']
    if not isinstance(groups,list) or not groups:raise ValueError('Grupos de apoyo vacíos')
    seen=set();covered=set()
    for group in groups:
        if not isinstance(group,dict):raise ValueError('Grupo de apoyo inválido')
        key=group.get('id');members=group.get('members');minimum=group.get('minimum')
        if not isinstance(key,str) or not key or key in seen:raise ValueError('Identificador de grupo inválido o repetido')
        seen.add(key)
        if not isinstance(members,list) or not members or any(not isinstance(m,str) for m in members):
            raise ValueError('Miembros de grupo vacíos o inválidos')
        if len(set(members))!=len(members) or not set(members)<=parents:
            raise ValueError('Grupo con apoyo repetido o no declarado')
        if not isinstance(minimum,int) or isinstance(minimum,bool) or not 1<=minimum<=len(members):
            raise ValueError('Mínimo de grupo inválido')
        covered.update(members)
    if covered!=parents:raise ValueError('Apoyos declarados sin grupo')
    return groups


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
        if 'support_groups' in node and 'minimum_supports' in node:
            issues.append({'code':'CONFLICTING_SUPPORT_POLICIES','element':key})
        if 'support_groups' in node:
            try:support_policy(node,supports[key])
            except ValueError as exc:issues.append({'code':'INVALID_SUPPORT_GROUPS','element':key,'reason':str(exc)})
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
    'IA: Propaga pérdida si falla cualquier grupo k-de-n, distinguiendo extremos; sin política solo pide revisión y nunca inventa caída.'
    nodes={e['id']:e for e in model['elements']};removed=set(removed)&nodes.keys()
    supports=defaultdict(set)
    for r in model['relations']:
        if r['kind']=='SUPPORTED_BY' and r['source'] in nodes and r['target'] in nodes:supports[r['source']].add(r['target'])
    policies={key:support_policy(node,supports[key]) for key,node in nodes.items()}
    def closure(pessimistic):
        'IA: Punto fijo monótono de pérdidas; política desconocida conserva en optimista y pierde en pesimista solo tras perder algún apoyo.'
        missing=set(removed);changed=True
        while changed:
            changed=False
            for key,parents in supports.items():
                if key in missing or not parents&missing:continue
                groups=policies[key]
                fails=pessimistic if groups is None else any(len(set(g['members'])-missing)<g['minimum'] for g in groups)
                if fails:missing.add(key);changed=True
        return missing
    optimistic=closure(False);pessimistic=closure(True)
    return {'removed':sorted(removed),'unsupported':sorted(optimistic-removed),'requires_review':sorted(pessimistic-optimistic)}
