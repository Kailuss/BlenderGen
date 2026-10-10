"""Suelos de madera en habitaciones: tablones lowpoly, juntas alternas sobre vigas y rotura local."""
import math
import random
from .. import meta,runtime,config
from ..geometry import primitives,timber
from . import openings,spatial,layout


def plank(coll,mat,name,a,b,y,width,top,seed,grain,broken=False,broken_left=False):
    'IA: Tablón cerrado con veta longitudinal de baja densidad; extremos rotos varían por fibra sin generar esquirlas flotantes.'
    rng=random.Random(seed);nx=max(3,min(12,round((b-a)/3)));ny=6
    phase=rng.uniform(0,math.tau)
    end=[rng.uniform(-.7,.1) if broken else 0 for _ in range(ny+1)]
    verts=[];faces=[];n=(nx+1)*(ny+1)
    for layer in range(2):
        for j in range(ny+1):
            u=j/ny
            for i in range(nx+1):
                t=i/nx;x=a+(b-a)*t+end[j]*t**8
                if broken_left:x+=rng.uniform(.05,.65)*(1-t)**8
                relief=grain*(.045*math.sin(t*9+phase)-.13*max(0,math.cos(u*19+t*.7+phase))**4)
                relief-=min(.65,timber.decay_relief(u-.5,t,phase,runtime.settings.wood_damage))
                z=top+relief if layer else top-1.8
                verts.append((x,y+(u-.5)*width,z))
    for j in range(ny):
        for i in range(nx):
            a0=j*(nx+1)+i;face=(a0,a0+1,a0+nx+2,a0+nx+1)
            faces.append(tuple(reversed(face)));faces.append(tuple(v+n for v in face))
    ring=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    for i,a0 in enumerate(ring):
        b0=ring[(i+1)%len(ring)];faces.append((a0,b0,b0+n,a0+n))
    ob=primitives.mesh_obj(name,verts,faces,coll,mat)
    from ..geometry import surfaces
    surfaces.grain_uv(ob,[((v.co.y-y)/width+.5,(v.co.x-a)/8) for v in ob.data.vertices])
    ob.data.materials[0]=surfaces.variant(mat,seed%5)
    ob['wood_floor']=True;ob['broken_plank']=broken or broken_left
    ob['madera']=True;ob['wood_damage']=runtime.settings.wood_damage
    return ob


def build(coll,p,scene):
    'IA: Solo Habitación; planta baja sobre rastreles y entreplanta a layout.upper_floor(p) sobre vigas reales; nunca cubre zonas sin anclajes.'
    meta.put(scene,'suelos_generados',[])
    meta.put(scene,'escalera_generada',{})
    if p.layout_mode!='ROOM':return
    walls={w['id']:w for w in meta.get(scene,'paredes_generadas',[])}
    if not all(k in walls for k in ('left','right','back')):return
    xmin=walls['left']['origin'][0]+p.thickness/2-.6
    xmax=walls['right']['origin'][0]-p.thickness/2+.6
    ymin=p.thickness/2-.6;ymax=walls['back']['origin'][1]-p.thickness/2+.6
    from . import stairs
    stair=stairs.plan(p,(xmin,xmax,ymin,ymax))
    opening=stair['opening'] if stair and 'error' not in stair else None
    # Las vigas transversales terminan sobre el cabecero, nunca atraviesan la escalera.
    if opening:
        for ob in coll.objects:
            if primitives.piece_key(ob)=='Madera · viga de planta':
                co=primitives.coords(ob);cx=(co[:,0].min()+co[:,0].max())/2
                if opening[0]-2<cx<opening[1]+2:
                    primitives.clip_closed(ob,(0,stair['y0']-2.4,0),(0,1,0))
    wood=primitives.material('Madera · suelo',(.30,.205,.115))
    records=[]
    for level,enabled,top in ((0,p.ground_floor,3.2),(1,p.upper_floor and p.floor_beams and p.height_type=='TWO',layout.upper_floor(p))):
        if not enabled:continue
        if level==0:
            count=max(2,math.ceil((xmax-xmin)/24))
            anchors=[xmin+(xmax-xmin)*i/count for i in range(count+1)]
            for x in anchors:
                ob=timber.timber_beam(coll,wood,'Madera · rastrel de planta baja',(x,ymin,.975),(x,ymax,.975),1.55,2.4,p.seed+round(x*10))
                ob['wood_floor']=True
        else:
            anchors=sorted(b['x'] for b in meta.get(scene,'vigas_generadas',[]) if b['wall']=='front')
            if len(anchors)<2 or anchors[-1]-anchors[0]<(xmax-xmin)*.7:
                # Bastidor interior autoportante cuando los muros han perdido sus alojamientos.
                extra=[xmin+2+(xmax-xmin-4)*i/4 for i in range(5)]
                extra=[x for x in extra if all(abs(a-x)>4 for a in anchors)]
                anchors=sorted(anchors+extra)
                for j,x in enumerate(extra):
                    end=stair['y0']-2.4 if opening and min(opening[0]-2,stair['approach'][0])<x<max(opening[1]+2,stair['approach'][1]) else ymax-1
                    for y in (ymin+1,end):
                        timber.timber_beam(coll,wood,'Madera · poste forjado',(x,y,.7),(x,y,(layout.upper_floor(p)-3.6)),3.6,3.6,p.seed+29100+j)
                    timber.timber_beam(coll,wood,'Madera · viga forjado',(x,ymin,(layout.upper_floor(p)-3.6)),(x,end+.3,(layout.upper_floor(p)-3.6)),4.2,4.7,p.seed+29200+j)
        rows=max(2,math.ceil((ymax-ymin)/5.5));pitch=(ymax-ymin)/rows
        left_tree=openings.wall_tree(coll,walls['left']);right_tree=openings.wall_tree(coll,walls['right'])
        made=0;broken_count=0
        holes=spatial.floor_holes(p,(xmin,xmax,ymin,ymax),level)
        for row in range(rows):
            y=ymin+(row+.5)*pitch
            joints=list(anchors)
            if level:
                for wallid,tree,x in (('left',left_tree,xmin),('right',right_tree,xmax)):
                    if openings.wall_hit(tree,walls[wallid],p,y,top-2.5):joints.append(x)
                joints=sorted(set(joints))
            # Juntas a matajunta: una o dos luces de viga por tablón.
            ids=[0]+list(range(1 if row%2 else 2,len(joints)-1,2))+[len(joints)-1]
            for piece,(ia,ib) in enumerate(zip(ids,ids[1:])):
                a,b=joints[ia],joints[ib]
                if b-a<2:continue
                rect=opening if level else None
                # Todo el ancho de la tabla deja libre el hueco de escalera.
                if rect:rect=[min(rect[0],stair['landing'][0]),max(rect[1],stair['landing'][1]),rect[2]-pitch/2,rect[3]+pitch/2]
                board_holes=holes
                if not level and opening and stair['approach'][2]-pitch/2<y<stair['approach'][3]+pitch/2:
                    board_holes=[h for h in holes if h[0]+h[2]<stair['approach'][0] or h[0]-h[2]>stair['approach'][1]]
                for part,(aa,bb) in enumerate(spatial.cut_intervals(a,b,y,board_holes,rect)):
                    left=aa>a+.01;right=bb<b-.01
                    if level and not any(aa-.5<=x<=bb+.5 for x in joints):continue
                    plank(coll,wood,'Madera · suelo %s tabla %s.%s.%s'%(level,row,piece,part),aa if left else aa-.35,bb if right else bb+.35,y,pitch-.12,top,p.seed+row*101+piece+level*7001,p.wood_grain,right,left)
                    made+=1;broken_count+=int(left or right)
        records.append({'level':level,'boards':made,'broken':broken_count,'top_mm':top,'anchors':anchors,'holes':[list(h) for h in holes]})
    meta.put(scene,'suelos_generados',records)
    stairs.build(coll,p,scene,stair)
