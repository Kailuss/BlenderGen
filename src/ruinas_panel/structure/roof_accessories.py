"""Chimenea y canalización sobre apoyos reales; reservas compatibles con vanos."""
import math,random
from .. import meta,config
from ..geometry import primitives,weather,balconies,timber
from . import openings,spatial,roof_damage


def chimney_plan(coll,p,walls,bounds,z,rise,patches):
    'IA: Reserva hogar desde planta baja en muro conservado, evitando vanos y escalera; dimensiona conducto y salida según hilada y cubierta.'
    if not p.chimneys:return None
    import bpy
    scene=bpy.context.scene
    xa,xb,ya,yb=bounds['cover'];xm=(xa+xb)/2
    half=max(12,min(17,p.stone_size*2));depth=max(9,min(12,p.thickness*.5+5))
    radius=min(depth-1,max(6.5,p.thickness*.65+2))
    windows=meta.get(scene,'ventanas_generadas',[])
    door=meta.get(scene,'puerta_generada',{})
    stair=meta.get(scene,'escalera_generada',{})
    for wallid,normal in (('front',(0,1)),('right',(-1,0)),('left',(1,0)),('back',(0,-1))):
        w=walls[wallid];tree=openings.wall_tree(coll,w)
        for fraction in (.74,.26,.5,.86,.14):
            u=w['start']+(w['end']-w['start'])*fraction
            if u-half<w['start']+4 or u+half>w['end']-4:continue
            if any(h['wall']==wallid and u+half+2>h['x0'] and u-half-2<h['x1'] for h in windows):continue
            if wallid=='front' and door and u+half+3>door['left'] and u-half-3<door['right']:continue
            if not all(openings.wall_hit(tree,w,p,u+dx,h) for dx in (-half+2,0,half-2) for h in (8,p.height*.5,p.height-3)):continue
            point=openings.wall_point(w,u,0,0)
            x=point[0]+normal[0]*(p.thickness/2+depth-.5)
            y=point[1]+normal[1]*(p.thickness/2+depth-.5)
            hx=depth if normal[0] else half;hy=half if normal[0] else depth
            blocked=False
            for part in meta.get(scene,'plano_interior',{}).get('partitions',[]):
                if part['axis']=='x':
                    blocked|=abs(y-part['fixed'])<hy+3 and x+hx>part['start'] and x-hx<part['end']
                else:
                    blocked|=abs(x-part['fixed'])<hx+3 and y+hy>part['start'] and y-hy<part['end']
            if blocked:continue
            if stair and 'error' not in stair:
                sx0=min(stair['opening'][0],stair['landing'][0],stair['approach'][0])
                sx1=max(stair['opening'][1],stair['landing'][1],stair['approach'][1])
                if x+hx+3>sx0 and x-hx-3<sx1 and y+hy+8>stair['y0'] and y-hy-8<stair['y1']:continue
            if roof_damage.distance(x,y,patches)<1.5:continue
            t=min((x-radius-xa)/(xm-xa),(xb-x-radius)/(xb-xm))
            top=spatial.roof_height(t,z,rise,p.roof_curve)+max(16,p.stone_size*3)+8
            floor=3.2 if p.ground_floor else 1.0
            return {'x':x,'y':y,'bottom':.5,'top':top,'radius':radius,'half_width':half,'half_depth':depth,
                    'normal':normal,'wall':wallid,'floor':floor,'mouth_top':floor+3*p.stone_size,
                    'hood_top':floor+5*p.stone_size,'roof':[xa,xb,z,rise,p.roof_curve]}
    return None


def chimney(coll,p,scene,plan):
    'IA: Hogar abierto sobre base pétrea, campana y conducto continuo; reserva forjado, remata cubierta y añade leños carbonizados.'
    meta.put(scene,'chimeneas_generadas',[plan] if plan else [])
    if not plan:return
    mat=primitives.material('Piedra · chimenea',(.43,.41,.37))
    soot=primitives.material('Hogar · hollín',(.055,.042,.03))
    half,depth,r=plan['half_width'],plan['half_depth'],plan['radius']
    floor,mouth,hood=plan['floor'],plan['mouth_top'],plan['hood_top']
    reserve_floors(coll,p,plan)
    chimney_block(coll,mat,plan,'Piedra · hogar base',-half-1,half+1,-depth,depth+3,.5,floor+.9)
    # Núcleo continuo detrás del aparejo: las juntas no abren el conducto a la habitación.
    for a,b,c,d in ((-half,-half+3,-depth,depth),(half-3,half,-depth,depth),(-half+3,half-3,-depth,-depth+3)):
        chimney_block(coll,soot,plan,'Hogar · fábrica interior',a,b,c,d,floor+.75,mouth+2.8)
    chimney_block(coll,mat,plan,'Piedra · hogar dintel',-half,half,depth-3,depth,mouth,mouth+3.8)
    rows=max(2,math.ceil((mouth+3.8-floor)/p.stone_size));pitch=(mouth+3.8-floor)/rows
    for row in range(rows):
        z0=floor+row*pitch;z1=z0+pitch-.12
        for side in (-1,1):
            lo,hi=sorted((side*(half-3),side*half))
            chimney_block(coll,mat,plan,'Piedra · hogar frente',lo,hi,depth-.8,depth+.2,z0,z1)
            cuts=[-depth,-depth/3,depth/3,depth] if row%2 else [-depth,0,depth]
            for part,(a,b) in enumerate(zip(cuts,cuts[1:])):
                lo,hi=sorted((side*(half-2.6),side*(half+.2)))
                chimney_block(coll,mat,plan,'Piedra · hogar jamba',lo,hi,a+.06,b-.06,z0,z1)
    ring(coll,mat,plan,'Piedra · campana hogar',(half,depth),(r,r),mouth+3,hood,3.0)
    ring(coll,soot,plan,'Hogar · conducto interior',(r-.5,r-.5),(r-.5,r-.5),hood-.1,plan['top'],2.0)
    rows=max(2,math.ceil((plan['top']-hood)/p.stone_size));pitch=(plan['top']-hood)/rows
    for row in range(rows):
        z0=hood+row*pitch
        for side in range(4):
            cuts=[-r,-r*.35,r*.35,r] if row%2 else [-r,0,r]
            for part,(a,b) in enumerate(zip(cuts,cuts[1:])):
                rng=random.Random(p.seed+60400+row*113+side*23+part)
                ob=primitives.block('Piedra · chimenea sillar',a+.05,b-.05,-r,-r+1.6,z0,z0+pitch-.12,coll,mat,rng=rng,wear=.13)
                ob['chimney_course']=row
                co=primitives.coords(ob);angle=side*math.pi/2;c,s=math.cos(angle),math.sin(angle)
                xx=co[:,0].copy();yy=co[:,1].copy();co[:,0]=c*xx-s*yy;co[:,1]=s*xx+c*yy
                primitives.set_coords(ob,co);place_chimney(ob,plan)
    ring(coll,mat,plan,'Piedra · remate chimenea',(r+1,r+1),(r+1,r+1),plan['top']-1,plan['top']+1.2,3.0)
    flashing(coll,plan)
    # Carbón y dos leños bajos, separados de la boca y apoyados en la solera.
    for i,(a,b,v) in enumerate(((-6,5,-2),(-4,6,2))):
        rng=random.Random(p.seed+60110+i);verts=[];faces=[]
        for u in (a,(a+b)*.5,b):
            for j in range(8):
                angle=j*math.tau/8;radius=rng.uniform(.85,1.15)
                verts.append((u,v+math.cos(angle)*radius,floor+1.7+math.sin(angle)*radius))
        faces=[tuple(reversed(range(8))),tuple(range(16,24))]
        for k in range(2):
            faces.extend((k*8+j,k*8+(j+1)%8,(k+1)*8+(j+1)%8,(k+1)*8+j) for j in range(8))
        ob=primitives.mesh_obj('Hogar · leño carbonizado',verts,faces,coll,soot)
        # El eje del cilindro es X; recalcular orientación antes de transformarlo.
        import bmesh
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
        place_chimney(ob,plan);ob['charred']=True


def place_chimney(ob,plan):
    'IA: Convierte X local tangente/Y local hacia la habitación; protege piezas del hogar frente al instanciado y grietas genéricas.'
    co=primitives.coords(ob);nx,ny=plan['normal'];u=co[:,0].copy();v=co[:,1].copy()
    co[:,0]=plan['x']+ny*u+nx*v;co[:,1]=plan['y']-nx*u+ny*v
    primitives.set_coords(ob,co)
    ob['ruin_box']=False;ob['chimney']=True;ob['protected_sill']=True
    return ob


def chimney_block(coll,mat,plan,name,a,b,c,d,z0,z1):
    'IA: Sillar local cerrado con coordenadas transformadas una vez; el hogar no hereda grietas que atraviesen sus paredes finas.'
    ob=primitives.block(name,a,b,c,d,z0,z1,coll,mat)
    return place_chimney(ob,plan)


def ring(coll,mat,plan,name,lower,upper,z0,z1,thickness):
    'IA: Anillo rectangular cerrado, opcionalmente troncopiramidal; deja la abertura interior libre en ambos extremos.'
    import bmesh
    verts=[]
    for h,(rx,ry) in ((z0,lower),(z1,upper)):
        for inset in (0,thickness):
            a,b=rx-inset,ry-inset
            verts.extend((x,y,h) for x,y in ((-a,-b),(a,-b),(a,b),(-a,b)))
    faces=[]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j,j+8,i+8),(i+4,i+12,j+12,j+4),(i,i+4,j+4,j),(i+8,j+8,j+12,i+12)))
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    return place_chimney(ob,plan)


def reserve_floors(coll,p,plan):
    'IA: Recorta madera que cruza hogar/conducto; conserva piezas fuera y enmarca el paso de entreplanta con cabeceros apoyados junto a la fábrica.'
    import bpy
    import numpy
    r=plan['radius']+1.0;x,y=plan['x'],plan['y']
    mat=primitives.material('Temporal',(.5,.5,.5))
    # La reserva baja incluye el hogar; la alta solo el conducto.
    cuts=[(plan['half_width']+1,plan['half_depth']+3,.4,plan['hood_top']) ,(r,r,plan['hood_top'],p.height+1)]
    for half,depth,z0,z1 in cuts:
        hx=depth if plan['normal'][0] else half;hy=half if plan['normal'][0] else depth
        lo=numpy.array((x-hx,y-hy,z0));hi=numpy.array((x+hx,y+hy,z1))
        vertices=[(a,b,c) for c in (z0,z1) for a,b in ((x-hx,y-hy),(x+hx,y-hy),(x+hx,y+hy),(x-hx,y+hy))]
        cutter=primitives.mesh_obj('Cortador · paso chimenea',vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],coll,mat)
        bpy.context.view_layer.update()
        for ob in list(coll.objects):
            if ob==cutter or ob.get('roof_timber') or ob.get('stair') or not (ob.get('wood_floor') or ob.get('madera')):continue
            co=primitives.coords(ob)
            if not len(co) or numpy.any(co.max(axis=0)<=lo) or numpy.any(co.min(axis=0)>=hi):continue
            if numpy.all(co>=lo) and numpy.all(co<=hi):primitives.remove_objects([ob]);continue
            mod=ob.modifiers.new('Paso del conducto','BOOLEAN');mod.operation='DIFFERENCE';mod.solver=config.BOOLEAN_SOLVER;mod.object=cutter
            primitives.apply_modifier(ob,mod,cutter)
            if not ob.data.vertices:primitives.remove_objects([ob])
        primitives.remove_objects([cutter])
    if p.height_type=='TWO' and p.upper_floor:
        wood=primitives.material('Madera · cabecero chimenea',(.27,.18,.1))
        for side in (-1,1):
            chimney_block(coll,wood,plan,'Madera · cabecero chimenea',-r-2,r+2,side*r-1,side*r+1,config.UPPER_FLOOR-4.5,config.UPPER_FLOOR-1.6)


def flashing(coll,plan):
    'IA: Encuentro cerámico estrecho bajo medias cañas de borde; sigue pendiente y mantiene libre el conducto.'
    import bmesh
    xa,xb,z,rise,curve=plan['roof'];xm=(xa+xb)/2;x,y=plan['x'],plan['y'];r=plan['radius']
    mat=primitives.material('Tejas · arcilla',(.40,.20,.115))
    outer=r+2.8;inner=r-.3
    verts=[]
    for layer in (0,.65):
        for radius in (outer,inner):
            for dx,dy in ((-radius,-radius),(radius,-radius),(radius,radius),(-radius,radius)):
                xx=x+dx;t=(xx-xa)/(xm-xa) if xx<xm else (xb-xx)/(xb-xm)
                verts.append((xx,y+dy,spatial.roof_height(t,z,rise,curve)+3.65+layer))
    faces=[]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j,j+4,i+4),(i+8,i+12,j+12,j+8),(i,i+8,j+8,j),(i+4,j+4,j+12,i+12)))
    ob=primitives.mesh_obj('Plomo · babero chimenea',verts,faces,coll,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob['chimney']=True;ob['roof_flashing']=True
    # Petos contra fábrica por encima de las crestas cerámicas: el encuentro no
    # termina en cuatro bordes abiertos ni deja pasar tejas a través del babero.
    verts=[]
    for layer in (0,3):
        for radius in (r+.6,r-.3):
            for dx,dy in ((-radius,-radius),(radius,-radius),(radius,radius),(-radius,radius)):
                xx=x+dx;t=(xx-xa)/(xm-xa) if xx<xm else (xb-xx)/(xb-xm)
                verts.append((xx,y+dy,spatial.roof_height(t,z,rise,curve)+3.65+layer))
    ob=primitives.mesh_obj('Plomo · peto chimenea',verts,faces,coll,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob['chimney']=True;ob['roof_flashing']=True
    from . import roof
    tile_verts=[];tile_faces=[];count=0
    for side in (-1,1):
        for j in range(max(3,math.ceil(2*(r+2.8)/4))):
            n=max(3,math.ceil(2*(r+2.8)/4));yy=y-r-2.8+(j+.5)*2*(r+2.8)/n
            ends=[]
            for xx in (x+side*(r+3.6),x+side*(r+.1)):
                t=(xx-xa)/(xm-xa) if xx<xm else (xb-xx)/(xb-xm)
                ends.append((xx,yy,spatial.roof_height(t,z,rise,curve)+4.7))
            roof.curved_tile(tile_verts,tile_faces,*ends,2*(r+2.8)/n,1.55,thickness=.5,taper=.85)
            count+=1
    roof.ceramic_mesh(coll,mat,'Tejas · encuentro chimenea',tile_verts,tile_faces,count)


def pipe_section(coll,mat,start,end,radius,seed,amount,name='Latón · bajante abollada'):
    'IA: Tramo tubular hueco de pared .65 mm, tres anillos abollados y labios cerrados; deformación común conserva espesor.'
    from mathutils import Vector
    import bmesh
    axis=(Vector(end)-Vector(start)).normalized()
    u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
    rng=random.Random(seed);verts=[];faces=[];n=10
    dents=[rng.uniform(-.24,.12)*amount for _ in range(n)]
    for station in range(3):
        center=Vector(start).lerp(Vector(end),station/2)
        for layer in (0,1):
            for j in range(n):
                angle=j*math.tau/n
                r=radius-layer*.65+dents[j]*(1 if station==1 else .25)
                verts.append(tuple(center+r*(math.cos(angle)*u+math.sin(angle)*v)))
    for station in range(2):
        for layer in (0,1):
            for j in range(n):
                a=station*2*n+layer*n+j;b=station*2*n+layer*n+(j+1)%n
                faces.append((a,b,b+2*n,a+2*n))
    for station in (0,2):
        for j in range(n):
            a=station*2*n+j;b=station*2*n+(j+1)%n
            faces.append((a,a+n,b+n,b))
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob['drain']=True;ob['pipe_section']=True;ob['wall_mm']=.65
    return ob


def gutter(coll,mat,x,y0,y1,z,seed=0,amount=0):
    'IA: Canalón ancho de latón con tres estaciones abolladas y pared .7 mm; cada luz constituye una sección independiente.'
    rng=random.Random(seed);verts=[];faces=[];n=18
    for station,y in enumerate((y0,(y0+y1)/2,y1)):
        dent=rng.uniform(-.35,.2)*amount if station==1 else 0
        profile=[(math.cos(i*math.pi/8)*(2.6+dent),-math.sin(i*math.pi/8)*(2.6+dent)) for i in range(9)]
        profile += [(math.cos(i*math.pi/8)*(1.9+dent),-math.sin(i*math.pi/8)*(1.9+dent)) for i in range(8,-1,-1)]
        verts.extend((x+dx,y,z+dz) for dx,dz in profile)
    faces=[tuple(reversed(range(n))),tuple(range(2*n,3*n))]
    for station in range(2):
        faces.extend((station*n+i,station*n+(i+1)%n,(station+1)*n+(i+1)%n,(station+1)*n+i) for i in range(n))
    ob=primitives.mesh_obj('Latón · canalón',verts,faces,coll,mat)
    import bmesh
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob['drain']=True


def drains(coll,p,scene,walls,bounds,bays,z,patches):
    'IA: Canalones solo en luces de cubierta supervivientes; bajantes en franjas sin ventanas ni balcones, con abrazaderas a muro.'
    meta.put(scene,'bajantes_generadas',[])
    if not p.brass_pipes:return
    mat=primitives.material('Latón · envejecido',(.36,.26,.105));xa,xb,ya,yb=bounds['cover'];result=[]
    identity={'id':'accessory','origin':(0,0),'axis':(1,0)}
    windows=meta.get(scene,'ventanas_generadas',[])
    for wallid,edge,side in (('left',xa,-1),('right',xb,1)):
        w=walls[wallid];tree=openings.wall_tree(coll,w);spans=[]
        for a,b in zip(bays,bays[1:]):
            if b['index']!=a['index']+1:continue
            for lo,hi in roof_damage.segments(a['y'],b['y'],edge,patches,'y'):
                if hi-lo<2:continue
                rng=random.Random(p.seed+round(lo*13)+side*97)
                if rng.random()<p.wear*.18:continue
                gap=.6*p.wear
                gutter(coll,mat,edge,lo+gap,hi-gap,z+1,p.seed+round(lo*11),p.wear);spans.append((lo+gap,hi-gap))
        for y in (w['start']+8,w['end']-8,(w['start']+w['end'])/2):
            if not any(a+1<y<b-1 for a,b in spans):continue
            if any(h['wall']==wallid and h['x0']-5<y<h['x1']+5 for h in windows):continue
            if not all(openings.wall_hit(tree,w,p,y,h) for h in (8,p.height*.5,p.height-4)):continue
            x=w['origin'][0]+side*(p.thickness/2+3.4)
            rng=random.Random(p.seed+round(y*7));sections=max(3,math.ceil((p.height-4)/18));kept=[]
            for i in range(sections):
                low=4+(p.height-5)*i/sections;high=4+(p.height-5)*(i+1)/sections
                if 0<i<sections-1 and rng.random()<p.wear*.24:continue
                shift=rng.uniform(-.7,.7)*p.wear
                bottom=(x+shift,y,low+.5*p.wear);top=(x,y,high+.25)
                pipe_section(coll,mat,bottom,top,1.8,p.seed+62000+i,p.wear)
                pipe_section(coll,mat,(x,y,high-1),(x,y,high+.5),2.15,p.seed+62100+i,p.wear,'Latón · manguito')
                h=(low+high)/2
                ob=primitives.block('Latón · abrazadera',min(x,w['origin'][0]),max(x,w['origin'][0]),y-2.1,y+2.1,h-.65,h+.65,coll,mat);ob['drain']=True
                kept.append(i)
            pipe_section(coll,mat,(x+side*3,y,1.8),(x,y,4.3),1.8,p.seed+62200,p.wear)
            pipe_section(coll,mat,(x,y,p.height-1),(edge,y,z-.3),1.8,p.seed+62201,p.wear)
            result.append({'wall':wallid,'y':y,'sections':sections,'surviving':kept});break
    meta.put(scene,'bajantes_generadas',result)
