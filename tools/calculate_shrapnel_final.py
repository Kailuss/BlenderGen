"""Calcula la puesta en escena con tejas convexas y subpasos reforzados."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from stage_shrapnel_house import addon,runtime,OUT,simulate


def run():
    'IA: Conserva mallas, masas y trayectorias; usa tejas convexas y HIGH con 160 subpasos en el trabajador específico; exige auditoría posterior.'
    addon.register();runtime.busy=runtime.preview=True
    lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'));bpy.context.window.scene=lab;lab.frame_set(1)
    lab.ruin_settings.physics_precision='HIGH'
    proxies=[]
    for ob in lab.objects:
        if ob.rigid_body and ob.rigid_body.type=='ACTIVE' and ob.get('physical_role')=='tile':
            ob.rigid_body.collision_shape='CONVEX_HULL';ob.rigid_body.collision_margin=0;proxies.append(ob.name)
    report=json.loads((OUT/'impactos.json').read_text(encoding='utf8'))
    report['collision_profile']=dict(precision='HIGH',substeps=160,iterations=60,convex_tiles=proxies,passive_collision_merged_exactly=True,visual_meshes_unchanged=True)
    report['limits']='Ensayo artístico dirigido: cuerpos fuera de los corredores pasivos; piezas retenidas hasta contacto; proyectiles guiados. 160 subpasos, 60 iteraciones, tejas móviles convexas y obstáculos pasivos agrupados con sus superficies originales. Sin calibración mecánica ni predicción causal.'
    (OUT/'impactos.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'03e_laboratorio_entrega.blend'))
    print('FINAL_CALCULATION',len(proxies),'convex moving pieces',flush=True)
    simulate(lab,report)


if __name__=='__main__':run()
