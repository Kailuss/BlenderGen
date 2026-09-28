"""Planificación espacial pura: derrumbes, huecos del forjado y perfil de cubierta."""
import math
import random


def impacts(p):
    'IA: Centros compactos por fachada en mm; comparten campo en esquinas y no rebajan uniformemente toda la coronación.'
    seed=p.distribution_seed if p.lock_distribution else p.seed
    rng=random.Random(seed+27103)
    depth=p.building_depth+p.thickness/2+3.42
    half=p.length/2-(p.thickness+p.projection*1.5+.8)/2
    x=(p.break_position-.5)*p.length
    return [(x,0,p.length*.25,max(16,depth*.33)),
            ((rng.uniform(-.24,.24))*p.length,depth,p.length*.24,max(16,depth*.36)),
            (-half,depth*rng.uniform(.36,.62),max(16,p.length*.16),depth*.34),
            (half,depth*rng.uniform(.35,.68),max(16,p.length*.16),depth*.34)]


def collapse_height(p,x,y):
    'IA: Pérdida monótona con Derrumbe, acotada al pie de 4 mm; cero fuera de los impactos compactos.'
    strength=0
    for cx,cy,rx,ry in impacts(p):
        d=((x-cx)/rx)**2+((y-cy)/ry)**2
        strength=max(strength,max(0,1-d)**.65)
    return p.height-min(1,p.collapse*1.15)*(p.height-4)*strength


def floor_holes(p,bounds,level):
    'IA: Elipses localizadas, dependientes de nivel y semilla; nunca una supresión aleatoria de tablones enteros.'
    xmin,xmax,ymin,ymax=bounds;w=xmax-xmin;d=ymax-ymin
    rng=random.Random(p.seed+9721+level*1709)
    holes=[]
    if p.floor_damage>0:
        for i in range(2):
            holes.append((xmin+w*(.3+i*.4),ymin+d*rng.uniform(.32,.68),w*(.035+.12*p.floor_damage),d*(.05+.22*p.floor_damage)))
    if p.collapse>0:
        scale=(.25+.75*level)*p.collapse
        for x,y,rx,ry in impacts(p):
            holes.append((x,y,rx*scale*.7,ry*scale*.85))
    return holes


def cut_intervals(a,b,y,holes,rectangle=None):
    'IA: Resta uniones de elipses y hueco rectangular a un tablón; devuelve tramos ordenados sin solapamiento.'
    cuts=[]
    for cx,cy,rx,ry in holes:
        q=(y-cy)/max(ry,.001)
        if abs(q)<1:
            reach=rx*math.sqrt(1-q*q);cuts.append((cx-reach,cx+reach))
    if rectangle and rectangle[2]<y<rectangle[3]:cuts.append(tuple(rectangle[:2]))
    pieces=[(a,b)]
    for lo,hi in sorted(cuts):
        result=[]
        for x0,x1 in pieces:
            if hi<=x0 or lo>=x1:result.append((x0,x1))
            else:
                if lo>x0:result.append((x0,lo))
                if hi<x1:result.append((hi,x1))
        pieces=result
    return [(x0,x1) for x0,x1 in pieces if x1-x0>=2]


def roof_height(t,base,rise,curve):
    'IA: Perfil alero→cumbrera creciente y convexo en sección; curve=0 recto, hasta 1 cóncavo de fantasía sin valle que retenga agua.'
    t=max(0,min(1,t))
    return base+rise*((1-curve*.7)*t+curve*.7*t*t)
