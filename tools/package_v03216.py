"""Entrega reproducible de la revisión de construcción."""
import json,zipfile,html,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Empaqueta addon, fuentes editables con laboratorios, ejemplos de daño y manual con hashes, sin presentar los ejemplos como física horneada.'
    rows=[]
    for line in (ROOT/'docs/V03216.md').read_text(encoding='utf8').splitlines():
        safe=html.escape(line);safe=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',safe)
        if safe.startswith('## '):rows.append('<h2>'+safe[3:]+'</h2>')
        elif safe.startswith('# '):rows.append('<h1>'+safe[2:]+'</h1>')
        elif safe:rows.append('<p>'+safe+'</p>')
    manual=ROOT/'dist/Manual_Ruinas_v03216.html'
    manual.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Ruinas 0.32.16</title><style>body{font:17px/1.6 system-ui;max-width:900px;margin:40px auto;padding:20px;background:#faf8f2;color:#232925}h2{margin-top:2em}</style>'+''.join(rows),encoding='utf8')
    files=[manual,ROOT/'docs/V03216.md',ROOT/'reports/v03216.json',ROOT/'reports/v03216_tower_damage.json']
    files += [ROOT/'dist'/name for name in ('ruinas_panel_v03216.zip','ruinas_v03216_WOOD_0.blend','ruinas_v03216_STONE_0.blend','ruinas_v03216_torre_dano_1.blend','ruinas_v03216_torre_dano_2.blend')]
    files += [ROOT/'reports'/name for name in ('v03216_WOOD_0.png','v03216_STONE_0.png','v03216_tower_damage_1.png','v03216_tower_damage_2.png')]
    manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
    target=ROOT/'dist/ruinas_v03216_pruebas.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:archive.write(path,path.name)
        archive.writestr('manifest.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    (ROOT/'reports/v03216_delivery.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('V03216_PACKAGED',flush=True)


if __name__=='__main__':run()
