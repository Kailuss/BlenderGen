"""Entrega reproducible de v0.32, sin scripts embebidos."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def run():
    'IA: Empaqueta addon, ejemplo y evidencia tras comprobar informes; valida ZIP y manifiesto SHA256.'
    report=json.loads((ROOT/'reports/v032.json').read_text(encoding='utf-8'))
    assert len(report)==3 and all(not item['closure']['open_edges'] for item in report)
    for log,marker in [('sectioned_interiors.log','V032_PASSED'),('room_process.log','ROOM_PROCESS_PASSED'),('room_reopen.log','ROOM_REOPEN_PASSED'),('physics_demo.log','PHYSICS_DEMO_PASSED'),('demo_reopen.log','DEMO_REOPEN_PASSED'),('tile_fit.log','TILE_FIT_PASSED'),('roof_v032_after.log','ROOF_SURFACE_PASSED')]:
        assert marker in (ROOT/'reports'/log).read_text(encoding='utf-8',errors='replace')
    files=['dist/ruinas_panel_v0324.zip','dist/ruina_v032.blend','reports/v032_exterior.png','reports/v032_interior.png','reports/v032_worn.png','reports/v032.json','docs/V032.md','docs/DESTRUCTION_STUDY.md','docs/V0322.md','reports/precision_comparison.json','reports/partition_sections.json','reports/physics_readiness.json','docs/V0323.md','reports/profile_options.json','reports/physics_lab.png','dist/ruinas_physics_lab.blend','docs/V0324.md','reports/room_process.json','reports/room_reopen.json','reports/material_relief.png','reports/room_physics_result.png','dist/ruinas_v0324_proceso_completo.blend','dist/ruinas_v0324_proceso_completo.stl','dist/ruinas_v0324_fisica_interactiva.blend','docs/MANUAL_FISICA.md','dist/Manual_Ruinas_Fisica.html','reports/physics_demo.json','reports/demo_reopen.json']
    manifest={}
    target=ROOT/'dist/ruinas_v0324_completo.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for item in files:
            path=ROOT/item;data=path.read_bytes();archive.writestr(path.name,data)
            manifest[path.name]=hashlib.sha256(data).hexdigest()
        archive.writestr('SHA256.json',json.dumps(manifest,indent=2))
        archive.writestr('LEEME.txt','Ruinas 0.32.4. Instala ruinas_panel_v0324.zip y abre ruinas_v0324_fisica_interactiva.blend; pulsa Espacio para ver la caída. Consulta Manual_Ruinas_Fisica.html.\nLa vista interior es un recorte de inspección; el blend conserva la casa completa.\nConsulta V0324.md para validación y límites de impresión.\n')
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('BUNDLE_PASSED',target)


if __name__=='__main__':run()
