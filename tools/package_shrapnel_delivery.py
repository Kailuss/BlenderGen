"""Empaqueta únicamente la entrega verificada y sus dependencias de render."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/Ejercicio02_metralla_20261028'


def run():
    'IA: Exige los informes y archivos finales, crea manifiesto de tamaño/hash y ZIP con rutas relativas; excluye escenas intermedias y diagnósticos.'
    verified=ROOT/'reports/ejercicio02_delivery_verified.json'
    assert verified.is_file()
    with (OUT/'05_render_listo.blend').open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==json.loads(verified.read_text(encoding='utf8'))['blend_sha256'],'La escena cambió después de verificarse.'
    files=[OUT/name for name in ('05_render_listo.blend','LEEME.md','Render_GPU.cmd','Render_GPU.py','impactos.json','render_config.json','Vista_previa.png')]
    files+=sorted(p for p in (OUT/'cache/humo').rglob('*') if p.is_file())
    assert all(p.is_file() for p in files) and any(p.suffix=='.vdb' for p in files)
    records=[]
    for path in files:
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        records.append(dict(path=path.relative_to(OUT).as_posix(),bytes=path.stat().st_size,sha256=digest.hexdigest()))
    manifest=OUT/'MANIFEST.json';manifest.write_text(json.dumps(dict(files=records),indent=2),encoding='utf8')
    target=ROOT/'dist/Ejercicio02_metralla_entrega_20261102.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
        for path in [*files,manifest]:archive.write(path,'Ejercicio02_metralla/'+path.relative_to(OUT).as_posix())
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('DELIVERY_PACKAGED',str(target),target.stat().st_size,flush=True)


if __name__=='__main__':run()
