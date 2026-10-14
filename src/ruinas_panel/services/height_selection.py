"""Selección reproducible por porcentaje y altura, independiente de la simulación."""
import math,random,json


def ranked(records,percent,gradient,seed):
    'IA: Muestreo ponderado sin reemplazo; porcentaje exacto redondeado, gradiente cero uniforme y positivo favorece cotas altas sin excluir las bajas.'
    records=sorted(records,key=lambda r:r[0]);count=min(len(records),max(0,round(len(records)*percent/100)))
    if not records or not count:return []
    low=min(r[1] for r in records);span=max(r[1] for r in records)-low;rng=random.Random(seed)
    scores=[]
    for key,z in records:
        height=(z-low)/span if span>1e-12 else .5
        weight=math.exp(4*max(0,min(1,gradient))*height)
        scores.append((-math.log(max(1e-12,rng.random()))/weight,key))
    return [key for score,key in sorted(scores)[:count]]


def choose(scene):
    'IA: Selecciona solo piezas originalmente móviles del laboratorio; excluye terreno, base y proyectiles, conserva simulación y no suelta uniones por sorpresa.'
    if not scene.get('structural_physics') or scene.get('ruinas_replay'):raise ValueError('Abre el laboratorio estructural editable.')
    p=scene.ruin_settings;roles={'ALL':{'stone','tile','wood','metal'},'STONE':{'stone'},'TILE':{'tile'},'WOOD':{'wood'},'METAL':{'metal'}}[p.physics_selection_material]
    eligible=[o for o in scene.objects if o.rigid_body and o.get('original_body_type',o.rigid_body.type)=='ACTIVE' and not o.get('collision_floor') and not o.get('impactor') and o.get('physical_role','stone' if o.get('masonry_brick') else '') in roles]
    names=ranked([(o.name,float(o.location.z)) for o in eligible],p.physics_selection_percent,p.physics_selection_gradient,p.physics_selection_seed)
    chosen={scene.objects[name] for name in names}
    for ob in scene.objects:ob.select_set(ob in chosen)
    if chosen:scene.view_layers[0].objects.active=scene.objects[names[0]]
    report={'eligible':len(eligible),'selected':len(chosen),'percent':p.physics_selection_percent,'gradient':p.physics_selection_gradient,'seed':p.physics_selection_seed,'roles':{role:sum(o.get('physical_role','stone')==role for o in chosen) for role in sorted(roles)}}
    scene['height_selection_report']=json.dumps(report)
    return sorted(chosen,key=lambda o:o.name)
