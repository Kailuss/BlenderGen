"""T1/T2: auditoría de daño y vanos; no usa medidas como entradas del grafo."""
import json,sys,time,subprocess
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.structure import layout,damage,walls,assembly,openings,floor_frame
from ruinas_panel.geometry import primitives


def snapshot(coll):
    'IA: Captura cajas para auditar piedras supervivientes, nunca para decidir los apoyos del plan.'
    result=[]
    for ob in coll.objects:
        if not ob.name.startswith('Piedra'):continue
        co=primitives.coords(ob)
        if len(co):result.append({'name':ob.name,'wall':ob.get('wall_id','front'),'lo':co.min(axis=0).tolist(),'hi':co.max(axis=0).tolist()})
    return result


def measure(stones,wall,x,z,half=2.6):
    'IA: Fracción proyectada en X de piedras en la banda bajo asiento [z-4.5,z-2.7]; evita muestrear solo una junta horizontal de mortero.'
    selected=[s for s in stones if s['wall']==wall and s['hi'][0]>x-half and s['lo'][0]<x+half and s['hi'][2]>2 and s['lo'][2]<z]
    spans=sorted((max(x-half,s['lo'][0]),min(x+half,s['hi'][0])) for s in selected if s['lo'][2]<z-2.7 and s['hi'][2]>z-4.5)
    length=0;end=x-half
    for a,b in spans:
        length+=max(0,b-max(a,end));end=max(end,b)
    return {'stone_count':len(selected),'seat_fraction':length/(2*half),'stone_names':[s['name'] for s in selected]}


def run():
    'IA: Tres semillas por T1/T2 con misma casa; informa ausencia de eventos causales sin fabricar predicciones ni cero discrepancias.'
    addon.register();runtime.busy=True;runtime.preview=True;runtime.instance_build=False
    p=bpy.context.scene.ruin_settings
    p.layout_mode='ROOM';p.height_type='THREE';p.length=190;p.building_depth=100
    p.lock_distribution=False;p.door_enabled=False;p.floor_beams=True;p.upper_floor=False;p.ground_floor=False;p.stair_type='NONE'
    p.roof_frame=False;p.roof_tiles=False;p.roof_gables=False;p.chimneys=False;p.balconies=False
    p.window_canopies=False;p.window_projection=0;p.window_leaves=False;p.windows_per_wall=3
    p.collapse=.18;p.hole_count=1;p.hole_size=20;p.hole_damage=.3;p.wear_level='CUSTOM';p.wear=0;p.cracks=0;p.rubble_amount=0
    results=[]
    for mode in ('T1','T2'):
        for seed in (1,20,73):
            started=time.perf_counter();p.seed=seed;p.damage_enabled=False;p.windows_enabled=False
            layout.apply_profiles(p);q=damage.effective_settings(p);runtime.settings=q;runtime.quality='DRAFT';runtime.timings={}
            coll=walls._build_wall(bpy.context,q);initial=snapshot(coll)
            descriptors={w['id']:w for w in meta.get(bpy.context.scene,'paredes_generadas')}
            probes=[]
            for role,level,z in [('floor_beam',1,layout.floor_bases(q)[1]-3.6),('floor_beam',2,layout.floor_bases(q)[2]-3.6),('wall_top_probe',None,q.height-3.6)]:
                axes=floor_frame.aligned_axes(*[layout.masonry_joints(layout.masonry_intervals(q,descriptors[w],z)) for w in ('front','back')])
                for a in axes['axes']:
                    for wall in ('front','back'):
                        probes.append({'id':f"seg.{wall}.{level-1 if level else 'probe'}.{a['ordinal']}",'wall':wall,'level':level,'role':role,'z':z,'axis':a,'initial':measure(initial,wall,a['x_mm'],z)})
            p.damage_enabled=True;p.windows_enabled=mode=='T2';q=damage.effective_settings(p);runtime.settings=q
            coll=walls._build_wall(bpy.context,q);assembly.finish(coll,q,bpy.context.scene)
            final=snapshot(coll);records=[]
            windows=meta.get(bpy.context.scene,'ventanas_generadas',[])
            for probe in probes:
                measured=measure(final,probe['wall'],probe['axis']['x_mm'],probe['z'])
                blocked=[h for h in windows if h['wall']==probe['wall'] and h['x0']-2.5<=probe['axis']['x_mm']<=h['x1']+2.5 and h['z0']<=probe['z']<=h['z1']]
                records.append(dict(probe,remaining=measured,axis_state='BLOQUEADO_POR_VANO' if blocked else 'CANDIDATO',
                    sensitivity=[{'threshold':t,'measured_supported':measured['seat_fraction']>=t} for t in (.06,.12,.24)],
                    graph_state=None,discrepancy=None,cause='MISSING_PURE_DAMAGE_EVENTS: graph has no independent per-stone removal input'))
            floating=0;beam_count=0;front_tree=openings.wall_tree(coll,descriptors['front'])
            for beam in meta.get(bpy.context.scene,'vigas_generadas',[]):
                if beam['wall']!='front':continue
                beam_count+=1
                if sum(openings.wall_hit(front_tree,descriptors['front'],q,beam['x']+dx,beam['z']-2.7) for dx in (-1.5,0,1.5))<2:floating+=1
            results.append({'mode':mode,'seed':seed,'seconds':time.perf_counter()-started,'segments':records,
                'candidate_axis_count':len(probes)//2,'generated_front_beams':beam_count,'front_seat_failed_ray_audit':floating,
                'graph_unsupported_beams':None,'derrumbe_global':meta.get(bpy.context.scene,'derrumbe_global'),
                'holes':meta.get(bpy.context.scene,'huecos_generados'),'windows':windows,
                'coverage_scope':'front/back segment boxes; first two floors and wall-top probe; no rear/header beam contact certification'})
            primitives.drop_stage();print('C3_CASE',mode,seed,flush=True)
    report={'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'B1_0_closed':False,'status':'MEASURED_WITH_UNRESOLVED_CAUSAL_INPUT',
            'criterion':'union of remaining X intervals intersecting band [z-4.5,z-2.7] / segment width; thresholds 0.06,0.12,0.24; sensitivity only; beam audit uses original 2-of-3 rays, including mortar',
            'cases':results}
    for mode in ('T1','T2'):
        (ROOT/f'reports/b1_c3_{mode.lower()}.json').write_text(json.dumps(dict(report,cases=[r for r in results if r['mode']==mode]),indent=2),encoding='utf8')
    print('B1_C3_AUDIT_COMPLETED_NOT_ACCEPTED',flush=True)


if __name__=='__main__':run()
