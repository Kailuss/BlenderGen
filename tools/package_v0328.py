"""Entrega reproducible de la casa máxima y su resultado físico validado."""
import html,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Empaqueta solo artefactos existentes y auditados, con manual legible y vistas de antes/después.'
    report=json.loads((ROOT/'reports/stress_max_reopen.json').read_text(encoding='utf8'))
    assert report['closed'] and report['consistent_orientation']
    manual=(ROOT/'docs/MANUAL_CARGA_MAXIMA.md').read_text(encoding='utf8')
    parts=[]
    for block in manual.split('\n\n'):
        if block.startswith('# '):parts.append('<h1>'+html.escape(block[2:])+'</h1>')
        elif block.startswith('## '):parts.append('<h2>'+html.escape(block[3:])+'</h2>')
        else:parts.append('<p>'+html.escape(block).replace('\n','<br>')+'</p>')
    page='<!doctype html><html lang="es"><meta charset="utf-8"><title>Ruinas · casa máxima</title><style>body{max-width:920px;margin:40px auto;padding:0 24px;font:17px/1.6 system-ui;background:#f3f0e9;color:#29251f}h1,h2{line-height:1.2}p{white-space:normal}img{max-width:100%}</style><main>'+''.join(parts)+'</main></html>'
    (ROOT/'dist/Manual_Ruinas_Carga_Maxima.html').write_text(page,encoding='utf8')
    names=['dist/ruinas_panel_v0328.zip','dist/ruinas_v0328_maxima.blend','dist/ruinas_v0328_maxima.stl','dist/Manual_Ruinas_Carga_Maxima.html','docs/MANUAL_CARGA_MAXIMA.md']
    names += ['reports/stress_max_'+s+'.json' for s in ('generation','preparation','simulation','export','reopen')]
    names += ['reports/stress_max_'+s+'.png' for s in ('before','after','solid')]
    target=ROOT/'dist/ruinas_v0328_completo.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in names:archive.write(ROOT/name,Path(name).name)
        archive.writestr('LEEME.txt','Abre ruinas_v0328_maxima.blend y pulsa Espacio. Conserva casa, laboratorio, reproducción y sólido. Instala ruinas_panel_v0328.zip para editar. Lee Manual_Ruinas_Carga_Maxima.html. La zona móvil tiene 2048 cuerpos contando el proyectil; el resto es soporte fijo.\n')
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('MAX_PACKAGE_PASSED',target)


if __name__=='__main__':run()