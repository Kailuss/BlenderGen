"""Esquema común SI/mm; ningún valor desconocido se sustituye por resistencia ficticia."""
import math
from .. import config_materials
from . import materials

VERSION=3
UNITS={'length':'mm','volume':'mm3','area':'mm2','mass':'kg','load':'N','capacity':'N','density':'kg/m3','moment':'N*mm','energy':'J','pressure':'kPa','pressure_impulse':'kPa*s'}


def element(identifier,kind,material=None,volume_mm3=None,**properties):
    'IA: Recibe volumen de MUNDO en mm³; masa real sin escala Bullet, magnitudes desconocidas explícitas y partición de impresión independiente; modelo debe pasar por units.to_world.'
    if material is not None and material not in config_materials.MECHANICAL:raise ValueError('Material sin registrar: '+material)
    if volume_mm3 is not None and (not math.isfinite(volume_mm3) or volume_mm3<0):raise ValueError('Volumen inválido')
    mass=None if material is None or volume_mm3 is None or materials.density(material) is None else volume_mm3*1e-9*materials.density(material)
    return {'id':identifier,'kind':kind,'material':material,'volume_mm3':volume_mm3,'mass_kg':mass,
            'rests_on':[],'load_N':None,'capacity_N':None,'fragility_class':None,'exposed_area_mm2':None,
            'pozo_de_colapso':False,'collapse_override':'AUTO','representation':'semantic','print_parts':[],'properties':properties,
            'quantity_frame':'world','demanda_lateral_N':None,'lateral_direction':None,'braced_by':[],
            'capacity_by_mode':{'compression_N':None,'tension_N':None,'shear_N':None,'bending_Nmm':None},
            'energy_absorption_J':None,'failure_mode':None}


def synchronise_supports(model):
    'IA: rests_on es una vista derivada de SUPPORTED_BY; nunca una segunda fuente editable de dependencias.'
    supports={e['id']:set() for e in model['elements']}
    for r in model['relations']:
        if r['kind']=='SUPPORTED_BY' and r['source'] in supports:supports[r['source']].add(r['target'])
    for e in model['elements']:e['rests_on']=sorted(supports[e['id']])
    for e in model['elements']:e['braced_by']=sorted({r['target'] for r in model['relations'] if r['source']==e['id'] and r['kind']=='ARRIOSTRADO_POR'})


def validate(model):
    'IA: Verifica esquema común, unidades y magnitudes finitas; detecta masa incoherente y divergencia entre rests_on y relaciones.'
    issues=[]
    if model.get('schema')!=VERSION or model.get('units')!=UNITS:issues.append({'code':'SCHEMA_OR_UNITS_MISMATCH'})
    expected={e['id']:set() for e in model['elements']}
    for r in model['relations']:
        if r['kind']=='SUPPORTED_BY' and r['source'] in expected:expected[r['source']].add(r['target'])
        for contact in r.get('contacts',[]):
            for field in ('area_mm2','seat_mm','load_share'):
                value=contact.get(field)
                if value is not None and (not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or value<0 or (field=='load_share' and value>1)):
                    issues.append({'code':'INVALID_CONTACT','relation':r['id'],'field':field})
            point=contact.get('point_mm')
            if point is not None and (not isinstance(point,(list,tuple)) or len(point)!=3 or not all(isinstance(v,(float,int)) and math.isfinite(v) for v in point)):
                issues.append({'code':'INVALID_CONTACT_POINT','relation':r['id']})
    fields=set(element('_','_'))
    for e in model['elements']:
        key=e['id']
        if fields-set(e):issues.append({'code':'MISSING_SCHEMA_FIELDS','element':key,'fields':sorted(fields-set(e))});continue
        for field in ('volume_mm3','mass_kg','load_N','capacity_N','exposed_area_mm2','demanda_lateral_N','energy_absorption_J'):
            v=e[field]
            if v is not None and (not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<0):issues.append({'code':'INVALID_QUANTITY','element':key,'field':field})
        if e['material'] is not None and e['material'] not in config_materials.MECHANICAL:issues.append({'code':'UNKNOWN_MATERIAL','element':key})
        elif e['material'] is not None and isinstance(e['volume_mm3'],(int,float)):
            rho=materials.density(e['material'])
            if rho is None:issues.append({'code':'UNKNOWN_DENSITY','element':key});continue
            mass=e['volume_mm3']*1e-9*rho
            if not isinstance(e['mass_kg'],(int,float)) or not math.isclose(e['mass_kg'],mass,rel_tol=1e-9,abs_tol=1e-12):issues.append({'code':'INCONSISTENT_MASS','element':key})
        if e['rests_on']!=sorted(expected[key]):issues.append({'code':'DIVERGENT_SUPPORTS','element':key})
        if e['quantity_frame']!='world':issues.append({'code':'AMBIGUOUS_SCALE','element':key})
        modes=e['capacity_by_mode']
        required_modes={'compression_N','tension_N','shear_N','bending_Nmm'}
        if not isinstance(modes,dict) or set(modes)!=required_modes:issues.append({'code':'INVALID_CAPACITY_MODES','element':key})
        elif any(v is not None and (not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<0) for v in modes.values()):issues.append({'code':'INVALID_CAPACITY_VALUE','element':key})
        direction=e['lateral_direction']
        if direction is not None:
            valid=isinstance(direction,(tuple,list)) and len(direction)==3 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in direction)
            if not valid or not math.isclose(sum(v*v for v in direction),1,abs_tol=1e-6):issues.append({'code':'INVALID_LATERAL_DIRECTION','element':key})
        elif e['demanda_lateral_N'] not in (None,0):issues.append({'code':'MISSING_LATERAL_DIRECTION','element':key})
        braces=sorted({r['target'] for r in model['relations'] if r['source']==key and r['kind']=='ARRIOSTRADO_POR'})
        if e['braced_by']!=braces:issues.append({'code':'DIVERGENT_BRACING','element':key})
        if e['collapse_override'] not in ('AUTO','ALLOW','BLOCK'):issues.append({'code':'INVALID_COLLAPSE_OVERRIDE','element':key})
        if not isinstance(e['pozo_de_colapso'],bool):issues.append({'code':'INVALID_COLLAPSE_WELL','element':key})
    return issues
