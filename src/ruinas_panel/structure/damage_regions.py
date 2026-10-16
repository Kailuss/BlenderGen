"""Regiones de daño puras: un mismo contorno para pérdida de apoyo y acabado."""
import math
import random
from .. import config


def roof_events(seed,damage_seed,amount,bounds):
    'IA: Define dos eventos deterministas, descentrados en ambos ejes, con contorno trapezoidal redondeado irregular; no crea mallas ni consume azar global.'
    if amount<=0:return []
    xa,xb,ya,yb=bounds;span=xb-xa;depth=yb-ya
    rng=random.Random(seed+46301+damage_seed*104729);events=[]
    for side in range(2):
        x=xa+span*((.23 if side==0 else .76)+rng.uniform(-.035,.035))
        y=ya+depth*((.22 if side==0 else .60)+rng.uniform(0,.17))
        events.append({'id':'roof.damage.%s'%side,'type':'ROOF_SUPPORT_LOSS','side':side,'x':x,'y':y,
                       'rx':span*(.045+.13*amount)*rng.uniform(.9,1.08),'ry':depth*(.045+.17*amount)*rng.uniform(.9,1.08),
                       'severity':amount,'bounds':list(bounds),'shape':'rounded_trapezoid','angle':rng.uniform(-.16,.16),
                       'taper':rng.uniform(.10,.23)*(-1 if side else 1),'shear':rng.uniform(-.15,.15),'phase':rng.uniform(0,math.tau)})
    return events


def radius(x,y,event):
    'IA: Radio normalizado continuo de superelipse deformada; admite eventos elípticos heredados sin cambiar su interpretación.'
    u=(x-event['x'])/event['rx'];v=(y-event['y'])/event['ry']
    if event.get('shape')!='rounded_trapezoid':return math.hypot(u,v)
    angle=event['angle'];u,v=u*math.cos(angle)+v*math.sin(angle),-u*math.sin(angle)+v*math.cos(angle)
    u=(u-event['shear']*v)/max(.65,1+event['taper']*max(-1,min(1,v)))
    theta=math.atan2(v,u);phase=event['phase']
    irregular=1+.075*math.sin(3*theta+phase)+.035*math.sin(5*theta-phase)
    return (u**4+v**4)**.25/irregular


def core(event):
    'IA: Conserva la primera etapa de hundimiento hasta 45%; la pérdida de material crece después sin saltar a un boquete completo.'
    return max(0,(event.get('severity',1)-.45)/.55)


def broken(x,y,events):
    'IA: Consulta el mismo núcleo de pérdida para madera y tejas; no añade ruido independiente por material.'
    return any(radius(x,y,event)<core(event) for event in events)


def segments(a,b,fixed,events,axis):
    'IA: Intersecta el contorno común con un elemento lineal, refina cruces por bisección y conserva solo extremos anclados de más de 2 mm.'
    low,high=sorted((a,b))
    if not events:return [(low,high)]
    def inside(value):
        'IA: Evalúa la sección horizontal o vertical del daño compartido.'
        return broken(value,fixed,events) if axis=='x' else broken(fixed,value,events)
    count=max(1,math.ceil((high-low)/config.ROOF_DAMAGE_SAMPLE_MM));cuts=[low]
    previous=low;state=inside(low)
    for i in range(1,count+1):
        value=low+(high-low)*i/count;now=inside(value)
        if state!=now:
            left,right=previous,value
            for _ in range(14):
                middle=(left+right)/2
                if inside(middle)==state:left=middle
                else:right=middle
            cuts.append((left+right)/2)
        previous=value;state=now
    cuts.append(high)
    return [(x,y) for x,y in zip(cuts,cuts[1:]) if y-x>2 and not inside((x+y)/2) and (abs(x-low)<1e-6 or abs(y-high)<1e-6)]
