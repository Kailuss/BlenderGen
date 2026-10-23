"""Lectura del catálogo y modificadores puros, sin calibración implícita de Bullet."""
import hashlib
import json
import math
import random
from .. import config,config_materials as data


def record(value,unit,range_values=None):
    'IA: Conserva confianza C y procedencia por campo; None es desconocido, nunca capacidad infinita.'
    return {'value':value,'range':list(range_values) if range_values is not None else None,'unit':unit,'confidence':'C','source':data.SOURCE}


def catalog():
    'IA: Expone ambas tablas y modificadores sin inventar valores ausentes ni aplicar umbrales de evento al solucionador.'
    result={}
    for key,raw in data.MECHANICAL.items():
        row={'density_ref':raw['density_ref'],'structural':key not in ('GLASS','PLASTER','JOINERY','TILE_CLAY')}
        row['density_kg_m3']=record(config.PHYSICS_DENSITIES.get(raw['density_ref']),'kg/m3')
        row['density_kg_m3']['source']='config.PHYSICS_DENSITIES; correspondencia provisional no contrastada'
        for field in ('compression','tension','shear','bending','bearing','friction'):
            entry=raw.get(field);row[field]=record(entry[0] if entry else None,'1' if field=='friction' else 'MPa',entry[1:] if entry else None)
        event=data.EVENT.get(key)
        row['fragility']=record(event[0] if event else None,'class')
        row['peak_kpa']=record(None,'kPa',event[1] if event else None)
        row['impulse_kpa_s']=record(None,'kPa*s')
        row['dominant_mode']=record(event[2] if event else None,'mode')
        row['restitution']=record(event[3] if event else None,'1')
        row['age_factor']=record(None,'1',data.AGE_RANGES.get(key))
        row['variability_cv']=record(data.VARIABILITY_CV.get(key),'1')
        result[key]=row
    return result


def signature():
    'IA: Firma estable de valores, densidades referidas, unidades, rangos y fuentes; los consumidores la usan para invalidar caché.'
    payload={'version':data.VERSION,'materials':catalog()}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,allow_nan=False).encode('utf8')).hexdigest()


def variability(seed,element_id,cv):
    'IA: Lognormal de media uno antes de truncar, normal latente truncada a ±2 sigma; SHA256 estable, sin random global ni muestreo por fragmento.'
    if not math.isfinite(cv) or cv<0:raise ValueError('CV inválido')
    if cv==0:return 1.0
    digest=hashlib.sha256(json.dumps([seed,element_id],ensure_ascii=False).encode('utf8')).digest()
    rng=random.Random(int.from_bytes(digest,'big'));sigma=math.sqrt(math.log1p(cv*cv))
    while True:
        z=rng.gauss(0,1)
        if -2<=z<=2:return math.exp(-sigma*sigma/2+sigma*z)


def acceptance(material,fields):
    'IA: Un camino crítico desconocido o C no pasa silenciosamente; devuelve campos ausentes y recuento provisional.'
    row=catalog()[material];unknown=[];provisional=[]
    for field in fields:
        entry=row.get(field)
        if not entry or entry['value'] is None:unknown.append(field)
        if entry and entry['confidence']=='C':provisional.append(field)
    return {'accepted':not unknown and not provisional,'unknown':unknown,'class_C':provisional,'class_C_count':len(provisional)}
