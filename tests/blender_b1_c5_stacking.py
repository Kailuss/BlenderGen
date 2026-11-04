"""C5-4: predicción pieza sobre pieza desde el aparejo frente a prune_support real."""
import json,sys,time
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime
from ruinas_panel.structure import layout,damage,walls,assembly,destruction
from ruinas_panel.services import removal_events
from ruinas_panel.construction_core import stacking
from ruinas_panel.geometry import primitives


def boxes(coll):
    'IA: Cajas de piedra y junta con la misma clasificación que prune_support, por nombre de objeto.'
    stones=[];mortar=[]
    for ob in coll.objects:
        name=primitives.piece_key(ob)
        if ob.get('escombro'):continue
        stone=name.startswith('Piedra') or (name.startswith('Pilar') and 'sillar' in name)
        if not stone and not name.startswith('Mortero'):continue
        co=primitives.coords(ob);lo=tuple(map(float,co.min(axis=0)));hi=tuple(map(float,co.max(axis=0)))
        (stones if stone else mortar).append((ob.name,lo,hi,'dintel' in name))
    return stones,mortar


def controlled_loss(coll):
    'IA: Pérdida controlada SOLO en la escena de ensayo: quita las piedras bajas del centro del frente y compara poda real con predicción.'
    stones,mortar=boxes(coll)
    centre=sum((lo[0]+hi[0])/2 for _,lo,hi,_ in stones)/max(1,len(stones))
    front=[key for key,lo,hi,_ in stones if bpy.data.objects[key].get('wall_id','front')=='front' and abs((lo[0]+hi[0])/2-centre)<8 and lo[2]<=stacking.GROUND_Z_MM+10]
    predicted=set(stacking.predict(stones,mortar,front))
    primitives.remove_objects([bpy.data.objects[k] for k in front])
    captured=[];remove0=removal_events.remove
    def remove(objects,cause):
        'IA: Instrumentación: nombres podados.'
        objects=list(objects);captured.extend(ob.name for ob in objects);return remove0(objects,cause)
    removal_events.remove=remove
    try:destruction.prune_support(coll)
    finally:removal_events.remove=remove0
    actual=set(captured)
    assert front and actual==predicted,(len(front),sorted(actual^predicted)[:10])
    return {'removed':len(front),'pruned':len(actual),'predicted':len(predicted),'stones_pruned':sum(1 for k in actual if not k.startswith('Mortero'))}


def run():
    'IA: Tres semillas; exige paridad exacta de la regla extraída y mide, sin aprobar, el acierto de la predicción desde el aparejo.'
    addon.register();runtime.busy=True;runtime.preview=True;runtime.instance_build=False
    p=bpy.context.scene.ruin_settings
    p.layout_mode='ROOM';p.height_type='THREE';p.length=190;p.building_depth=100
    p.lock_distribution=False;p.door_enabled=False;p.floor_beams=True;p.upper_floor=False;p.ground_floor=False;p.stair_type='NONE'
    p.roof_frame=False;p.roof_tiles=False;p.roof_gables=False;p.chimneys=False;p.balconies=False;p.windows_enabled=False
    p.wear_level='CUSTOM';p.wear=0;p.cracks=0;p.rubble_amount=0;p.damage_enabled=True;p.hole_count=1;p.hole_size=20;p.hole_damage=.3
    cases=[];apply0=destruction.apply;prune0=destruction.prune_support;remove0=removal_events.remove
    for collapse in (.18,.45):
        for seed in (1,20,73):
            started=time.perf_counter();p.collapse=collapse;p.seed=seed;layout.apply_profiles(p);q=damage.effective_settings(p)
            runtime.settings=q;runtime.quality='DRAFT';runtime.timings={};snap={};removed={}
            def apply(coll,pp,scene):
                'IA: Instrumentación: aparejo antes de cualquier retirada de destrucción global.'
                snap['layout']=boxes(coll);return apply0(coll,pp,scene)
            def prune(coll):
                'IA: Instrumentación: cajas reales justo antes de la poda.'
                snap['before_prune']=boxes(coll);return prune0(coll)
            def remove(objects,cause):
                'IA: Instrumentación: nombres retirados por causa.'
                objects=list(objects);removed.setdefault(cause,[]).extend(ob.name for ob in objects);return remove0(objects,cause)
            destruction.apply=apply;destruction.prune_support=prune;removal_events.remove=remove
            try:
                coll=walls._build_wall(bpy.context,q);assembly.finish(coll,q,bpy.context.scene)
            finally:destruction.apply=apply0;destruction.prune_support=prune0;removal_events.remove=remove0
            if 'layout' not in snap:
                cases.append({'seed':seed,'collapse':collapse,'skipped':'sin destrucción global'});continue
            actual=set(removed.get('PRUNE_SUPPORT',[]))
            parity=set(stacking.prune(*snap['before_prune'])[1])
            assert parity==actual,(seed,collapse,sorted(parity^actual)[:10])
            predicted=set(stacking.predict(*snap['layout'],removed.get('GLOBAL_COLLAPSE',[])))
            control=controlled_loss(coll)
            cases.append({'seed':seed,'collapse':collapse,'global_removed':len(removed.get('GLOBAL_COLLAPSE',[])),
                          'pruned':len(actual),'predicted':len(predicted),'matched':len(actual&predicted),
                          'missed':sorted(actual-predicted),'extra':sorted(predicted-actual),'controlled_loss':control,
                          'seconds':round(time.perf_counter()-started,2)})
            print('C5_4',json.dumps({k:v for k,v in cases[-1].items() if k not in ('missed','extra')}),'missed',len(actual-predicted),'extra',len(predicted-actual),flush=True)
    report={'scope':'C5-4 pieza sobre pieza: regla extraída (paridad exacta) y predicción desde aparejo previo a la destrucción',
            'criterion':'stacking.prune; los recortes COLLAPSE_EDGE no se modelan en la predicción','cases':cases}
    (ROOT/'reports/b1_c5_stacking.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('PASSED blender_b1_c5_stacking')


run()
