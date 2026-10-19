"""Carpinterías practicables, miradores y tejadillos cerámicos por vano."""
import math
import bmesh
from mathutils import Matrix,Vector
from .. import meta
from ..geometry import primitives,timber,balconies,plaster
from . import openings,roof,spatial,layout


def groups(windows,p,pillars,door=None):
    'IA: Agrupa ventanas exteriores coplanares y del mismo nivel, con distancia acotada y sin absorber pilares; nunca incluye accesos de balcón.'
    result=[]
    for index,h in sorted(enumerate(windows),key=lambda item:(item[1]['wall'],item[1]['z0'],item[1]['x0'])):
        if h['balcony']:continue
        previous=result[-1][-1][1] if result else None
        join=p.window_bay_join and p.window_projection>0 and p.window_facing=='OUTSIDE' and previous and previous['wall']==h['wall'] and abs(previous['z0']-h['z0'])<.01 and abs(previous['z1']-h['z1'])<.01 and h['x0']-previous['x1']<=p.window_bay_gap
        if join and h['wall']=='front':join=not any(previous['x1']<c['x_mm']+c['width_mm']/2 and h['x0']>c['x_mm']-c['width_mm']/2 for c in pillars)
        if join and h['wall']=='front' and door and h['z0']<door['lintel_top']+3:join=not (previous['x1']<door['right']+3 and h['x0']>door['left']-3)
        if join:result[-1].append((index,h))
        else:result.append([(index,h)])
    return result


def beam(coll,mat,w,name,a,b,size,depth,seed):
    'IA: Madera local con veta y sección cerrada, transformada rígidamente a la fachada y marcada como detalle para no ampliar el tejado principal.'
    ob=timber.timber_beam(coll,mat,name,a,b,size,depth,seed,coarse=True)
    ob['facade_detail']=True
    return balconies.place(ob,w)


def leaves(coll,p,w,h,index):
    'IA: Dos hojas de bastidor con parteluces, giro rígido alrededor de ejes verticales y dos pernios por hoja; ángulo es postura inicial, no bisagra Bullet.'
    wood=primitives.material('Madera · ventana',(.31,.22,.13));iron=primitives.material('Hierro · bisagra',(.10,.105,.11))
    side=1 if w['id'] in ('left','back') else -1
    y=h['frame_y']+side*1.8;bottom=h['z0']+3.3;top=h['z1']-2
    mid=(h['x0']+h['x1'])/2
    for leaf,(pivot,end,sign) in enumerate(((h['x0']+1.6,mid-.2,1),(h['x1']-1.6,mid+.2,-1))):
        angle=math.radians(p.window_open_angle)*side*sign
        transform=Matrix.Translation((pivot,y,0))@Matrix.Rotation(angle,4,'Z')@Matrix.Translation((-pivot,-y,0))
        a,b=sorted((pivot,end));parts=[]
        for x in (a,b):parts.append(((x,y,bottom),(x,y,top)))
        for z in (bottom,top,(bottom+top)/2):parts.append(((a,y,z),(b,y,z)))
        parts.append((((a+b)/2,y,bottom),((a+b)/2,y,top)))
        for part,(start,finish) in enumerate(parts):
            ob=timber.timber_beam(coll,wood,'Madera · hoja ventana',start,finish,.95,1.1,p.seed+51000+index*41+leaf*17+part,coarse=True)
            ob.data.transform(transform);ob['facade_detail']=True;ob['window_leaf']=True;ob['leaf_angle_degrees']=p.window_open_angle
            balconies.place(ob,w)
        for z in (bottom+2,top-2):
            ob=balconies.rod(coll,iron,w,'Hierro · pernio ventana',[(pivot,y,z-.8),(pivot,y,z+.8)],.5);ob['facade_detail']=True
            fixed=(pivot-sign*.9,h['frame_y']+side*1.3,z)
            tip=transform@Vector((pivot+sign*2,y,z))
            for name,points in (('Hierro · pletina fija ventana',[fixed,(pivot,y,z)]),('Hierro · pletina hoja ventana',[(pivot,y,z),tuple(tip)])):
                ob=balconies.rod(coll,iron,w,name,points,.35);ob['facade_detail']=True


def canopy(coll,p,w,a,b,top,depth,ceiling=None):
    'IA: Tejadillo de media caña con perfil compartido, solape del 30%, pares rectos por tramos y rastreles; todo queda sobre el dintel.'
    side=1 if w['id'] in ('left','back') else -1
    rear=side*(p.thickness/2-.3);front=side*(p.thickness/2+depth+7)
    wood=primitives.material('Madera · tejadillo',(.31,.22,.13));clay=primitives.material('Tejas · arcilla',(.40,.20,.115))
    a-=2.5;b+=2.5;run=abs(front-rear);rise=min(12,run*.52);base=top+2.8
    if ceiling is not None:rise=max(.5,min(rise,ceiling-base-5.5))
    rows=max(2,math.ceil(run/5));columns=max(2,math.ceil((b-a)/5));pitch=(b-a)/columns
    def point(x,t,extra=0):
        'IA: Coordenada local alero→muro; comparte perfil con la cubierta y mantiene las tejas por encima del bastidor.'
        longitudinal=.3*spatial.roof_offset(x,a,b,p.roof_sweep,p.roof_sweep_bias)
        return (x,front+(rear-front)*t,spatial.roof_height(t,base,rise,p.roof_curve)+longitudinal+extra)
    for x in (a+1,b-1):
        for row in range(rows):beam(coll,wood,w,'Madera · par tejadillo',point(x,row/rows),point(x,(row+1)/rows),1.7,1.8,p.seed+52000+row)
        beam(coll,wood,w,'Madera · ménsula tejadillo',(x,rear,top-3),point(x,.08),1.7,1.7,p.seed+52020)
    for row in range(rows+1):beam(coll,wood,w,'Madera · rastrel tejadillo',point(a,row/rows,2.1),point(b,row/rows,2.1),3.4,1.3,p.seed+52100+row)
    verts=[];faces=[];count=0
    for row in range(rows):
        t0=row/rows;t1=min(1,(row+1.3)/rows)
        for column in range(columns):
            x=a+(column+.5)*pitch
            roof.curved_tile(verts,faces,point(x,t0,3.7),point(x,t1,2.65),pitch+.08,min(2,pitch*.43),thickness=.5,taper=.72);count+=1
    ob=roof.ceramic_mesh(coll,clay,'Tejas · tejadillo fachada',verts,faces,count)
    ob['facade_detail']=True;balconies.place(ob,w)


def infill(coll,p,w,a,b,bottom,top,plane,seed,lateral=False):
    'IA: Paño de cal cerrado con relieve y pérdida Perlin independientes; el lateral intercambia ejes antes de orientar normales, y Revoco identifica su prefractura física.'
    if b-a<.1 or top-bottom<.1:return None
    step=2 if p.facade_damage>.45 or p.collapse>.35 else 4
    count=max(1,math.ceil((b-a)/step))
    xs=[a+(b-a)*i/count for i in range(count+1)]
    local=(plane,(a+b)/2,top) if lateral else ((a+b)/2,plane,top)
    world=openings.wall_point(w,*local)
    loss=max(0,p.height-spatial.collapse_height(p,world[0],world[1]))/max(1,p.height-4)
    severity=max(p.facade_damage,min(1,loss*(top/max(1,p.height))*2))
    verts,faces=plaster.panel(xs,bottom,[top]*len(xs),plane-1,plane+1,seed,severity,step=step,border_width=2)
    if lateral:verts=[(y,x,z) for x,y,z in verts]
    material=primitives.material('Revoco · cal',(.66,.60,.47))
    ob=primitives.mesh_obj('Revoco · lateral mirador' if lateral else 'Revoco · entreventana mirador',verts,faces,coll,material)
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob['facade_detail']=True;ob['fragile_material']='plaster'
    return balconies.place(ob,w)


def build(coll,p,scene,walls,door):
    'IA: Proyecta carpinterías existentes, abre el espacio común de miradores y añade hojas/tejadillos optativos; conserva vanos de balcón y geometría histórica con controles a cero.'
    meta.put(scene,'fachadas_detalles',[])
    if not any((p.window_leaves,p.window_canopies,p.door_canopy,p.window_projection)):return
    lookup={w['id']:w for w in walls};windows=meta.get(scene,'ventanas_generadas',[]);records=[]
    wood=primitives.material('Madera · mirador',(.31,.22,.13))
    for group in groups(windows,p,meta.get(scene,'pilares_generados',[]),door):
        h=group[0][1];w=lookup[h['wall']];side=1 if w['id'] in ('left','back') else -1
        a=group[0][1]['x0'];b=group[-1][1]['x1'];z0=h['z0'];z1=h['z1']
        depth=p.window_projection if p.window_facing=='OUTSIDE' else 0
        if depth:
            rear=side*(p.thickness/2-.5);front=h['frame_y']+side*depth
            if len(group)>1:openings.carve_rectangle(coll,w,a,b,z0,z1,p.thickness+5,'Mirador compartido')
            ids={i for i,_ in group};shift=Vector((-w['axis'][1]*side*depth,w['axis'][0]*side*depth,0))
            for ob in coll.objects:
                if ob.get('facade_window',-1) in ids:
                    ob.data.transform(Matrix.Translation(shift));ob['facade_detail']=True
            for _,window in group:window.update(frame_y=window['frame_y']+side*depth,bay_x0=a,bay_x1=b,projection_mm=depth)
            for z in (z0,z1+1):
                ob=primitives.block('Madera · fondo mirador',a-1.8,b+1.8,min(rear,front)-.6,max(rear,front)+.6,z-1.2,z+.4,coll,wood)
                ob['facade_detail']=True;balconies.place(ob,w)
            for x in (a-1,b+1):
                panel_rear=rear+side*2;panel_front=front-side
                if side*(panel_front-panel_rear)>.1:
                    infill(coll,p,w,min(panel_rear,panel_front),max(panel_rear,panel_front),z0+1,z1-1,x,p.seed+53500+group[0][0]*17+int(x*100),lateral=True)
                for z in (z0,z1):beam(coll,wood,w,'Madera · lateral mirador',(x,rear,z),(x,front,z),2,2,p.seed+53000)
                for y in (rear,front):beam(coll,wood,w,'Madera · montante mirador',(x,y,z0),(x,y,z1),2,2,p.seed+53010)
                beam(coll,wood,w,'Madera · ménsula mirador',(x,rear,z0-min(8,depth)),(x,front,z0-.8),2,2,p.seed+53020)
            for (_,left),(_,right) in zip(group,group[1:]):
                a0=left['x1']+.7;b0=right['x0']-.7
                if b0>a0:
                    infill(coll,p,w,a0,b0,z0+.4,z1,front,p.seed+53600+int(a0*100))
        for index,window in group:
            if p.window_leaves:leaves(coll,p,w,window,index)
        bases=layout.floor_bases(p);ceiling=bases[h['floor']+1]-3 if h['floor']+1<len(bases) else p.height
        if p.window_canopies:canopy(coll,p,w,a,b,z1,depth,ceiling)
        records.append({'wall':h['wall'],'windows':[i for i,_ in group],'projection_mm':depth,'bounds':[a,b,z0,z1],'canopy':p.window_canopies})
    if p.door_canopy and door and not door.get('gate'):
        bases=layout.floor_bases(p)
        ceiling=bases[1]-4 if len(bases)>1 else p.height
        canopy(coll,p,lookup['front'],door['left'],door['right'],door['lintel_top']+2,0,ceiling)
    if p.collapse>0:
        discard=[]
        for ob in list(coll.objects):
            if not ob.get('facade_detail') and 'facade_window' not in ob:continue
            co=primitives.coords(ob)
            if not len(co):continue
            low=co.min(axis=0);high=co.max(axis=0);center=(low+high)/2
            ceiling=spatial.collapse_height(p,float(center[0]),float(center[1]))
            if low[2]>=ceiling:discard.append(ob)
            elif high[2]>ceiling:
                primitives.clip_closed(ob,(0,0,ceiling),(0,0,1))
                ob['facade_collapse_trimmed']=True
        primitives.remove_objects(discard)
    meta.put(scene,'ventanas_generadas',windows);meta.put(scene,'fachadas_detalles',records)
