"""Segunda fase: aplica influencias y añade carpintería/remates a la fábrica base."""
from .. import meta,runtime,config
from ..geometry import timber,terrain,rubble,primitives
from . import layout,destruction,openings,relations,holes,floors,roof


def finish(coll,p,scene):
    'IA: Orden contractual: derrumbe, vanos/vigas, contactos, agujeros compatibles, suelos/escaleras y cubierta; acabado fino se difiere a generation.'
    walls=meta.get(scene,'paredes_generadas');door=meta.get(scene,'puerta_generada');centers=meta.get(scene,'pilares_generados')
    edges,rh=layout.course_layout(p)
    destruction.apply(coll,p,scene)
    timber.wooden_frame(coll,p,door);timber.wooden_door(coll,p,door)
    openings.architectural_openings(coll,p,walls,door,edges)
    relations.register(coll,scene)
    holes.apply(coll,p,scene,walls)
    floors.build(coll,p,scene);roof.build(coll,p,scene)
    terrain.pier_ground(coll,p,centers)
    if runtime.quality in config.DAMAGE_QUALITIES and getattr(p,'damage_enabled',True):
        stone=primitives.material('Piedra · neutro',(.52,.52,.52));mortar=primitives.material('Núcleo · neutro',(.44,.44,.44))
        rubble.build_rubble(coll,stone,mortar,p,door,rh)
