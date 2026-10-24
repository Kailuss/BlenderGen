"""B1.0: juntas nominales frente a mallas antes de modificar el productor."""
import json,random,subprocess,sys,time
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import meta,runtime
from ruinas_panel.geometry import primitives
from ruinas_panel.structure import damage,layout,openings,walls

AXIS_TOLERANCES_MM={'front':.05,'back':.001}


def joints(intervals):
    'IA: Reproduce el criterio contractual de junta sobre intervalos numéricos, sin consultar mallas.'
    ordered=sorted(intervals)
    return [((a[1]+b[0])/2,((a[1]-a[0])+(b[1]-b[0]))/2)
            for a,b in zip(ordered,ordered[1:])
            if -.05<=b[0]-a[1]<=1.5 and min(a[1]-a[0],b[1]-b[0])>=5.3]


def rear_intervals(p,w,z,edges):
    'IA: Calcula el aparejo trasero con los parámetros previos al mallado; conserva semillas y retranqueos heredados.'
    rh=(p.height-2)/(len(edges)-1);start,end=w['start'],w['end']
    bays=max(2,round((end-start)/(rh*1.8)));pitch=(end-start)/bays
    for row in range(len(edges)-1):
        if not edges[row]+.23<z<min(edges[row+1],w['height'])-.25:continue
        subdivisions=min(p.bond_subdivisions,max(1,int(pitch/3.2))) if row%2 else 1
        local=pitch/subdivisions;rng=random.Random(layout.distribution_seed(p)+row*3701+307)
        points=[start]
        for j in range(bays*subdivisions):
            x=start+(j+(.5 if row%2 else 1))*local
            if start+.01<x<end-.01:
                points.append(x+rng.uniform(-1,1)*local*(.12 if subdivisions==1 else .08)*p.stone_variation)
        points.append(end)
        return [(a+.18,b-.18) for a,b in layout.merge_thin_stones(list(zip(points,points[1:])),3.2)]
    return []


def run():
    'IA: Mide tres cotas y tres semillas sin tocar el laboratorio; identifica la ausencia de productor puro de fachada en vez de ocultarla.'
    addon.register();runtime.busy=True;runtime.preview=True;runtime.instance_build=False
    p=bpy.context.scene.ruin_settings
    p.layout_mode='ROOM';p.height_type='THREE';p.length=190;p.building_depth=100
    p.damage_enabled=False;p.lock_distribution=False;p.door_enabled=False
    rows=[];started=time.perf_counter()
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
                if wall_id=='front':
                    # Estos intervalos son parámetros de construcción, no coordenadas leídas de vértices.
                    audit=meta.get(bpy.context.scene,'aparejo_escalonado')
                    intervals=[(r['x0'] if r['x0']<=-p.length/2+.01 else r['x0']+.22,
                                r['x1'] if r['x1']>=p.length/2-.01 else r['x1']-.22)
                               for r in audit if r['z0']<z<r['z1']]
                    source='nominal intervals recorded by wall builder; pure front producer still missing'
                else:
                    intervals=rear_intervals(effective,w,z,edges);source='pure rear layout'
                nominal=joints(intervals);measured=openings.beam_joints(coll,w,z)
                delta=max((abs(a[0]-b[0]) for a,b in zip(nominal,measured)),default=0)
                tolerance=AXIS_TOLERANCES_MM[wall_id]
                rows.append({'seed':seed,'level':level,'sample_role':role,'base_mm':base,'wall':wall_id,'z_mm':z,'source':source,
                             'nominal_count':len(nominal),'measured_count':len(measured),
                             'tolerance_mm':tolerance,'max_axis_error_mm':delta,'pass':len(nominal)==len(measured) and delta<=tolerance})
        primitives.drop_stage()
    report={'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'scope':'intact masonry before openings, DRAFT; front uses recorded nominal intervals, not a pure producer',
            'axis_tolerances_mm':AXIS_TOLERANCES_MM,'seconds':time.perf_counter()-started,'cases':rows,
            'discrepancies':[r for r in rows if not r['pass']],
            'B1_0_complete':False,'remaining':'extract pure front course producer; test openings and damaged geometry separately'}
    (ROOT/'reports/b1_joint_baseline.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    assert not report['discrepancies'],report['discrepancies']
    print('B1_JOINT_BASELINE_PASSED',len(rows),flush=True)


if __name__=='__main__':run()
