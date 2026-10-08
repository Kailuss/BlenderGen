"""Entrega experimental de estructura sin mortero y manual HTML legible."""
import sys,re,html,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import dev


def run():
    'IA: Empaqueta únicamente artefactos existentes de v0325, con manual derivado de Markdown y comprobación CRC del ZIP.'
    dev.pack(project=True)
    source=(ROOT/'docs/MANUAL_ESTRUCTURA.md').read_text(encoding='utf8')
    content=html.escape(source)
    content=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',content)
    content=re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)',r'<a href="\2">\1</a>',content)
    content=re.sub(r'^## (.+)$',r'<h2>\1</h2>',content,flags=re.M)
    content=re.sub(r'^# (.+)$',r'<h1>\1</h1>',content,flags=re.M)
    header='<!doctype html><html lang="es"><meta charset="utf-8"><title>Ruinas · estructura sin mortero</title><style>body{max-width:850px;margin:48px auto;padding:0 24px;background:#f4f0e8;color:#252724;font:17px/1.6 system-ui}article{white-space:pre-wrap}h1,h2{white-space:normal;line-height:1.25}h2{margin-top:2em}a{color:#80502a}</style><article>'
    manual=ROOT/'dist/Manual_Ruinas_Estructura.html';manual.write_text(header+content+'</article></html>',encoding='utf8')
    names=['dist/ruinas_panel_v0325.zip','dist/ruinas_v0325_estructura_interactiva.blend','dist/Manual_Ruinas_Estructura.html','docs/MANUAL_ESTRUCTURA.md','docs/V0325.md','reports/structural_physics.json','reports/structural_demo.json','reports/structural_reopen.json','reports/structure_complete.png','reports/structure_interior_before.png','reports/structure_interior_after.png']
    target=ROOT/'dist/ruinas_v0325_completo.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in names:archive.write(ROOT/name,Path(name).name)
        archive.writestr('LEEME.txt','Instala ruinas_panel_v0325.zip. Abre ruinas_v0325_estructura_interactiva.blend y pulsa Espacio. La escena 03 muestra el interior de la misma simulación. Lee Manual_Ruinas_Estructura.html: ensayo experimental, aún sin reconstrucción de mortero ni exportación del resultado físico.\n')
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('STRUCTURAL_PACKAGE_PASSED',target)


if __name__=='__main__':run()
