"""Vanos independientes, alojamientos de vigas y revoco con ruido continuo."""
import sys,json,time
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.geometry import plaster
from blender_probe import closure
from blender_v032 import render


def run():
    'IA: Exige paños cerrados antes y después de perforar con ruido, verifica medidas de balcón independientes y guarda inspección del hastial.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;p.live_preview=False
    counts=[]
    for damage in (0,.7,1):
        vertices,faces=plaster.panel(list(range(-60,61,4)),0,[60-abs(x)*.7 for x in range(-60,61,4)],0,4,20,damage)
        mesh=bpy.data.meshes.new('Paño');mesh.from_pydata(vertices,[],faces)
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert all(e.is_manifold for e in bm.edges),(damage,'open')
        counts.append({'damage':damage,'volume':bm.calc_volume(),'faces':len(bm.faces)});bm.free();bpy.data.meshes.remove(mesh)
    assert counts[-1]['volume']<counts[0]['volume']*.8,counts
    for key,value in dict(length=180,building_depth=150,height_type='TWO',layout_mode='ROOM',interior_layout='OPEN',lock_distribution=False,seed=20,pillar_count=0,damage_enabled=True,collapse=0,hole_count=0,roof_damage=.7,roof_frame=True,roof_tiles=True,roof_gables=True,chimneys=False,brass_pipes=False,windows_enabled=True,balconies=True,window_width=12,window_height=18,balcony_width=24,balcony_height=42,door_width=35,door_height=48,batch_preview=False).items():setattr(p,key,value)
    p.door_enabled=True
    started=time.perf_counter();coll=addon.generate(bpy.context,p,'WORK');closed=closure(coll)
    assert not closed['open_edges'] and not closed['degenerate_faces'],closed
    windows=meta.get(scene,'ventanas_generadas');assert windows and any(w['balcony'] for w in windows)
    for w in windows:
        assert abs(w['x1']-w['x0']-(24 if w['balcony'] else 12))<1e-5
        assert abs(w['z1']-w['z0']-(42 if w['balcony'] else 18))<1e-5
    beams=meta.get(scene,'vigas_generadas');assert beams
    for a,b in zip(beams,beams[1:]):assert abs(b['x']-a['x'])>=20
    render(scene,ROOT/'reports/architecture_revision.png',focus=(0,60,110),location=(240,-300,190),scale=310)
    report={'panels':counts,'windows':windows,'beams':beams,'closure':closed,'seconds':time.perf_counter()-started}
    (ROOT/'reports/architecture_revision.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03211_arquitectura.blend'))
    print('ARCHITECTURE_REVISION_PASSED',report,flush=True)


if __name__=='__main__':run()
