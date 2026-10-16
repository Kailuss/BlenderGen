"""Cimiento elevado, acceso exterior y patio opcional; geometría en mm."""
import math
from mathutils import Matrix
from .. import meta
from ..geometry import primitives,timber


def build(coll,p,scene):
    'IA: Eleva la construcción sin mover terreno, añade fábrica perimetral bajo muros/pilares, escalones hasta la entrada y patio vallado con paso libre; cero altura conserva la casa histórica.'
    height=p.foundation_height if p.foundation_enabled else 0
    meta.put(scene,'cimiento_generado',{})
    if not height and not p.patio_enabled:return
    walls={w['id']:w for w in meta.get(scene,'paredes_generadas',[])}
    if p.layout_mode!='ROOM':return
    from . import roof
    x0,x1,y0,y1=roof.envelope(coll,p,walls)['walls'];thickness=p.thickness
    stone=primitives.material('Piedra · cimientos',(.43,.43,.40))
    door=meta.get(scene,'puerta_generada');cx=(door['left']+door['right'])/2 if door else 0
    width=max(35,door['right']-door['left']+6 if door else 35);run=0
    if height:
        transform=Matrix.Translation((0,0,height))
        for ob in list(coll.objects):
            key=primitives.piece_key(ob).lower()
            if ob.get('escombro') or any(tag in key for tag in ('tierra','grava','peana')):continue
            ob.data.transform(transform)
        rows=max(1,math.ceil((height+2)/5));rh=(height+2)/rows
        spans=[(x0,x1,y0,y0+thickness,False),(x0,x1,y1-thickness,y1,False),(y0+thickness,y1-thickness,x0,x0+thickness,True),(y0+thickness,y1-thickness,x1-thickness,x1,True)]
        for side,(a,b,c,d,swap) in enumerate(spans):
            count=max(1,math.ceil((b-a)/14));pitch=(b-a)/count
            for row in range(rows):
                cuts=sorted({a,b,*[a+(i+(.5 if row%2 else 0))*pitch for i in range(count+1) if a<a+(i+(.5 if row%2 else 0))*pitch<b]})
                for lo,hi in zip(cuts,cuts[1:]):
                    xy=(c+.06,d-.06,lo+.06,hi-.06) if swap else (lo+.06,hi-.06,c+.06,d-.06)
                    ob=primitives.block('Piedra · cimiento %s'%side,*xy,row*rh,(row+1)*rh-.06,coll,stone);ob['foundation']=True
        if door:
            count=max(1,math.ceil(height/4));run=count*p.entrance_tread
            for i in range(count):
                top=height*(i+1)/count
                ob=primitives.block('Piedra · escalón de entrada',cx-width/2,cx+width/2,y0-run+i*p.entrance_tread,y0-run+(i+1)*p.entrance_tread,0,top,coll,stone);ob['foundation']=True
        # Metadatos publicados: cotas mundiales, sin volver a alimentar reglas locales de construcción.
        for key,fields in (('ventanas_generadas',('z0','z1')),('vigas_generadas',('z',)),('suelos_generados',('top_mm',)),('cubierta_generada',('z','ridge'))):
            records=meta.get(scene,key,[])
            for record in records:
                for field in fields:
                    if field in record:record[field]+=height
            meta.put(scene,key,records)
        if door:
            for field in ('top','lintel_top'):door[field]+=height
            meta.put(scene,'puerta_generada',door)
        stairs=meta.get(scene,'escaleras_generadas',[])
        for stair in stairs:
            if stair and 'error' not in stair:
                stair['bottom']+=height;stair['top']+=height
        meta.put(scene,'escaleras_generadas',stairs)
        first=meta.get(scene,'escalera_generada',{})
        if first and 'error' not in first:
            first['bottom']+=height;first['top']+=height;meta.put(scene,'escalera_generada',first)
    if p.patio_enabled:
        margin=p.patio_margin;left=x0-margin;right=x1+margin;front=y0-max(margin,run+10);back=y1+margin
        ground=primitives.material('Tierra · patio',(.29,.235,.16))
        primitives.block('Tierra · patio',left,right,front,back,-1,0,coll,ground)
        if p.patio_fence:
            wood=primitives.material('Madera · valla',(.31,.22,.13));gate=width+4
            spans=[((left,front),(cx-gate/2,front)),((cx+gate/2,front),(right,front)),((left,back),(right,back)),((left,front),(left,back)),((right,front),(right,back))]
            for index,(a,b) in enumerate(spans):
                length=math.dist(a,b);count=max(1,math.ceil(length/20))
                for i in range(count+1):
                    x=a[0]+(b[0]-a[0])*i/count;y=a[1]+(b[1]-a[1])*i/count
                    timber.timber_beam(coll,wood,'Madera · poste valla',(x,y,0),(x,y,p.fence_height),2.4,2.4,p.seed+43000+index*100+i,coarse=True)
                for z in (p.fence_height*.35,p.fence_height*.8):
                    timber.timber_beam(coll,wood,'Madera · travesaño valla',(*a,z),(*b,z),2,2,p.seed+44000+index,coarse=True)
    meta.put(scene,'cimiento_generado',{'height_mm':height,'entrance_run_mm':run,'patio':p.patio_enabled,'bounds':[x0,x1,y0,y1]})
