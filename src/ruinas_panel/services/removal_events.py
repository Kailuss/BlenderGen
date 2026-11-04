"""Puente de operaciones geométricas confirmadas al registro causal."""
import hashlib
from .. import runtime,meta
from ..geometry import primitives
from ..construction_core import identifiers
from ..construction_core.removal_ledger import RemovalLedger


def begin(coll,scene):
    'IA: Inventaría fuente al entrar en assembly, antes de derrumbe/huecos; no identifica retrospectivamente retiradas por diferencias de malla final.'
    ledger=RemovalLedger()
    for ob in coll.objects:
        key=identifiers.piece(ob.get('wall_id','front'),ob.name)
        ledger.register(key,{'source_name':ob.name,'source_key':primitives.piece_key(ob),'wall':ob.get('wall_id','front')})
        ob['construction_id']=key
    runtime.removal_ledger=ledger;runtime.removal_scene=scene
    flush()


def flush():
    'IA: Persiste inventario y eventos completos en meta; no borra el último registro al cerrar sesión.'
    ledger=getattr(runtime,'removal_ledger',None)
    if ledger is not None:meta.put(runtime.removal_scene,'removal_ledger',ledger.dump())


def end():
    'IA: Guarda registro y libera referencias de escena incluso cuando finaliza la generación con error.'
    flush();runtime.removal_ledger=None;runtime.removal_scene=None


def record(key,operation,cause,details=None):
    'IA: Registra solo piezas del inventario de assembly; las piezas creadas después no se presentan como fuente inicial.'
    ledger=getattr(runtime,'removal_ledger',None)
    if ledger is not None and key in ledger.elements:ledger.record(key,operation,cause,details)


def remove(objects,cause):
    'IA: Captura IDs antes de destruir y confirma eventos después de una retirada que termina correctamente.'
    objects=list(objects);keys=[ob.get('construction_id') for ob in objects]
    primitives.remove_objects(objects)
    for key in keys:record(key,'REMOVE',cause)
    flush()


def fingerprint(ob):
    'IA: Huella temporal para distinguir recorte confirmado de no-op/reversión; no decide apoyos.'
    return hashlib.sha256(primitives.coords(ob).tobytes()).hexdigest()


def cut_confirmed(ob,before,cause,details):
    'IA: Anota modificación solo si cambió la geometría; conserva parámetros de la operación, sin suponer retirada completa.'
    if fingerprint(ob)!=before:record(ob.get('construction_id'),'CUT',cause,details)


def clip(ob,point,normal,cause):
    'IA: Ejecuta el corte plano heredado y registra el plano si hubo cambio real.'
    before=fingerprint(ob);primitives.clip_closed(ob,point,normal)
    cut_confirmed(ob,before,cause,{'point':list(point),'normal':list(normal),'keep':'inner'})
