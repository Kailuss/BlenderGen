"""Entrega reproducible de v0.32, sin scripts embebidos."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Empaqueta addon, ejemplo y evidencia tras comprobar informes; valida ZIP y manifiesto SHA256.'
    report=json.loads((ROOT/'reports/v032.json').read_text(encoding='utf-8'))
    assert len(report)==3 and all(not item['closure']['open_edges'] for item in report)
    for log,marker in [('v032.log','V032_PASSED'),('tile_fit.log','TILE_FIT_PASSED'),('roof_v032_after.log','ROOF_SURFACE_PASSED')]:
        assert marker in (ROOT/'reports'/log).read_text(encoding='utf-8',errors='replace')
    files=['dist/ruinas_panel_v032.zip','dist/ruina_v032.blend','reports/v032_exterior.png','reports/v032_interior.png','reports/v032_worn.png','reports/v032.json','docs/V032.md']
    manifest={}
    target=ROOT/'dist/ruinas_v032_completo.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for item in files:
            path=ROOT/item;data=path.read_bytes();archive.writestr(path.name,data)
            manifest[path.name]=hashlib.sha256(data).hexdigest()
        archive.writestr('SHA256.json',json.dumps(manifest,indent=2))
        archive.writestr('LEEME.txt','Ruinas 0.32. Instala ruinas_panel_v032.zip y abre ruina_v032.blend.\nLa vista interior es un recorte de inspección; el blend conserva la casa completa.\nConsulta V032.md para validación y límites de impresión.\n')
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('BUNDLE_PASSED',target)


if __name__=='__main__':run()
