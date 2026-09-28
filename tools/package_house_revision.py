"""Empaqueta la revisión de la casa sin sustituir el ZIP aportado como referencia."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def run():
    """IA: empaqueta artefactos verificados y sumas SHA256; exige informe de conducto/caché y conserva la entrada original."""
    report=json.loads((ROOT/'reports/house_revision.json').read_text(encoding='utf-8'))
    assert report['cache_identical'] and report['wood_passage_clear']
    assert not report['closure']['open_edges']
    files={
        'ruina_v031_revisada.blend':'dist/ruina_v031_revisada.blend',
        'ruinas_panel_v031.zip':'dist/ruinas_panel_v031.zip',
        'exterior.png':'reports/house_after.png',
        'hogar.png':'reports/house_fireplace.png',
        'escalera.png':'reports/stairs_surface_full.png',
        'detalle_huellas.png':'reports/stairs_surface_comparison.png',
        'metricas_y_pruebas.json':'reports/house_revision.json',
        'VALIDACION.md':'docs/HOUSE_REVISION.md',
    }
    readme=('RUINAS 0.31 — CASA REVISADA\n\n'
            'Abre ruina_v031_revisada.blend para ver la casa.\n'
            'Para editar parámetros y regenerar, instala ruinas_panel_v031.zip en Blender; '
            'mantén una sola versión del complemento activa. Panel Vista 3D > N > Ruinas.\n'
            'La actualización automática está apagada al abrir esta entrega; usa Actualizar.\n\n'
            'Chimenea desde planta baja con hogar abierto y conducto continuo; tejas de media '
            'caña, hastiales con entramado y huellas de piedra con relieve.\n'
            'Los archivos originales del usuario se conservan. Esta escena usa el addon '
            'instalado, sin activador Python embebido de la versión anterior.\n\n'
            'Incluye geometría procedural, no un sólido fusionado para imprimir. Las '
            'limitaciones heredadas de exportación están descritas en VALIDACION.md.\n')
    target=ROOT/'dist/ruinas_v031_revisada_completo.zip'
    sums=[]
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,path in files.items():
            data=(ROOT/path).read_bytes();archive.writestr(name,data)
            sums.append(hashlib.sha256(data).hexdigest()+'  '+name)
        archive.writestr('LEEME.txt',readme.encode('utf-8'))
        archive.writestr('SHA256SUMS.txt','\n'.join(sums)+'\n')
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('HOUSE_PACKAGED',target,target.stat().st_size)


if __name__=='__main__':run()
