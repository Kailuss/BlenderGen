"""Revoco con relieve geométrico acotado, cerrado y sin booleanas."""
import math
import random


def panel(xs,bottom,tops,y0,y1,seed):
    'IA: Cuadrícula uniforme de cal recortada por cubierta; grano interior de .28 mm sin comprimirlo en aleros, borde intacto y espesor nominal menos .56 mm.'
    points=[];indices={};polys=[];border=set();rng=random.Random(seed)
    for column,(a,b) in enumerate(zip(xs,xs[1:])):
        za,zb=tops[column:column+2];slope=(zb-za)/(b-a)
        for row in range(math.ceil((max(za,zb)-bottom)/4)):
            low=bottom+row*4;high=low+4
            square=[(a,low),(b,low),(b,high),(a,high)];clipped=[]
            for previous,current in zip(square[-1:]+square[:-1],square):
                dp=previous[1]-(za+slope*(previous[0]-a));dc=current[1]-(za+slope*(current[0]-a))
                if (dp<=0)!=(dc<=0):
                    t=dp/(dp-dc);clipped.append((previous[0]+t*(current[0]-previous[0]),previous[1]+t*(current[1]-previous[1])))
                if dc<=0:clipped.append(current)
            keys=[]
            for x,z in clipped:
                key=(round(x,7),round(z,7))
                if keys and keys[-1]==key:continue
                keys.append(key)
                if key not in indices:indices[key]=len(points);points.append(key)
                if abs(x-xs[0])<1e-6 or abs(x-xs[-1])<1e-6 or abs(z-bottom)<1e-6 or abs(z-(za+slope*(x-a)))<1e-6:border.add(key)
            if len(keys)>1 and keys[0]==keys[-1]:keys.pop()
            if len(keys)>=3:polys.append(tuple(indices[key] for key in keys))
    n=len(points);verts=[];faces=[];edges={}
    for side,y in enumerate((y0,y1)):
        for x,z in points:
            relief=0 if (x,z) in border else min(.28,max(.02,.14+rng.uniform(-.1,.1)+.04*math.sin(x*.37+z*.51)))
            verts.append((x,y+(relief if side==0 else -relief),z))
    for poly in polys:
        faces.extend((tuple(reversed(poly)),tuple(i+n for i in poly)))
        for a,b in zip(poly,poly[1:]+poly[:1]):
            key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
    for (a,b),count in edges.items():
        if count==1:faces.append((a,b,b+n,a+n))
    return verts,faces
