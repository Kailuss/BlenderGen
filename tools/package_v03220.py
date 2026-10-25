"""Publica manual y manifiesto solo después del ciclo y reapertura validados."""
import hashlib
import html
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Exige diez segundos, STL cerrado y ninguna pieza fugada; genera manual local y hashes sin empaquetar una prueba fallida.'
    cycle=json.loads((ROOT/'reports/reported_cycle.json').read_text(encoding='utf8'))
    reopen=json.loads((ROOT/'reports/reported_cycle_reopen.json').read_text(encoding='utf8'))
    assert cycle['simulation']['duration_seconds']==10 and cycle['simulation']['time_scale']==1
    assert cycle['export']['closed'] and not reopen['escaped_below_floor']
    rows=[]
    for line in (ROOT/'docs/V03220.md').read_text(encoding='utf8').splitlines():
        text=html.escape(line)
        if line.startswith('## '):rows.append('<h2>'+text[3:]+'</h2>')
        elif line.startswith('# '):rows.append('<h1>'+text[2:]+'</h1>')
        elif line:rows.append('<p>'+text.replace('**','')+'</p>')
    rows.append('<h2>Ejemplo calculado</h2><p><a href="repro_revoco_ciclo.blend">Abrir archivo Blender</a> · <a href="repro_revoco_ciclo.stl">STL del fotograma final</a> · <a href="ruinas_panel_v03220.zip">Complemento 0.32.20</a></p>')
    rows.append('<img style="max-width:100%" src="../reports/reported_cycle_final.png" alt="Resultado de la prueba de diez segundos">')
    target=ROOT/'dist/Manual_Ruinas_v03220.html'
    target.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Ruinas 0.32.20</title><style>body{font:17px/1.6 system-ui;max-width:900px;margin:40px auto;padding:20px;background:#faf8f2;color:#232925}h2{margin-top:2em}</style>'+''.join(rows),encoding='utf8')
    paths=[target]+[ROOT/'dist'/name for name in ('repro_revoco_ciclo.blend','repro_revoco_ciclo.stl','ruinas_panel_v03220.zip')]
    manifest={}
    for path in paths:
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1048576),b''):digest.update(chunk)
        manifest[path.name]={'bytes':path.stat().st_size,'sha256':digest.hexdigest()}
    (ROOT/'reports/v03220_delivery.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('V03220_PACKAGED',flush=True)


if __name__=='__main__':run()
