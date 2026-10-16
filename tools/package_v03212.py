"""Manual HTML y paquete de resultados; el código instalable viene de dev.py pack."""
import hashlib,html,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Crea manual legible sin dependencias, empaqueta cuatro etapas y STL con hashes; comprueba la integridad ZIP, sin modificar fuentes ni archivos aportados.'
    rows=[]
    for line in (ROOT/'docs/MANUAL_V03212.md').read_text(encoding='utf8').splitlines():
        safe=html.escape(line)
        safe=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',safe);safe=re.sub(r'`([^`]+)`',r'<code>\1</code>',safe)
        if safe.startswith('## '):rows.append('<h2>'+safe[3:]+'</h2>')
        elif safe.startswith('# '):rows.append('<h1>'+safe[2:]+'</h1>')
        elif safe:rows.append('<p>'+safe+'</p>')
    target=ROOT/'dist/Manual_Ruinas_v03212.html'
    target.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Ruinas 0.32.12 · Manual</title><style>body{font:17px/1.6 system-ui;max-width:900px;margin:40px auto;padding:0 24px;background:#faf8f2;color:#232925}h1,h2{line-height:1.2}h2{margin-top:2em;color:#315440}code{background:#e7ece5;padding:2px 5px}p{margin:.8em 0}</style><main>'+''.join(rows)+'</main></html>',encoding='utf8')
    files=[ROOT/'dist'/name for name in ('ruinas_panel_v03212.zip','ruinas_v03212_torre_integrada.blend','ruinas_v03212_torre.stl','Manual_Ruinas_v03212.html')]
    files += [ROOT/'docs'/name for name in ('MANUAL_V03212.md','V03212.md','REESTRUCTURACION_03212.md')]
    files += [ROOT/'reports'/name for name in ('v03212_integration.json','v03212_tower_source.png','v03212_tower_shake.png','v03212_tower_interior.png')]
    manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
    destination=ROOT/'dist/ruinas_v03212_completo.zip'
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:archive.write(path,path.name)
        archive.writestr('manifest.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(destination) as archive:assert archive.testzip() is None
    (ROOT/'reports/v03212_delivery.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('DELIVERY_PACKAGED',destination,flush=True)


if __name__=='__main__':run()
