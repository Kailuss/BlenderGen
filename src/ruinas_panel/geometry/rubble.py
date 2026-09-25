"""geometry /rubble — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from ..geometry import fracture
from ..geometry import primitives
from ..geometry import terrain
from ..geometry import weather
from ..structure import layout
from mathutils import Euler
from mathutils import Vector
import bpy
import math
import numpy
import random


def build_rubble(coll,stone,mortar,p,door,rh):
    'IA: Crea cúmulos y asienta cada pieza sobre el terreno; actualiza metadatos de apoyo.'
    L,T=p.length,p.thickness
    dseed=layout.distribution_seed(p)
    amount=p.rubble_amount
    soil=primitives.material('Tierra · arena',(.36,.31,.24))
    audit=[]
    for i,(dx,side) in enumerate(((-10,-1),(11,-1),(0,1))):
        rr=random.Random(dseed+3300+i)
        rx=rh*(1.18+.62*amount)
        ry=5.5+4*amount
        x=max(-L/2+rx,min(L/2-rx,(p.break_position-.5)*L+dx))
        if door:
            intervals=[(-L/2+rx,door['left']-rx-1),(door['right']+rx+1,L/2-rx)]
            candidates=[max(a,min(b,x)) for a,b in intervals if a<=b]
            if not candidates:
                continue
            x=min(candidates,key=lambda q:abs(q-x))
        y=side*(T/2+ry*.52)
        mound_height=1.5+amount*rh*.65
        pad,surface=terrain.earth_patch(coll,soil,'Tierra · cúmulo %s'%i,x,y,rx,ry,mound_height,dseed+2200+i,p.ground_roughness)
        count=1+round(10*amount)
        audit.append({'x':x,'y':y,'groups':count,'height':mound_height})
        for j in range(count):
            ang=rr.uniform(-math.pi,math.pi)
            # Depósito radial: piezas grandes abajo, pequeñas hacia la cima.
            radius=.72*math.sqrt((count-j-.5)/count) if count>1 else 0
            a=rr.random()*math.tau
            cx=x+rx*radius*math.cos(a)
            cy=y+ry*radius*math.sin(a)
            scale=rr.uniform(.65,1.03)*(1-.3*j/max(1,count))
            before=set(coll.objects)
            if j%3==1:
                w=rh*1.7*scale
                d=rh*.72*scale
                h=rh*.58*scale
                ob=primitives.block('Piedra caída · entera %s.%s'%(i,j),-w/2,w/2,-d/2,d/2,0,h,coll,stone)
                weather.weather_stone(ob,p.wear*.7,dseed+i*91+j)
                rot=Euler((rr.uniform(-.22,.22),rr.uniform(-.22,.22),ang)).to_matrix()
                co=primitives.coords(ob)@numpy.array(rot).T
                co[:,0]+=cx
                co[:,1]+=cy
                primitives.set_coords(ob,co)
            else:
                fracture.broken_stone(coll,stone,cx,cy,ang,rh*1.6*scale,rh*.78*scale,rh*.62*scale,dseed+3300+i*117+j,p.wear)
            for ob in set(coll.objects)-before:
                # Enterrar el punto de contacto en la superficie real del montículo.
                terrain.settle_rubble(ob,surface)
                ob['escombro']=True
        terrain.gravel_batch(coll,stone,'Grava · cúmulo %s'%i,x,y,rx,ry,surface,round(12+amount*45+p.ground_roughness*12),dseed+9400+i)
    meta.put(bpy.context.scene,'escombros_generados',audit)
