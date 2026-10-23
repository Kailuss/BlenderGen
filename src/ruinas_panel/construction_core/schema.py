"""Esquema común SI/mm; ningún valor desconocido se sustituye por resistencia ficticia."""
import math
from .. import config

VERSION=2
UNITS={'length':'mm','volume':'mm3','area':'mm2','mass':'kg','load':'N','capacity':'N','density':'kg/m3'}


def element(identifier,kind,material=None,volume_mm3=None,**properties):
    'IA: Crea elemento físico o semántico con campos comunes; masa real sin escala Bullet, magnitudes desconocidas explícitas y partición de impresión independiente.'
    if material is not None and material not in config.PHYSICS_DENSITIES:raise ValueError('Material sin registrar: '+material)
    if volume_mm3 is not None and (not math.isfinite(volume_mm3) or volume_mm3<0):raise ValueError('Volumen inválido')
    mass=None if material is None or volume_mm3 is None else volume_mm3*1e-9*config.PHYSICS_DENSITIES[material]
    return {'id':identifier,'kind':kind,'material':material,'volume_mm3':volume_mm3,'mass_kg':mass,
            'rests_on':[],'load_N':None,'capacity_N':None,'fragility_class':None,'exposed_area_mm2':None,
            'pozo_de_colapso':False,'representation':'semantic','print_parts':[],'properties':properties}


def synchronise_supports(model):
    'IA: rests_on es una vista derivada de SUPPORTED_BY; nunca una segunda fuente editable de dependencias.'
    supports={e['id']:set() for e in model['elements']}
    for r in model['relations']:
        if r['kind']=='SUPPORTED_BY' and r['source'] in supports:supports[r['source']].add(r['target'])
    for e in model['elements']:e['rests_on']=sorted(supports[e['id']])


def validate(model):
    'IA: Verifica esquema común, unidades y magnitudes finitas; detecta masa incoherente y divergencia entre rests_on y relaciones.'
    issues=[]
    if model.get('schema')!=VERSION or model.get('units')!=UNITS:issues.append({'code':'SCHEMA_OR_UNITS_MISMATCH'})
    expected={e['id']:set() for e in model['elements']}
    for r in model['relations']:
        if r['kind']=='SUPPORTED_BY' and r['source'] in expected:expected[r['source']].add(r['target'])
    fields=set(element('_','_'))
    for e in model['elements']:
        key=e['id']
        if fields-set(e):issues.append({'code':'MISSING_SCHEMA_FIELDS','element':key,'fields':sorted(fields-set(e))});continue
        for field in ('volume_mm3','mass_kg','load_N','capacity_N','exposed_area_mm2'):
            v=e[field]
            if v is not None and (not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<0):issues.append({'code':'INVALID_QUANTITY','element':key,'field':field})
        if e['material'] is not None and e['material'] not in config.PHYSICS_DENSITIES:issues.append({'code':'UNKNOWN_MATERIAL','element':key})
        elif e['material'] is not None and isinstance(e['volume_mm3'],(int,float)):
            mass=e['volume_mm3']*1e-9*config.PHYSICS_DENSITIES[e['material']]
            if not isinstance(e['mass_kg'],(int,float)) or not math.isclose(e['mass_kg'],mass,rel_tol=1e-9,abs_tol=1e-12):issues.append({'code':'INCONSISTENT_MASS','element':key})
        if e['rests_on']!=sorted(expected[key]):issues.append({'code':'DIVERGENT_SUPPORTS','element':key})
        if not isinstance(e['pozo_de_colapso'],bool):issues.append({'code':'INVALID_COLLAPSE_WELL','element':key})
    return issues
