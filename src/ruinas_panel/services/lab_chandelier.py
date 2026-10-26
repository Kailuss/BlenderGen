"""Lámpara escénica de tres velas; curvas sin coste de colisión Bullet."""
import math
import bpy
from mathutils import Vector


def material(name,color,metallic=0,emission=0):
    'IA: Material visual propio compartido; no altera los materiales constructivos.'
    mat=bpy.data.materials.get(name)
    if mat:return mat
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True
    node=mat.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Metallic'].default_value=metallic;node.inputs['Roughness'].default_value=.38
    node.inputs['Emission Color'].default_value=(*color,1);node.inputs['Emission Strength'].default_value=emission
    return mat


def tube(scene,parent,name,points,radius,mat,cyclic=False):
    'IA: Tubo visual de curva cerrada en extremos; se excluye de cuerpos físicos e impresión.'
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=2;data.use_fill_caps=True
    spline=data.splines.new('POLY');spline.points.add(len(points)-1)
    for point,co in zip(spline.points,points):point.co=(*co,1)
    spline.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.parent=parent;ob['lab_decor']=True;data.materials.append(mat)
    return ob


def create(scene,ceiling):
    'IA: Cuelga tres velas del centro inferior de la pieza seleccionada; sigue su pose y añade balanceo artístico, no cadena física ni colisiones.'
    if ceiling is None or ceiling.name not in scene.objects or ceiling.type!='MESH' or ceiling.get('impactor') or ceiling.get('physical_role')=='ground':
        raise ValueError('Selecciona una pieza del techo o una viga del laboratorio.')
    existing=next((o for o in scene.objects if o.get('lab_chandelier') and o.parent==ceiling),None)
    if existing:return existing
    p=scene.ruin_settings;drop=p.chandelier_drop_mm*.001;scale=drop/.025;radius=.010*scale
    points=[ceiling.matrix_world@Vector(v) for v in ceiling.bound_box]
    anchor=Vector(((min(v.x for v in points)+max(v.x for v in points))/2,(min(v.y for v in points)+max(v.y for v in points))/2,min(v.z for v in points)))
    pivot=bpy.data.objects.new('Lámpara · suspensión',None);scene.collection.objects.link(pivot)
    pivot.parent=ceiling;pivot.matrix_parent_inverse=ceiling.matrix_world.inverted();pivot.location=anchor
    pivot['lab_decor']=True;pivot['lab_chandelier']=True;pivot['motion_model']='Decorative damped swing; follows support; no collision'
    iron=material('Lámpara · hierro',(.055,.04,.025),.75)
    wax=material('Lámpara · cera',(.85,.68,.39))
    flame=material('Lámpara · llama',(1,.32,.055),emission=4)
    tube(scene,pivot,'Lámpara · colgante',[(0,0,0),(0,0,-drop)],.00055*scale,iron)
    ring=[(radius*math.cos(i*math.tau/32),radius*math.sin(i*math.tau/32),-drop) for i in range(32)]
    tube(scene,pivot,'Lámpara · aro',ring,.0008*scale,iron,True)
    lights=[]
    for i in range(3):
        angle=i*math.tau/3;x=radius*math.cos(angle);y=radius*math.sin(angle)
        tube(scene,pivot,'Lámpara · brazo',[(0,0,-drop*.7),(x*.6,y*.6,-drop),(x,y,-drop)],.00065*scale,iron)
        tube(scene,pivot,'Lámpara · vela',[(x,y,-drop),(x,y,-drop+.0055*scale)],.0013*scale,wax)
        tube(scene,pivot,'Lámpara · llama',[(x,y,-drop+.0055*scale),(x,y,-drop+.0075*scale)],.0005*scale,flame)
        data=bpy.data.lights.new('Vela · luz cálida','POINT');data.color=(1,.48,.16);data.shadow_soft_size=.0015*scale
        ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob);ob.parent=pivot;ob.location=(x,y,-drop+.008*scale);ob['lab_decor']=True
        lights.append(data)
    fps=scene.render.fps/scene.render.fps_base;duration=max(scene.frame_end,1+round(10*fps));amplitude=math.radians(p.chandelier_sway_deg)
    frames=sorted(set(range(1,duration+1,2))|{duration})
    for frame in frames:
        t=(frame-1)/fps
        pivot.rotation_euler=(amplitude*math.sin(t*3.6)*math.exp(-t*.035),amplitude*.6*math.sin(t*2.8+.4)*math.exp(-t*.035),0)
        pivot.keyframe_insert(data_path='rotation_euler',frame=frame)
        for i,data in enumerate(lights):
            data.energy=.035*scale*scale*(1+.18*math.sin(t*13.7+i*2)+.09*math.sin(t*29.3+i))
            data.keyframe_insert(data_path='energy',frame=frame)
    scene.frame_set(scene.frame_current)
    return pivot
