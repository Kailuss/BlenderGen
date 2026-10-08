from pathlib import Path
import html,zipfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import dev

def run():
    'IA: Empaqueta addon, escenas físicas y manual de ladrillos, comprobando integridad del ZIP.'
    dev.pack(project=True)
    manual=(ROOT/'docs/MANUAL_LADRILLOS.md').read_text(encoding='utf-8-sig')
    (ROOT/'dist/Manual_Ruinas_Ladrillos.html').write_text('<!doctype html><meta charset="utf-8"><title>Ruinas · ladrillos</title><style>body{max-width:850px;margin:40px auto;font:17px/1.6 system-ui;background:#eee9df}pre{white-space:pre-wrap;font:inherit}</style><pre>'+html.escape(manual)+'</pre>',encoding='utf8')
    target=ROOT/'dist/ruinas_v0326_completo.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ['dist/ruinas_panel_v0326.zip','dist/ruinas_v0326_ladrillos.blend','dist/Manual_Ruinas_Ladrillos.html','docs/MANUAL_LADRILLOS.md','reports/masonry_physics.json']:
            z.write(ROOT/name,Path(name).name)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print('MASONRY_PACKAGE_PASSED',target)
if __name__=='__main__':run()
