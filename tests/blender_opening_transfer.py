"""Comparación de carpintería del generador con sus copias físicas."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel.services import physics


def extent(objects,factor):
    'IA: Caja mundial a partir de transformaciones RNA guardadas; no evalúa Bullet en escenas inactivas.'
    points=[(o.matrix_basis@v.co)*factor for o in objects for v in o.data.vertices]
    if not points:return None
    low=[min(v[i] for v in points) for i in range(3)];high=[max(v[i] for v in points) for i in range(3)]
    return {'min':low,'max':high,'size':[b-a for a,b in zip(low,high)]}


def run():
    'IA: Mide hojas, jambas y travesaños en mm antes y después de preparar; agrupa fragmentos por source_piece y documenta pérdidas sin confundir unidades.'
    addon.register();source=bpy.data.scenes['01 · Casa editable'];lab=bpy.data.scenes['02 · Laboratorio editable']
    groups={}
    for ob in lab.objects:
        if ob.type=='MESH':groups.setdefault(ob.get('source_piece',''),[]).append(ob)
    records=[]
    for ob in source.objects:
        if ob.type!='MESH' or not (ob.get('hoja_puerta') or any(t in ob.name.lower() for t in ('jamba','cabezal','ventana travesaño'))):continue
        before=extent([ob],1);after=extent(groups.get(ob.name,[]),1000)
        records.append({'name':ob.name,'before':before,'after':after,'delta_size_mm':[b-a for a,b in zip(before['size'],after['size'])] if after else None})
    door=[o for o in source.objects if o.get('hoja_puerta')]
    report={'door_leaf_before':extent(door,1),'door_leaf_after':extent([p for o in door for p in groups.get(o.name,[])],1000),'pieces':records}
    frames={}
    for ob in source.objects:
        if ob.type=='MESH' and ob.get('window_frame'):frames.setdefault(ob.get('wall_id',''),[]).append(ob)
    report['frames']={wall:{'before':extent(objects,1),'after':extent([p for o in objects for p in groups.get(o.name,[])],1000)} for wall,objects in frames.items()}
    report['source_matches']=physics.source_matches(lab)
    (ROOT/'reports/opening_transfer.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('OPENING_TRANSFER',report['door_leaf_before'],report['door_leaf_after'],flush=True)
    print('LARGEST_CHANGES',[(r['name'],r['delta_size_mm']) for r in sorted(records,key=lambda r:max(abs(v) for v in r['delta_size_mm']) if r['delta_size_mm'] else 1000,reverse=True)[:12]],flush=True)
    assert report['source_matches'] is True,'Fuente y laboratorio pertenecen a configuraciones diferentes.'
    for name,pair in [('puerta',{'before':report['door_leaf_before'],'after':report['door_leaf_after']})]+list(report['frames'].items()):
        assert pair['after'],name
        assert max(abs(b-a) for key in ('min','max') for a,b in zip(pair['before'][key],pair['after'][key]))<.5,(name,pair)
    width=source.ruin_settings.window_width
    source.ruin_settings.window_width=width+1
    assert physics.source_matches(lab) is False
    source.ruin_settings.window_width=width
    assert physics.source_matches(lab) is True
    print('OPENING_TRANSFER_PASSED',flush=True)


if __name__=='__main__':run()
