from pathlib import Path
import html,zipfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import dev

def run():
    'IA: Empaqueta addon, casa física y manual de impactos, comprobando integridad del ZIP.'
    dev.pack(project=True)
    manual=(ROOT/'docs/MANUAL_IMPACTOS.md').read_text(encoding='utf-8-sig')
    (ROOT/'dist/Manual_Ruinas_Impactos.html').write_text('<!doctype html><meta charset="utf-8"><title>Ruinas · impactos</title><style>body{max-width:850px;margin:40px auto;font:17px/1.6 system-ui;background:#eee9df}pre{white-space:pre-wrap;font:inherit}</style><pre>'+html.escape(manual)+'</pre>',encoding='utf8')
    target=ROOT/'dist/ruinas_v0327_completo.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ['dist/ruinas_panel_v0327.zip','dist/ruinas_v0327_casa_impacto.blend','dist/Manual_Ruinas_Impactos.html','docs/MANUAL_IMPACTOS.md','reports/impact_house.json','reports/impact_reopen.json','reports/impact_house_before.png','reports/impact_house_after.png']:
            z.write(ROOT/name,Path(name).name)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print('MASONRY_PACKAGE_PASSED',target)
if __name__=='__main__':run()
