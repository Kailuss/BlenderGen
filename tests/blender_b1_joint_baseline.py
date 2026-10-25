"""B1.0: juntas nominales frente a mallas antes de modificar el productor."""
import json,subprocess,sys,time
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import meta,runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import damage,layout,openings,walls,floor_frame
from ruinas_panel.construction_core import graph

AXIS_TOLERANCES_MM={'front':.05,'back':.001}


def run():
    'IA: Compara dos cotas de viga y una sonda con layout puro en tres semillas; verifica cobertura de segmentos y pérdida localizada sin ejecutar el laboratorio.'
    addon.register();runtime.busy=True;runtime.preview=True;runtime.instance_build=False
    p=bpy.context.scene.ruin_settings
    p.layout_mode='ROOM';p.height_type='THREE';p.length=190;p.building_depth=100
    p.damage_enabled=False;p.lock_distribution=False;p.door_enabled=False
    rows=[];skeletons=[];started=time.perf_counter()
    for seed in (1,20,73):
        p.seed=seed;layout.apply_profiles(p);effective=damage.effective_settings(p)
        runtime.settings=effective;runtime.quality='DRAFT';runtime.timings={}
        coll=walls._build_wall(bpy.context,effective)
        descriptors={w['id']:w for w in meta.get(bpy.context.scene,'paredes_generadas')}
        edges,_=layout.course_layout(effective)
        samples=[(level,base,'floor_beam') for level,base in enumerate(layout.floor_bases(effective)[1:],1)]
        samples.append((None,effective.height,'wall_top_probe'))
        for level,base,role in samples:
            z=base-3.6
            for wall_id in ('front','back'):
                w=descriptors[wall_id]
                intervals=layout.masonry_intervals(effective,w,z,edges)
                source='pure layout producer'
                nominal=layout.masonry_joints(intervals);measured=openings.beam_joints(coll,w,z)
                delta=max((abs(a[0]-b[0]) for a,b in zip(nominal,measured)),default=0)
                tolerance=AXIS_TOLERANCES_MM[wall_id]
                rows.append({'seed':seed,'level':level,'sample_role':role,'base_mm':base,'wall':wall_id,'z_mm':z,'source':source,
                             'nominal_count':len(nominal),'measured_count':len(measured),
                             'tolerance_mm':tolerance,'max_axis_error_mm':delta,'pass':len(nominal)==len(measured) and delta<=tolerance})
        z=layout.floor_bases(effective)[1]-3.6
        axes=floor_frame.aligned_axes(*[layout.masonry_joints(layout.masonry_intervals(effective,descriptors[k],z,edges)) for k in ('front','back')],tolerance_mm=1.5)
        assert axes['axes'],axes
        model=floor_frame.beam_skeleton(axes['axes'][0],[(2,z)],{'front':0,'back':descriptors['back']['origin'][1]},
                                        seat_width_mm=4.2,seat_depth_mm=3,margin_world_mm=30,min_seat_world_mm=120,model_scale=60)
        coverage=[]
        for element in model['elements']:
            if element['kind']!='WALL_SEGMENT':continue
            props=element['properties'];lo,hi=props['interval_model_mm'];z0,z1=props['band_model_mm'];count=0
            for ob in coll.objects:
                if not ob.name.startswith('Piedra') or ob.get('wall_id','front')!=props['wall']:continue
                co=primitives.coords(ob)
                if co[:,0].max()>lo and co[:,0].min()<hi and co[:,2].max()>z0 and co[:,2].min()<z1:count+=1
            assert count,element
            coverage.append({'segment':element['id'],'stone_count':count})
        removed=coverage[0]['segment'];loss=graph.loss(model,[removed])
        assert loss['unsupported']==[model['beam_id']],loss
        skeletons.append({'seed':seed,'axes':axes,'segment_count':model['segment_count'],'coverage':coverage,'loss':loss,
                          'scope':'one beam at first floor; nominal contacts, no raycast or mesh consumer'})
        primitives.drop_stage()
    report={'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'scope':'intact masonry before assembly openings, DRAFT; both walls use pure layout',
            'axis_tolerances_mm':AXIS_TOLERANCES_MM,'seconds':time.perf_counter()-started,'cases':rows,'skeletons':skeletons,
            'discrepancies':[r for r in rows if not r['pass']],
            'B1_0_complete':False,'remaining':'test assembly openings and damaged geometry separately'}
    (ROOT/'reports/b1_joint_baseline.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    assert not report['discrepancies'],report['discrepancies']
    print('B1_JOINT_BASELINE_PASSED',len(rows),flush=True)


if __name__=='__main__':run()
