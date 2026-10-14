"""Preparación y simulación aisladas de la casa integrada con selección por altura."""
import sys,time,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics_jobs,structural_physics,height_selection,impact_physics,physics


def calculate(scene,mode):
    'IA: Ejecuta una etapa en hijo vigilado y devuelve escena, tiempo y memoria sin evaluar Bullet en el padre.'
    started=time.perf_counter();job=physics_jobs.start(scene,mode);peak=0;last=0
    while True:
        peak=max(peak,physics_jobs.memory_mb(job['process'].pid));status=physics_jobs.poll()
        if 'finished' in status:return status['finished'],{'seconds':time.perf_counter()-started,'peak_mb':peak}
        if time.perf_counter()-last>20:
            print('SYNERGY_PROGRESS',mode,status,flush=True);last=time.perf_counter()
        time.sleep(1)


def run():
    'IA: Conserva fuente y laboratorio, selecciona porcentaje exacto con gradiente y guarda reproducción de 72 fotogramas con límite explícito de móviles.'
    addon.register();source=bpy.context.scene
    if source.get('structural_physics'):
        lab=source;cost={'reused_checkpoint':bpy.data.filepath}
    elif '--prepared' in sys.argv:
        path=sys.argv[sys.argv.index('--prepared')+1]
        with bpy.data.libraries.load(path,link=False) as (data,loaded):loaded.scenes=data.scenes
        lab=next(s for s in loaded.scenes if s.get('structural_physics'));cost={'reused_checkpoint':path}
    else:lab,cost=calculate(source,'PREPARE')
    assert physics.source_matches(lab) is True,'El checkpoint no corresponde a la configuración actual de la fuente.'
    bpy.context.window.scene=lab;lab.name='02 · Laboratorio editable'
    report={'preparation':json.loads(lab['preparation_report']),'prepare_cost':cost}
    report['timber_joints_added']=structural_physics.connect_timber_fragments(lab)
    connected={o for ob in lab.objects if ob.rigid_body_constraint for o in (ob.rigid_body_constraint.object1,ob.rigid_body_constraint.object2)}
    report['preparation']['unconnected']=[o.name for o in lab.objects if o.rigid_body and o.rigid_body.type=='ACTIVE' and o not in connected]
    assert not report['preparation']['unconnected'],report['preparation']['unconnected']
    report['preparation']['constraints']=sum(o.rigid_body_constraint is not None for o in lab.objects)
    report['preparation']['timber_fracture_joints']=sum(bool(o.get('timber_fracture_joint')) for o in lab.objects)
    lab['preparation_report']=json.dumps(report['preparation'])
    print('SYNERGY_PREPARED',report['preparation']['bodies'],'bodies; extra timber joints',report['timber_joints_added'],flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03211_preparada.blend'))
    structural_physics.merge_ground(lab);print('SYNERGY_GROUND_MERGED',flush=True)
    report['collisions']=structural_physics.optimise_collisions(lab)
    print('SYNERGY_COLLISIONS',report['collisions'],flush=True)
    p=lab.ruin_settings;p.physics_selection_percent=35;p.physics_selection_gradient=.7;p.physics_selection_seed=17;p.physics_selection_material='ALL'
    if '--memory-mb' in sys.argv:p.physics_memory_mb=int(sys.argv[sys.argv.index('--memory-mb')+1])
    p.physics_timeout_seconds=1800
    report['resource_budget']={'memory_mb':p.physics_memory_mb,'seconds':p.physics_timeout_seconds}
    if '--percent' in sys.argv:p.physics_selection_percent=float(sys.argv[sys.argv.index('--percent')+1])
    chosen=height_selection.choose(lab);assert chosen
    if len(chosen)>2048:
        eligible=json.loads(lab['height_selection_report'])['eligible']
        p.physics_selection_percent=int(204800/eligible)
        chosen=height_selection.choose(lab)
    assert {o.name for o in chosen}=={o.name for o in height_selection.choose(lab)}
    report['selection']=json.loads(lab['height_selection_report'])
    assert len(chosen)<=2048,report['selection']
    p.physics_brick_limit=2048;impact_physics.limit_to_selection(lab,chosen)
    report['constraints']=structural_physics.sparsify_constraints(lab)
    structural_physics.release(lab,chosen)
    lab.frame_end=72;lab.rigidbody_world.point_cache.frame_end=72
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03211_laboratorio.blend'))
    (ROOT/'reports/synergy_physics.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    result,cost=calculate(lab,'SIMULATE');bpy.context.window.scene=result;result.name='03 · Reproducción'
    report['simulation']=json.loads(result['simulation_report']);report['simulation_cost']=cost
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dist/ruinas_v03211_integrada.blend'))
    (ROOT/'reports/synergy_physics.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('SYNERGY_PHYSICS_PASSED',report,flush=True)


if __name__=='__main__':run()
