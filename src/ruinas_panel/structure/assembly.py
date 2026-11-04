"""Segunda fase: aplica influencias y añade carpintería/remates a la fábrica base."""
from .. import meta,runtime,config
from ..geometry import timber,terrain,rubble,primitives
from . import layout,destruction,openings,relations,holes,floors,roof,floor_plan,placement,interiors


def finish(coll,p,scene):
    'IA: Orden contractual: derrumbe, vanos/vigas, contactos, agujeros compatibles, suelos/escaleras y cubierta; acabado fino se difiere a generation.'
    walls=meta.get(scene,'paredes_generadas');door=meta.get(scene,'puerta_generada');centers=meta.get(scene,'pilares_generados')
    edges,rh=layout.course_layout(p)
    from . import construction_plan
    construction_plan.prepare(p,walls,scene)
    plan={}
    if p.layout_mode=='ROOM':
        lookup={w['id']:w for w in walls}
        bounds=(lookup['left']['origin'][0]+p.thickness/2-.6,lookup['right']['origin'][0]-p.thickness/2+.6,p.thickness/2-.6,lookup['back']['origin'][1]-p.thickness/2+.6)
        plan=floor_plan.plan(p,bounds,door,construction_plan.stair(scene,1))
    meta.put(scene,'plano_interior',plan)
    from ..services import removal_events
    removal_events.begin(coll,scene)
    destruction.apply(coll,p,scene)
    timber.wooden_frame(coll,p,door);timber.wooden_door(coll,p,door)
    openings.architectural_openings(coll,p,walls,door,edges)
    relations.register(coll,scene)
    holes.apply(coll,p,scene,walls)
    from . import facade_details
    facade_details.build(coll,p,scene,walls,door)
    floors.build(coll,p,scene);interiors.build(coll,p,scene);roof.build(coll,p,scene)
    from . import building_definition
    definition=meta.get(scene,'building_definition') or building_definition.define(p)
    meta.put(scene,'architectural_graph',building_definition.graph(definition,walls,plan,meta.get(scene,'ventanas_generadas',[]),meta.get(scene,'cubierta_roturas',[]),bool(meta.get(scene,'cubierta_generada',[])),door,meta.get(scene,'escaleras_generadas',[])))
    terrain.pier_ground(coll,p,centers)
    if runtime.quality in config.DAMAGE_QUALITIES and getattr(p,'damage_enabled',True):
        stone=primitives.material('Piedra · neutro',(.52,.52,.52));mortar=primitives.material('Núcleo · neutro',(.44,.44,.44))
        rubble.build_rubble(coll,stone,mortar,p,door,rh)
    from . import foundations
    foundations.build(coll,p,scene)
    removal_events.end()
