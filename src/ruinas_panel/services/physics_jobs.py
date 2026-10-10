"""Simulación aislada: un fallo nativo no debe cerrar la sesión de edición."""
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
import bpy
from .. import runtime,config


def start(scene,mode='SIMULATE',export_path=''):
    'IA: Guarda una copia del laboratorio y arranca otro Blender sin ventana; no evalúa Bullet en la sesión del usuario.'
    if runtime.physics_job:raise ValueError('Ya hay una simulación en curso.')
    if not (mode=='PREPARE' or scene.get('ruinas_physics_lab') or (mode=='EXPORT' and scene.get('physics_result_scene'))):raise ValueError('Abre un laboratorio físico.')
    folder=Path(tempfile.mkdtemp(prefix='ruinas_physics_'))
    source=folder/'input.blend';output=folder/'result.blend';progress=folder/'progress.json'
    bpy.data.libraries.write(str(source),{scene},fake_user=True)
    command=[bpy.app.binary_path,'--factory-startup','--threads','2','-b',str(source),'--python-exit-code','1','--python',str(Path(__file__).with_name('physics_worker.py')),'--',str(output),str(progress),scene.name,mode,str(export_path)]
    with (folder/'worker.log').open('w',encoding='utf8') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    runtime.physics_job={'process':process,'folder':folder,'output':output,'progress':progress,'started':time.monotonic(),'scene':scene.name,'mode':mode}
    return runtime.physics_job


def memory_mb(pid):
    'IA: Consulta memoria residente del proceso hijo en Windows o Linux; si no se puede medir devuelve cero sin alterar procesos ajenos.'
    if os.name!='nt':
        try:return int(Path('/proc/%s/statm'%pid).read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')/1048576
        except (OSError,ValueError):return 0
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(key,ctypes.c_size_t) for key in ('peak','rss','peak_pool','pool','peak_nonpool','nonpool','pagefile','peak_pagefile')]
    kernel=ctypes.windll.kernel32;kernel.OpenProcess.restype=wintypes.HANDLE
    handle=kernel.OpenProcess(0x410,False,pid)
    if not handle:return 0
    try:
        values=Counters();values.cb=ctypes.sizeof(values)
        okay=ctypes.windll.psapi.GetProcessMemoryInfo(wintypes.HANDLE(handle),ctypes.byref(values),values.cb)
        return values.rss/1048576 if okay else 0
    finally:kernel.CloseHandle(wintypes.HANDLE(handle))


def cancel():
    'IA: Cancela exclusivamente el hijo creado por esta sesión y conserva el checkpoint y log para diagnóstico.'
    job=runtime.physics_job
    if job and job['process'].poll() is None:job['process'].terminate()
    runtime.physics_job=None


def poll():
    'IA: Vigila tiempo y memoria del hijo; devuelve progreso o escena terminada, y conserva diagnóstico si falla.'
    job=runtime.physics_job
    if not job:raise ValueError('No hay simulación en curso.')
    process=job['process'];code=process.poll()
    if code is None:
        elapsed=time.monotonic()-job['started'];memory=memory_mb(process.pid)
        if elapsed>config.PHYSICS_JOB_SECONDS or memory>config.PHYSICS_JOB_MEMORY_MB:
            folder=job['folder']
            details={'mode':job['mode'],'seconds':elapsed,'resident_mb':memory,'limit_seconds':config.PHYSICS_JOB_SECONDS,'limit_mb':config.PHYSICS_JOB_MEMORY_MB}
            cancel()
            (folder/'resource_limit.json').write_text(json.dumps(details,indent=2),encoding='utf8')
            raise ValueError('Proceso detenido por límite de recursos (%.0f MB, %.0f s). Fuente intacta. Diagnóstico: %s'%(memory,elapsed,folder))
        try:return json.loads(job['progress'].read_text(encoding='utf8'))
        except (OSError,ValueError):return {'stage':'Arrancando proceso separado'}
    runtime.physics_job=None
    if code or not job['output'].exists():raise ValueError('El proceso físico falló (código %s); la sesión se conserva. Log: %s'%(code,job['folder']/'worker.log'))
    with bpy.data.libraries.load(str(job['output']),link=False) as (data,loaded):loaded.scenes=data.scenes
    result=loaded.scenes[0]
    if job['mode']=='SIMULATE':result['lab_scene']=job['scene']
    return {'finished':result}
