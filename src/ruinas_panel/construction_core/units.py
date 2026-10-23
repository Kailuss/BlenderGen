"""Frontera única entre dimensiones de miniatura y mundo representado."""
import math


def to_world(value,dimension,model_scale):
    'IA: Convierte magnitud geométrica de modelo a mundo (mm, mm² o mm³); escala explícita positiva, independiente de Bullet.'
    if dimension not in (1,2,3):raise ValueError('Dimensión geométrica inválida')
    if not isinstance(model_scale,(int,float)) or isinstance(model_scale,bool) or not math.isfinite(model_scale) or model_scale<=0:raise ValueError('Falta escala modelo/mundo válida')
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or value<0:raise ValueError('Magnitud geométrica inválida')
    return value*model_scale**dimension


def event(peak_kpa,impulse_kpa_s,direction):
    'IA: Registra presión e integral temporal separadas en unidades de mundo; no deduce daño ni duración a partir del pico.'
    for value in (peak_kpa,impulse_kpa_s):
        if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or value<0:raise ValueError('Presión/impulso inválido')
    if len(direction)!=3 or not all(math.isfinite(v) for v in direction):raise ValueError('Dirección inválida')
    length=math.sqrt(sum(v*v for v in direction))
    if length==0:raise ValueError('Dirección nula')
    return {'peak_kpa':peak_kpa,'impulse_kpa_s':impulse_kpa_s,'direction':[v/length for v in direction],'frame':'world'}
