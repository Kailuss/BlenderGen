"""Entrega reproducible del ensayo integrado y su manual."""
import html,json,zipfile,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Empaqueta únicamente artefactos existentes y verificados, con informes y manual; no altera la fuente del addon.'
    report=json.loads((ROOT/'reports/synergy_physics.json').read_text(encoding='utf8'))
    assert report.get('simulation')
    export=json.loads((ROOT/'reports/synergy_export.json').read_text(encoding='utf8'));assert export
    audit=json.loads((ROOT/'reports/delivery_audit.json').read_text(encoding='utf8'))
    assert audit.get('source_matches') is True and audit.get('build')=='0.32.11-r2'
    assert json.loads((ROOT/'reports/opening_transfer.json').read_text(encoding='utf8')).get('source_matches') is True
    replay=json.loads((ROOT/'reports/replay_audit.json').read_text(encoding='utf8'))
    assert replay['pieces_compared']>0 and not replay['below_safety_floor']
    with (ROOT/'dist/ruinas_v03211_integrada.blend').open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==audit['blend_sha256']
    manual=(ROOT/'docs/MANUAL_SELECCION_ALTURA.md').read_text(encoding='utf8')
    for suffix in ('blend','stl'):shutil.copy2(ROOT/('dist/ruinas_v03211_integrada.'+suffix),ROOT/('dist/ruinas_v03211_r2_integrada.'+suffix))
    page='<!doctype html><meta charset="utf-8"><title>Ruinas 0.32.11-r2 · Madera y desprendimiento</title><style>body{max-width:900px;margin:40px auto;padding:0 24px;font:17px/1.6 system-ui;background:#eee9df}pre{white-space:pre-wrap;font:inherit}img{max-width:100%}</style><pre>'+html.escape(manual)+'</pre>'
    path=ROOT/'dist/Manual_Ruinas_Seleccion_r2.html';path.write_text(page,encoding='utf8')
    files=['dist/ruinas_panel_v03211_r2.zip','dist/ruinas_v03211_r2_integrada.blend','dist/ruinas_v03211_r2_integrada.stl','dist/Manual_Ruinas_Seleccion_r2.html','docs/MANUAL_SELECCION_ALTURA.md']
    files+=['reports/'+name for name in ('synergy_source.json','synergy_physics.json','synergy_export.json','synergy_source.png','synergy_final.png','synergy_timber.png','synergy_splinters.png','replay_audit.json','delivery_audit.json','memory_probe_fixed.json','solver_scale.json')]
    files.append('reports/opening_transfer.json')
    target=ROOT/'dist/ruinas_v03211_r2_completo.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in files:archive.write(ROOT/name,Path(name).name)
        archive.writestr('LEEME.txt','Instala ruinas_panel_v03211_r2.zip y reinicia Blender tras guardar tu trabajo. Comprueba v0.32.11-r2 en el panel: abrir el .blend no actualiza el addon. Abre ruinas_v03211_r2_integrada.blend: contiene la casa editable, el laboratorio, la reproducción y el sólido. Elige la escena 03 para reproducir la caída; la escena 02 conserva la selección y sus uniones. Consulta Manual_Ruinas_Seleccion_r2.html y los informes.\n')
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('SYNERGY_PACKAGED',target)


if __name__=='__main__':run()
