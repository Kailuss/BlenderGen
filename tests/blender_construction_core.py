"""Integración nominal, caché y visualización de cobertura, sin cambiar mallas."""
import sys,json,time,html
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import ruinas_panel as addon
from ruinas_panel import runtime,meta
from ruinas_panel.construction_core import adapter


def run():
    'IA: Genera edificio, verifica modelo y caché, mide coste del núcleo y publica tabla de relaciones sin presentar cobertura incompleta como estabilidad.'
    addon.register();runtime.busy=True
    scene=bpy.context.scene;p=scene.ruin_settings
    p.layout_mode='ROOM';p.height_type='THREE';p.length=190;p.building_depth=100
    p.floor_beams=True;p.upper_floor=True;p.stair_type='WOOD';p.roof_frame=True
    p.damage_enabled=False
    addon.generate(bpy.context,p,'DRAFT')
    model=meta.get(scene,'construction_model');report=meta.get(scene,'construction_validation')
    assert model['elements'] and not report['issues'],report
    meta.put(scene,'construction_model',{'invalid':True})
    addon.generate(bpy.context,p,'DRAFT')
    assert meta.get(scene,'construction_model')==model
    start=time.perf_counter()
    for _ in range(1000):adapter.report(model)
    report['mean_validation_ms']=(time.perf_counter()-start)
    report['model']=model
    (ROOT/'reports/construction_core.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    rows=[]
    for node in model['elements']:
        key=node['id'];unknown=key in report['unresolved_supports'] or key in report['unresolved_policies']
        supports=[r['target'] for r in model['relations'] if r['source']==key and r['kind']=='SUPPORTED_BY']
        rows.append('<tr style="background:%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%('#ffe7b8' if unknown else '#e3edf7',html.escape(key),html.escape(node['kind']),html.escape(', '.join(supports)), 'Pendiente de comprobar' if unknown else 'Relación nominal'))
    (ROOT/'dist/Coherencia_constructiva.html').write_text('<!doctype html><meta charset="utf-8"><title>Coherencia constructiva</title><style>body{font:16px system-ui;margin:40px}td,th{padding:9px;border:1px solid #bbb}table{border-collapse:collapse}</style><h1>Base constructiva: cobertura del modelo</h1><p>Ámbar: apoyos o política sin resolver. Azul: relación nominal. Ningún color certifica resistencia física. La geometría no se modifica.</p><table><tr><th>Elemento</th><th>Tipo</th><th>Apoyo declarado</th><th>Estado</th></tr>'+''.join(rows)+'</table>',encoding='utf8')
    print('CONSTRUCTION_CORE_PASSED',report['mean_validation_ms'],flush=True)


if __name__=='__main__':run()
