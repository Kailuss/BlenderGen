"""Daño localizado de cubierta y restos asentados, sin simulación ni booleanos masivos."""
import math,random
from .. import meta
from ..geometry import primitives,timber,terrain
from . import damage_regions


def plan(p,bounds):
    'IA: Dos regiones reproducibles en faldones opuestos, con intensidad máxima entre daño de cubierta y derrumbe general; comparten hundimiento, anclajes y rotura.'
    return damage_regions.roof_events(p.seed,getattr(p,'roof_damage_seed',0),max(p.roof_damage,p.collapse),bounds['cover'])


def broken(x,y,patches):
    'IA: El núcleo pierde piezas solo después del 45% de daño; antes conserva los apoyos deformados, con transición continua en área.'
    return damage_regions.broken(x,y,patches)


def sag(x,y,patches):
    'IA: Hundimiento compartido en mm para madera y tejas; campo continuo bidimensional, acotado y nulo en los bordes de cubierta.'
    result=0
    for h in patches:
        radius=damage_regions.radius(x,y,h)
        if radius>=1.6:continue
        envelope=(1-(radius/1.6)**2)**2
        bounds=h.get('bounds')
        anchor=min(1,max(0,min(x-bounds[0],bounds[1]-x,y-bounds[2],bounds[3]-y)/6)) if bounds else 1
        result=max(result,min(16,min(h['rx'],h['ry'])*.75)*h.get('severity',1)*envelope*anchor)
    return result


def deform_timber(coll,patches):
    'IA: Sustituye madera afectada por tramos rectos cerrados con extremos astillados; cambia poses y rompe juntas, nunca curva las fibras de un tramo.'
    from mathutils import Vector
    import bpy
    maximum=0;affected=0;fragments=0
    for ob in list(coll.objects):
        if not ob.get('roof_timber') or ob.get('roof_gable_frame') or 'timber_path' not in ob:continue
        path=[Vector(v) for v in ob['timber_path']];points=[path[0]]
        for a,b in zip(path,path[1:]):
            steps=max(1,math.ceil((b-a).length/16))
            points.extend(a.lerp(b,i/steps) for i in range(1,steps+1))
        offsets=[sag(v.x,v.y,patches) for v in points];amount=max(offsets,default=0)
        if amount<.15:continue
        displaced=[Vector((v.x,v.y,v.z-drop)) for v,drop in zip(points,offsets)]
        # Fusionar intervalos intactos colineales evita trocear madera sana sin necesidad.
        knots=[displaced[0]]
        for i in range(1,len(displaced)-1):
            before=(displaced[i]-knots[-1]).normalized();after=(displaced[i+1]-displaced[i]).normalized()
            if before.dot(after)<.9998 or offsets[i]>.15:knots.append(displaced[i])
        knots.append(displaced[-1])
        name=ob.name;props={k:ob[k] for k in ob.keys()};width=ob['timber_width'];depth=ob['timber_depth'];seed=ob['timber_seed']
        material=bpy.data.materials.get('Madera · cubierta') or ob.data.materials[0]
        primitives.remove_objects([ob])
        for index,(a,b) in enumerate(zip(knots,knots[1:])):
            direction=(b-a).normalized();broken=(index>0,index<len(knots)-2)
            start=a+direction*(.08 if broken[0] else 0);finish=b-direction*(.08 if broken[1] else 0)
            part=timber.timber_beam(coll,material,name if index==0 else name+' · astilla %02d'%index,start,finish,width,depth,seed+index*31,coarse=True,broken=broken)
            for key in ('roof_timber','roof_gable_frame'):
                if key in props:part[key]=props[key]
            part['roof_fracture_parent']=name;part['roof_member_segment']=index
            part['roof_sag_mm']=amount;part['roof_damage_stage']=2 if any(h.get('severity',1)>.45 for h in patches) else 1
            fragments+=1
        maximum=max(maximum,amount);affected+=1
    return {'sag_mm':maximum,'deformed_timbers':affected,'fractured_timbers':affected,'timber_fragments':fragments}


def distance(x,y,patches):
    'IA: Distancia normalizada cuadrática al evento común; conserva el umbral existente de detalle en los bordes.'
    return min((damage_regions.radius(x,y,h)**2 for h in patches),default=1000)


def segments(a,b,fixed,patches,axis):
    'IA: Corta apoyos con el mismo contorno irregular utilizado por las tejas; conserva únicamente extremos anclados.'
    return damage_regions.segments(a,b,fixed,patches,axis)


def debris(coll,p,scene,bounds,missing):
    'IA: Deposita fragmentos de teja y palos junto al faldón perdido sobre tierra real; coste máximo de 64 tejas y 12 palos.'
    meta.put(scene,'escombros_cubierta',{})
    if not missing or p.rubble_amount<=0:return
    xa,xb,ya,yb=bounds['cover'];rng=random.Random(p.seed+48200)
    clay=primitives.material('Tejas · arcilla',(.40,.20,.115));wood=primitives.material('Madera · cubierta',(.31,.22,.13));soil=primitives.material('Tierra · arena',(.36,.31,.24))
    total=0;sticks=0
    for side in (0,1):
        points=[q for q in missing if (q[0]<(xa+xb)/2)==(side==0)]
        if not points:continue
        cx=(bounds['walls'][0]-2 if side==0 else bounds['walls'][1]+2);cy=sum(q[1] for q in points)/len(points)
        _,surface=terrain.earth_patch(coll,soil,'Tierra · caída de cubierta',cx,cy,10,13,1.3+p.rubble_amount*1.2,p.seed+side+48210,p.ground_roughness)
        count=min(32,max(2,round(len(points)*.3*p.rubble_amount)))
        for j in range(count):
            x=cx+rng.uniform(-5,5);y=cy+rng.uniform(-9,9);angle=rng.uniform(0,math.tau)
            w=rng.uniform(1.8,4.3);d=rng.uniform(2,5.5)
            ob=primitives.block('Teja caída · fragmento',-w/2,w/2,-d/2,d/2,0,.7,coll,clay)
            primitives.clip_closed(ob,(w*.25,d*.25,.4),(1,1,.15))
            from mathutils import Euler
            import numpy as np
            co=primitives.coords(ob)@np.array(Euler((rng.uniform(-.4,.4),rng.uniform(-.4,.4),angle)).to_matrix()).T
            co[:,0]+=x;co[:,1]+=y;primitives.set_coords(ob,co);terrain.settle_rubble(ob,surface)
            ob['escombro']=True;ob['roof_debris']=True;total+=1
        for j in range(min(6,1+count//5)):
            x=cx+rng.uniform(-4,4);y=cy+rng.uniform(-8,8);ang=rng.random()*math.tau;length=rng.uniform(5,13)
            ob=timber.timber_beam(coll,wood,'Madera · palo caído',(x,y,1),(x+math.cos(ang)*length,y+math.sin(ang)*length,1.5),1.4,1.3,p.seed+48400+side*100+j,coarse=True)
            terrain.settle_rubble(ob,surface);ob['escombro']=True;ob['roof_debris']=True;sticks+=1
        terrain.gravel_batch(coll,soil,'Arena · cubierta caída',cx,cy,10,13,surface,round(18+25*p.rubble_amount),p.seed+48600+side,radius_scale=.45)
    meta.put(scene,'escombros_cubierta',{'tiles':total,'sticks':sticks,'source_missing':len(missing)})
