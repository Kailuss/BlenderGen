"""0.32.31: ninguna pieza de la terraza del torreón queda sin apoyo real (caso imposible.blend, semilla 17, y barrido de semillas)."""
import sys,json,time
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.geometry import primitives
from ruinas_panel.construction_core import roof_support as rs
from blender_probe import closure


def box(ob):
    'IA: Caja (lo, hi) en mm de la malla real.'
    co=primitives.coords(ob)
    return tuple(float(v) for v in co.min(axis=0)),tuple(float(v) for v in co.max(axis=0))


def audit(coll,p):
    'IA: Auditoría independiente del constructor: vigas con piedra bajo las dos cabezas, losas y bloques sin vuelco sobre lo aceptado y piezas caídas reposando sobre algo real.'
    walls={w['id']:w for w in meta.get(bpy.context.scene,'paredes_generadas',[])}
    x0=walls['left']['origin'][0]-p.thickness/2;x1=walls['right']['origin'][0]+p.thickness/2
    tower=[o for o in coll.objects if o.get('tower_part') or (o.get('roof_timber') and 'terraza' in primitives.piece_key(o))]
    fallen=[o for o in coll.objects if o.get('tower_fallen')]
    others=[o for o in coll.objects if o not in tower and o not in fallen and len(o.data.vertices)]
    stones=[box(o) for o in others if primitives.piece_key(o).startswith(('Piedra','Pilar')) and not o.get('escombro') and not o.get('stair')]
    problems=[];gaps=[]
    beams=[o for o in tower if o.get('roof_timber')]
    for ob in beams:
        lo,hi=box(ob)
        if not primitives.piece_key(ob).startswith('Madera · viga terraza'):continue
        for end,foot in ((lo[0],(lo[0],x0+p.thickness,lo[1],hi[1])),(hi[0],(x1-p.thickness,hi[0],lo[1],hi[1]))):
            if x0+1.5<end<x1-1.5:continue
            under=[b[1][2] for b in stones if rs.rect_overlap(foot,*b) and b[0][2]<lo[2]]
            gap=lo[2]-max(under,default=-1e9);gaps.append(round(gap,2))
            if gap>rs.BEARING_GAP_MM or not rs.bearing(foot,lo[2],stones)[0]:problems.append(('viga sin entrega',ob.name,round(gap,2)))
    seats=[box(o) for o in beams]
    decks=[o for o in tower if o.get('tower_part')=='deck']
    for ob in decks:
        if not rs.seated(box(ob),seats,rs.MIN_SLAB_CONTACT)[0]:problems.append(('losa sin apoyo',ob.name))
    accepted=[box(o) for o in decks]
    for ob in sorted((o for o in tower if o.get('tower_part') in ('parapet','merlon')),key=lambda o:box(o)[0][2]):
        b=box(ob)
        if rs.seated(b,accepted,rs.MIN_BLOCK_CONTACT)[0]:accepted.append(b)
        else:problems.append(('bloque sin apoyo',ob.name))
    surfaces=[box(o) for o in others]+[box(o) for o in tower]
    for ob in fallen:
        lo,hi=box(ob);foot=(lo[0],hi[0],lo[1],hi[1])
        rest=max([b[1][2] for b in surfaces+[box(o) for o in fallen if o is not ob] if rs.rect_overlap(foot,*b) and b[1][2]<=lo[2]+.5],default=0.0)
        if lo[2]-rest>.3 and lo[2]>.5:problems.append(('pieza caída flotando',ob.name,round(lo[2]-rest,2)))
    return {'beams':len(beams),'decks':len(decks),'blocks':len(accepted)-len(decks),'fallen':len(fallen),'bearing_gaps':sorted(gaps)[-4:],'problems':problems}


def generate(p,values):
    'IA: Aplica ajustes (los que no existen se anotan) y genera en Trabajo sin instancias, para auditar objetos reales.'
    skipped=[]
    for key,value in values.items():
        try:setattr(p,key,value)
        except Exception:skipped.append(key)
    p.use_instances=False;p.batch_preview=False;p.live_preview=False
    started=time.perf_counter();coll=addon.generate(bpy.context,p,'WORK')
    return coll,skipped,round(time.perf_counter()-started,1)


def run():
    'IA: Regenera imposible.blend con el código actual y exige terraza sin piezas colgadas y malla cerrada; repite con un torreón pequeño en 8 semillas y dos daños.'
    bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings;report={'cases':[]}
    values=json.loads((ROOT/'tests/fixtures/imposible_s17.json').read_text(encoding='utf-8'))
    coll,skipped,seconds=generate(p,values)
    result=audit(coll,p);result.update(name='imposible_s17',seconds=seconds,skipped=skipped,support=meta.get(scene,'cubierta_detalles').get('support'))
    sealed=closure(coll);result['open_edges']=len(sealed['open_edges']);report['cases'].append(result)
    print('ROOF_SUPPORT_CASE',json.dumps(result,ensure_ascii=False),flush=True)
    out=ROOT/'dist/pruebas';out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'roof_support_imposible_s17.blend'))
    small=dict(length=80,building_depth=80,height_type='TWO',layout_mode='ROOM',pillar_count=0,door_enabled=True,windows_enabled=False,roof_frame=True,roof_type='TOWER',ground_floor=True,upper_floor=True,stair_type='NONE',hole_count=0,cracks=0,rubble_amount=.5,ground_roughness=0)
    addon.unregister();bpy.ops.wm.read_factory_settings(use_empty=True);addon.register();runtime.busy=True;runtime.preview=True
    scene=bpy.context.scene;p=scene.ruin_settings
    for seed in range(1,9):
        for collapse,damage in ((.55,0),(.3,.7)):
            coll,_,seconds=generate(p,dict(small,seed=seed,collapse=collapse,roof_damage=damage))
            result=audit(coll,p);result.update(name='torre_%s_%s_%s'%(seed,collapse,damage),seconds=seconds,support=meta.get(scene,'cubierta_detalles').get('support'))
            result['open_edges']=len(closure(coll)['open_edges']);report['cases'].append(result)
            print('ROOF_SUPPORT_CASE',json.dumps(result,ensure_ascii=False),flush=True)
    (ROOT/'reports/roof_support.json').write_text(json.dumps(report,indent=1,ensure_ascii=False),encoding='utf8')
    bad=[c for c in report['cases'] if c['problems'] or c['open_edges']]
    assert not bad,[(c['name'],c['problems'][:5],c['open_edges']) for c in bad]
    print('ROOF_SUPPORT_PASSED',len(report['cases']),'casos',flush=True)


if __name__=='__main__':run()
