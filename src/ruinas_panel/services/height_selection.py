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


def regional(records,center,radii,percent):
    'IA: Devuelve cuota redondeada dentro de un elipsoide mundial, del centro al borde y sin azar; radios positivos, desempate estable por nombre.'
    if any(r<=0 for r in radii):raise ValueError('Los tres alcances deben ser positivos.')
    scores=[]
    for name,point in records:
        distance=sum(((point[i]-center[i])/radii[i])**2 for i in range(3))
        if distance<=1+1e-9:scores.append((distance,name))
    scores.sort();count=min(len(scores),max(0,round(len(scores)*percent/100)))
    return [name for _,name in scores[:count]],len(scores)


def choose(scene):
    'IA: Selecciona móviles por altura o zona centrada en la pieza activa/cursor; permite acumular solo elegibles y conserva uniones, simulación y pieza maestra.'
    if not scene.get('structural_physics') or scene.get('ruinas_replay'):raise ValueError('Abre el laboratorio estructural editable.')
    p=scene.ruin_settings;roles={'ALL':{'stone','tile','wood','metal'},'STONE':{'stone'},'TILE':{'tile'},'WOOD':{'wood'},'METAL':{'metal'}}[p.physics_selection_material]
    eligible=[o for o in scene.objects if o.rigid_body and o.get('original_body_type',o.rigid_body.type)=='ACTIVE' and not o.get('collision_floor') and not o.get('impactor') and o.get('physical_role','stone' if o.get('masonry_brick') else '') in roles]
    mode=p.physics_selection_mode;active=scene.view_layers[0].objects.active
    center=None;zone_count=len(eligible)
    if mode=='HEIGHT':
        names=ranked([(o.name,float(o.location.z)) for o in eligible],p.physics_selection_percent,p.physics_selection_gradient,p.physics_selection_seed)
    else:
        if mode=='MASTER':
            if active not in eligible:raise ValueError('Activa una pieza móvil de la familia elegida como centro de daño.')
            center=tuple(active.matrix_world.translation)
        else:center=tuple(scene.cursor.location)
        names,zone_count=regional([(o.name,tuple(o.matrix_world.translation)) for o in eligible],center,p.physics_selection_radii,p.physics_selection_percent)
    chosen={scene.objects[name] for name in names}
    if p.physics_selection_add:chosen.update(o for o in eligible if o.select_get())
    for ob in scene.objects:ob.select_set(ob in chosen)
    if chosen:scene.view_layers[0].objects.active=active if active in chosen else sorted(chosen,key=lambda o:o.name)[0]
    report={'mode':mode,'center':center,'zone_eligible':zone_count,'zone_selected':len(names),'eligible':len(eligible),'selected':len(chosen),'percent':p.physics_selection_percent,'gradient':p.physics_selection_gradient,'seed':p.physics_selection_seed,'roles':{role:sum(o.get('physical_role','stone')==role for o in chosen) for role in sorted(roles)}}
    scene['height_selection_report']=json.dumps(report)
    return sorted(chosen,key=lambda o:o.name)
