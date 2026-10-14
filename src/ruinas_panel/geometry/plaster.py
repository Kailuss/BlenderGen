"""Revoco con relieve geométrico acotado, cerrado y sin booleanas."""
import math


def perlin(x,z,seed):
    'IA: Ruido de gradientes 2D reproducible sin estado global, con interpolación quintica continua; no añade geometría.'
    ix=math.floor(x);iz=math.floor(z);u=x-ix;v=z-iz
    def dot(a,b):
        'IA: Gradiente unitario elegido por hash entero estable en cada esquina de la retícula.'
        h=((a*374761393+b*668265263+seed*1442695041)&0xffffffff);h=((h^(h>>13))*1274126177)&0xffffffff
        angle=(h&7)*math.pi/4
        return math.cos(angle)*(x-a)+math.sin(angle)*(z-b)
    fu=u*u*u*(u*(u*6-15)+10);fv=v*v*v*(v*(v*6-15)+10)
    a=dot(ix,iz)*(1-fu)+dot(ix+1,iz)*fu;b=dot(ix,iz+1)*(1-fu)+dot(ix+1,iz+1)*fu
    return a*(1-fv)+b*fv


def panel(xs,bottom,tops,y0,y1,seed,damage=0):
    'IA: Revoco cerrado con relieve Perlin acotado y pérdida interior por contorno interpolado; conserva perímetro estructural y tapa agujeros sin booleanas ni más densidad base.'
    points=[];indices={};polys=[];border=set();amount=max(0,(damage-.45)/.55)
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
            if amount and clipped:
                values=[]
                for x,z in clipped:
                    edge=min(x-xs[0],xs[-1]-x,z-bottom,za+slope*(x-a)-z)
                    values.append(max((4-edge)*.25,perlin(x*.085,z*.085,seed)+.55-.9*amount))
                cut=[]
                for j,current in enumerate(clipped):
                    previous=clipped[j-1];dp=values[j-1];dc=values[j]
                    if (dp>=0)!=(dc>=0):
                        t=dp/(dp-dc);point=(previous[0]+t*(current[0]-previous[0]),previous[1]+t*(current[1]-previous[1]))
                        cut.append(point);border.add((round(point[0],7),round(point[1],7)))
                    if dc>=0:cut.append(current)
                clipped=cut
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
            relief=0 if (x,z) in border else min(.28,max(.02,.14+.14*perlin(x*.19,z*.19,seed+side*73)+.06*perlin(x*.53,z*.53,seed+31)))
            verts.append((x,y+(relief if side==0 else -relief),z))
    for poly in polys:
        faces.extend((tuple(reversed(poly)),tuple(i+n for i in poly)))
        for a,b in zip(poly,poly[1:]+poly[:1]):
            key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
    for (a,b),count in edges.items():
        if count==1:faces.append((a,b,b+n,a+n))
    return verts,faces
