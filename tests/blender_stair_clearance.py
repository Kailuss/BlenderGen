"""Reserva de los apoyos superiores frente a peldaños y desembarcos."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.geometry import primitives
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Genera tres plantas de alturas distintas y exige que apoyos de forjado y de la propia escalera no crucen ninguna huella ni desembarco.'
    addon.register();runtime.busy=True;runtime.preview=True;results=[]
    for side in ('LEFT','RIGHT'):
        bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;p=scene.ruin_settings
        for key,value in dict(layout_mode='ROOM',height_type='THREE',length=190,building_depth=90,ground_storey_height=75,upper_storey_height=55,stair_type='WOOD',stair_side=side,roof_frame=True,roof_type='TOWER',collapse=.35,hole_count=0,cracks=0,rubble_amount=0,ground_roughness=0,wood_damage=0,batch_preview=False).items():setattr(p,key,value)
        coll=addon.generate(bpy.context,p,'WORK');assert not closure(coll)['open_edges']
        posts=[o for o in coll.objects if primitives.piece_key(o) in ('Madera · poste forjado','Madera · viga de planta','Madera · viga forjado','Madera · poste desembarco','Madera · poste hueco escalera','Madera · travesaño desembarco')]
        treads=[o for o in coll.objects if o.name.startswith(('Madera · peldaño','Madera · desembarco'))]
        assert posts and treads
        conflicts=[]
        for post in posts:
            co=primitives.coords(post);a,b=co.min(axis=0),co.max(axis=0)
            for tread in treads:
                co=primitives.coords(tread);c,d=co.min(axis=0),co.max(axis=0)
                if all(min(b[k],d[k])-max(a[k],c[k])>.01 for k in range(3)):conflicts.append((post.name,tread.name))
        assert not conflicts,conflicts
        results.append({'side':side,'posts':len(posts),'treads':len(treads),'conflicts':conflicts})
        hidden={o:o.hide_render for o in coll.objects}
        for ob in coll.objects:ob.hide_render=not (ob.get('stair') or ob in posts)
        render(scene,ROOT/('reports/stair_clearance_%s.png'%side),focus=(0,55,90),location=(220,-220,260),scale=265)
        for ob,value in hidden.items():ob.hide_render=value
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('dist/ruinas_v03218_escalera_%s.blend'%side)))
    (ROOT/'reports/stair_clearance.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('STAIR_CLEARANCE_PASSED',flush=True)


if __name__=='__main__':run()
