"""B1-C4: replay causal desde entrada de assembly y auditoría independiente final."""
import json,sys,time
from pathlib import Path
from types import SimpleNamespace
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.structure import layout,damage,walls,assembly,openings,floor_frame
from ruinas_panel.services import removal_events
from ruinas_panel.construction_core import identifiers,seat,causal_support
from ruinas_panel.construction_core.removal_ledger import RemovalLedger
from ruinas_panel.geometry import primitives


def capture(coll,p,scene):
    'IA: Contactos medidos ANTES de assembly; no es predicción pura de layout y excluye omisiones previas del constructor.'
    ledger=runtime.removal_ledger
    model={'elements':[{'id':key} for key in ledger.elements],'relations':[]}
    descriptors={w['id']:w for w in meta.get(scene,'paredes_generadas')}
    records=[]
    for level,base in enumerate(layout.floor_bases(p)[1:],1):
        z=base-3.6
        axes=floor_frame.aligned_axes(*[layout.masonry_joints(layout.masonry_intervals(p,descriptors[w],z)) for w in ('front','back')])
        for axis in axes['axes']:
            for wall in ('front','back'):
                records.append({'id':identifiers.segment(wall,level-1,axis['ordinal']),'level':level,'wall':wall,'x':axis['x_mm'],'z':z,'axis':axis['ordinal'],'contacts':[[],[],[]]})
    for wall in ('front','back'):
        w=descriptors[wall];selected=[r for r in records if r['wall']==wall]
        for ob in coll.objects:
            tree=openings.wall_tree(SimpleNamespace(objects=[ob]),w)
            for record in selected:
                for i,(x,z) in enumerate(seat.samples(record['x'],record['z'])):
                    if openings.wall_hit(tree,w,p,x,z):record['contacts'][i].append(ob['construction_id'])
    for record in records:
        initial=seat.supported(bool(ids) for ids in record['contacts']);record['initial_supported']=initial
        if not initial:continue
        probes=[]
        for i,ids in enumerate(record['contacts']):
            if not ids:continue
            key=record['id']+'/probe/'+str(i);probes.append(key)
            model['elements'].append({'id':key,'minimum_supports':1})
            model['relations'].extend({'source':key,'target':target,'kind':'SUPPORTED_BY','contact_z_mm':record['z']+seat.VERTICAL_OFFSET_MM} for target in ids)
        model['elements'].append({'id':record['id'],'minimum_supports':seat.MINIMUM_HITS})
        model['relations'].extend({'source':record['id'],'target':key,'kind':'SUPPORTED_BY'} for key in probes)
    for record in records:
        if record['wall']!='front' or not record['initial_supported']:continue
        rear=next(r for r in records if r['wall']=='back' and r['level']==record['level'] and r['axis']==record['axis'])
        if not rear['initial_supported']:continue
        key=identifiers.beam(record['level'],record['axis'])
        model['elements'].append({'id':key,'support_groups':[{'id':r['wall'],'members':[r['id']],'minimum':1} for r in (record,rear)]})
        model['relations'].extend({'source':key,'target':r['id'],'kind':'SUPPORTED_BY'} for r in (record,rear))
    return model,records,descriptors


def run():
    'IA: Tres semillas T1, sin vanos ni escaleras; reporta incertidumbres y ejes no mapeados sin confundirlas con coincidencias.'
    addon.register();runtime.busy=True;runtime.preview=True;runtime.instance_build=False
    p=bpy.context.scene.ruin_settings
    p.layout_mode='ROOM';p.height_type='THREE';p.length=190;p.building_depth=100
    p.lock_distribution=False;p.door_enabled=False;p.floor_beams=True;p.upper_floor=False;p.ground_floor=False;p.stair_type='NONE'
    p.roof_frame=False;p.roof_tiles=False;p.roof_gables=False;p.chimneys=False;p.balconies=False;p.windows_enabled=False
    p.collapse=.18;p.hole_count=1;p.hole_size=20;p.hole_damage=.3;p.wear_level='CUSTOM';p.wear=0;p.cracks=0;p.rubble_amount=0;p.damage_enabled=True
    cases=[];original=removal_events.begin
    for seed in (1,20,73):
        started=time.perf_counter();p.seed=seed;layout.apply_profiles(p);q=damage.effective_settings(p)
        runtime.settings=q;runtime.quality='DRAFT';runtime.timings={};captured=[]
        def begin(coll,scene):
            'IA: Instrumentación de ensayo antes de cualquier evento de assembly.'
            original(coll,scene);captured.append(capture(coll,q,scene))
        removal_events.begin=begin
        try:
            coll=walls._build_wall(bpy.context,q);assembly.finish(coll,q,bpy.context.scene)
        finally:removal_events.begin=original
        model,records,descriptors=captured[0]
        ledger=RemovalLedger.load(meta.get(bpy.context.scene,'removal_ledger'))
        prediction=causal_support.replay(model,ledger)
        trees={wall:openings.wall_tree(coll,w) for wall,w in descriptors.items()}
        for record in records:
            key=record['id']
            state='INITIAL_CONTACT_ABSENT' if not record['initial_supported'] else 'UNSUPPORTED' if key in prediction['unsupported'] else 'REQUIRES_REVIEW' if key in prediction['requires_review'] else 'SUPPORTED'
            actual=seat.supported(openings.wall_hit(trees[record['wall']],descriptors[record['wall']],q,x,z) for x,z in seat.samples(record['x'],record['z']))
            record.update(graph_state=state,measured_supported=actual,discrepancy=(actual!=(state=='SUPPORTED')) if state in ('SUPPORTED','UNSUPPORTED') else None)
        beam_map=[]
        for beam in meta.get(bpy.context.scene,'vigas_generadas',[]):
            ends=[]
            for wall in ('front','back'):
                matches=[r for r in records if r['wall']==wall and abs(r['x']-beam['x'])<=.05 and abs(r['z']-beam['z'])<=.001]
                actual=seat.supported(openings.wall_hit(trees[wall],descriptors[wall],q,x,z) for x,z in seat.samples(beam['x'],beam['z']))
                ends.append({'wall':wall,'segment_id':matches[0]['id'] if len(matches)==1 else None,'axis':matches[0]['axis'] if len(matches)==1 else None,'map_state':'MATCHED' if len(matches)==1 else 'UNMAPPED','measured_supported':actual})
            beam_map.append(dict(beam,ends=ends))
        causes={}
        for event in ledger.events:causes[event['cause']]=causes.get(event['cause'],0)+1
        # Control destructivo SOLO en la escena de ensayo: quitar un asiento
        # completo debe producir pérdida causal y ausencia geométrica real.
        target_id=beam_map[0]['ends'][0]['segment_id']
        target=next(r for r in records if r['id']==target_id)
        keys={key for contacts in target['contacts'] for key in contacts}
        removed=[ob for ob in coll.objects if ob.get('construction_id') in keys]
        control=RemovalLedger.load(ledger.dump())
        for ob in removed:control.record(ob['construction_id'],'REMOVE','CONTROL_REMOVE_CONTACT')
        primitives.remove_objects(removed)
        control_prediction=causal_support.replay(model,control)
        tree=openings.wall_tree(coll,descriptors['front'])
        measured=seat.supported(openings.wall_hit(tree,descriptors['front'],q,x,z) for x,z in seat.samples(target['x'],target['z']))
        beam_id=identifiers.beam(target['level'],target['axis'])
        assert target_id in control_prediction['unsupported'] and beam_id in control_prediction['unsupported'] and not measured
        assert target_id not in prediction['unsupported'] and target_id not in prediction['requires_review']
        negative={'segment_id':target_id,'beam_id':beam_id,'removed_ids':sorted(keys),'predicted_unsupported':True,'measured_supported':measured,'missing_event_detected':True}
        cases.append({'seed':seed,'seconds':time.perf_counter()-started,'events_by_cause':causes,'ledger':ledger.dump(),'graph':model,'prediction':prediction,'segments':records,'beam_axis_map':beam_map,'negative_control':negative})
        primitives.drop_stage();print('C4_T1_CASE',seed,len(ledger.events),flush=True)
    report={'scope':'assembly-entry contacts measured before operations; NOT pure layout or full T1 acceptance','B1_0_closed':False,'cases':cases}
    (ROOT/'reports/b1_c4_t1.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('C4_T1_REPLAY_COMPLETED',flush=True)


if __name__=='__main__':run()
