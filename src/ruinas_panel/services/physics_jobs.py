"""Simulación aislada: un fallo nativo no debe cerrar la sesión de edición."""
import json
import hashlib
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
    worker=Path(__file__).with_name('physics_worker.py')
    (folder/'job.json').write_text(json.dumps({'build':config.BUILD_ID,'mode':mode,'worker':str(worker),'worker_sha256':hashlib.sha256(worker.read_bytes()).hexdigest(),'memory_limit_mb':scene.ruin_settings.physics_memory_mb,'time_limit_seconds':scene.ruin_settings.physics_timeout_seconds},indent=2),encoding='utf8')
    command=[bpy.app.binary_path,'--factory-startup','--threads','2','-b',str(source),'--python-exit-code','1','--python',str(Path(__file__).with_name('physics_worker.py')),'--',str(output),str(progress),scene.name,mode,str(export_path)]
    with (folder/'worker.log').open('w',encoding='utf8') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    runtime.physics_job={'process':process,'folder':folder,'output':output,'progress':progress,'started':time.monotonic(),'scene':scene.name,'mode':mode,'memory_limit_mb':scene.ruin_settings.physics_memory_mb,'time_limit_seconds':scene.ruin_settings.physics_timeout_seconds}
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
        memory_limit=job.get('memory_limit_mb',config.PHYSICS_JOB_MEMORY_MB);time_limit=job.get('time_limit_seconds',config.PHYSICS_JOB_SECONDS)
        if elapsed>time_limit or memory>memory_limit:
            folder=job['folder']
            details={'mode':job['mode'],'seconds':elapsed,'resident_mb':memory,'limit_seconds':time_limit,'limit_mb':memory_limit}
            cancel()
            (folder/'resource_limit.json').write_text(json.dumps(details,indent=2),encoding='utf8')
            raise ValueError('Límite configurado de Ruinas: %.0f/%.0f MB, %.0f/%.0f s. Fuente intacta. Diagnóstico: %s'%(memory,memory_limit,elapsed,time_limit,folder))
        try:return json.loads(job['progress'].read_text(encoding='utf8'))
        except (OSError,ValueError):return {'stage':'Arrancando proceso separado'}
    runtime.physics_job=None
    if code or not job['output'].exists():
        log=job['folder']/'worker.log'
        details=log.read_text(encoding='utf8',errors='replace')[-20000:] if log.exists() else ''
        reason=next((line.split(': ',1)[-1] for line in reversed(details.splitlines()) if line.startswith(('ValueError:','RuntimeError:','MemoryError:','PermissionError:'))),'código %s'%code)
        raise ValueError('Preparación/cálculo fallido: %s. Fuente intacta. Log: %s'%(reason,log))
    with bpy.data.libraries.load(str(job['output']),link=False) as (data,loaded):loaded.scenes=data.scenes
    result=loaded.scenes[0]
    if job['mode']=='SIMULATE':result['lab_scene']=job['scene']
    return {'finished':result}
