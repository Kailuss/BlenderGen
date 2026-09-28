"""Arrays de transformaciones y variantes compartidas; recortes singulares siguen siendo mallas."""
import math
import zlib
import bpy
import numpy as np
from mathutils import Vector, Matrix
from . import primitives, weather, fracture
from .. import config, runtime, meta


def cleanup():
    'IA: Retira bibliotecas GN sin usuarios tras borrar la fuente; nunca borra las referenciadas por otro muro.'
    for group in list(bpy.data.node_groups):
        if group.get('ruin_instances') and group.users==0:
            bpy.data.node_groups.remove(group)
    for coll in list(bpy.data.collections):
        if coll.get('ruin_library') and coll.users==0:
            primitives.remove_objects(coll.objects)
            bpy.data.collections.remove(coll)


def array_attribute(mesh,name,kind,values):
    'IA: Escribe arrays contiguos por punto; evita asignaciones RNA por ladrillo.'
    attr=mesh.attributes.new(name,kind,'POINT')
    attr.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(values).ravel())


def node_array(ob,library):
    'IA: Instancia hijos ordenados de biblioteca; no insertes Realize Instances en la vista de edición.'
    tree=bpy.data.node_groups.new('Ruinas · arrays de ladrillos','GeometryNodeTree')
    tree['ruin_instances']=True
    tree.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links=tree.nodes,tree.links
    inp=nodes.new('NodeGroupInput');inp.location=(-500,200)
    out=nodes.new('NodeGroupOutput');out.location=(300,200)
    source=nodes.new('GeometryNodeCollectionInfo');source.location=(-500,-50)
    source.inputs['Collection'].default_value=library
    source.inputs['Separate Children'].default_value=True
    source.inputs['Reset Children'].default_value=True
    inst=nodes.new('GeometryNodeInstanceOnPoints');inst.location=(60,200)
    inst.inputs['Pick Instance'].default_value=True
    links.new(inp.outputs['Geometry'],inst.inputs['Points'])
    links.new(source.outputs['Instances'],inst.inputs['Instance'])
    for i,(name,kind,socket) in enumerate((('ruin_index','INT','Instance Index'),('ruin_scale','FLOAT_VECTOR','Scale'),('ruin_rotation','FLOAT_VECTOR','Rotation'))):
        attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type=kind
        attr.inputs['Name'].default_value=name;attr.location=(-240,-100-i*180)
        links.new(attr.outputs['Attribute'],inst.inputs[socket])
    links.new(inst.outputs['Instances'],out.inputs['Geometry'])
    ob.modifiers.new('Array procedural · Geometry Nodes','NODES').node_group=tree


def build(coll,p):
    'IA: Reemplaza cajas ligeras por arrays; calcula desgaste/grietas una vez por variante y conserva recortes únicos.'
    cleanup()
    library=bpy.data.collections.new('Ruinas · biblioteca de variantes')
    library['ruin_library']=True
    templates={};records=[];discard=[]
    full_damage=runtime.quality in config.DAMAGE_QUALITIES
    for ob in list(coll.objects):
        if ob.get('architectural_cut') or not ob.get('ruin_box') or len(ob.data.vertices)!=8 or len(ob.data.polygons)!=6 or ob.get('borde_agujero') or ob.get('mortero_erosionado') or ob.get('escombro') or ob.get('protected_sill'):
            continue
        wall=ob.get('wall_id','front')
        angle=math.pi/2 if wall in ('left','right') else 0.0
        # Girar 180° mantiene determinante positivo y pone las grietas en la cara exterior.
        if wall in ('left','back'):angle+=math.pi
        rot=np.array(Matrix.Rotation(angle,3,'Z'))
        co=primitives.coords(ob)@rot
        low,high=co.min(axis=0),co.max(axis=0)
        span=high-low
        if min(span)<.05:continue
        mid=(low+high)/2
        stone=ob.data.materials[0].name.startswith('Piedra')
        pillar=primitives.piece_key(ob).startswith('Pilar') and 'sillar' in primitives.piece_key(ob)
        fixed=bool(ob.get('connection_face')) and not pillar
        key=zlib.crc32(primitives.piece_key(ob).encode())
        variant=(key+p.seed)%8
        if pillar:variant%=4
        cracked=stone and not fixed and full_damage and (key%1000)/1000 < min(.95,p.cracks*.95)
        ratio=span[0]/span[2]
        shape=0 if ratio<.8 else (1 if ratio<2.6 else 2)
        # Tres familias de proporciones, ocho variantes: el coste de acabado no crece por ladrillo.
        pillar_size=tuple(np.maximum(2,2*np.round(span/2))) if pillar else None
        signature=(ob.data.materials[0].name,shape,variant if stone and not fixed else 0,cracked,fixed,pillar_size)
        if signature not in templates:
            size=np.array(([4.5,14,6],[12,14,6],[24,14,6])[shape]) if stone else span.copy()
            if pillar:size=np.array(pillar_size)
            index=len(templates)
            template=primitives.block('Piedra variante' if stone else 'Mortero variante',-size[0]/2,size[0]/2,-size[1]/2,size[1]/2,-size[2]/2,size[2]/2,library,ob.data.materials[0])
            template['ruin_pillar']=pillar
            if stone and not fixed:
                weather.weather_stone(template,p.wear,p.seed+variant*937+shape*17)
                if cracked:
                    fracture.crack_stone(template,p.cracks,p.seed+variant*331+shape*89,library,ob.data.materials[0],(Vector((1,0,0)),Vector((0,-1,0))))
                    if pillar:
                        for i,(along,normal) in enumerate((((0,1,0),(1,0,0)),((1,0,0),(0,1,0)),((0,1,0),(-1,0,0)))):
                            fracture.crack_stone(template,p.cracks,p.seed+variant*331+123+i*67,library,ob.data.materials[0],(Vector(along),Vector(normal)))
            if stone:
                from . import surfaces
                template.data.materials[0]=surfaces.variant(ob.data.materials[0],variant%5)
            template['ruin_pillar']=pillar
            template['ruin_cracked']=cracked
            template.name='RUIN_VARIANT_%04d'%index
            templates[signature]=(index,template,size)
        index,template,size=templates[signature]
        records.append((mid@rot.T,span/size,(0,0,angle),index,primitives.piece_key(ob)))
        discard.append(ob)
    primitives.remove_objects(discard)
    # Piezas recortadas, rotas y escombros conservan su forma y su semilla propia.
    for ob in list(coll.objects):
        if ob.get('ruin_bevel'):
            primitives.bevel(ob,ob['ruin_bevel'])
        if ob.get('ruin_weather'):
            amount,seed=ob['ruin_weather']
            weather.weather_stone(ob,amount,int(seed))
    fracture.apply_damage(coll,p)
    if not records:
        bpy.data.collections.remove(library)
        return None
    ob=primitives.mesh_obj('MURO · array de instancias',[r[0] for r in records],[],coll,discard_material(library))
    ob['ruin_instances']=True
    ob['ruin_library']=library.name
    array_attribute(ob.data,'ruin_scale','FLOAT_VECTOR',[r[1] for r in records])
    array_attribute(ob.data,'ruin_rotation','FLOAT_VECTOR',[r[2] for r in records])
    array_attribute(ob.data,'ruin_index','INT',[r[3] for r in records])
    array_attribute(ob.data,'ruin_piece_id','INT',list(range(len(records))))
    import json
    ob['ruin_keys']=json.dumps([r[4] for r in records],ensure_ascii=False)
    faces={index:len(template.data.polygons) for index,template,size in templates.values()}
    ob['ruin_expanded_faces']=sum(faces[r[3]] for r in records)
    # La colección se enumera por nombre; los prefijos numéricos fijan los índices GN.
    node_array(ob,library)
    meta.put(bpy.context.scene,'instancias_generadas',{'pieces':len(records),'variants':len(templates)})
    return ob


def discard_material(library):
    'IA: Material auxiliar de puntos; las instancias usan los materiales de sus plantillas.'
    return next(iter(library.objects)).data.materials[0]


def expanded_faces(coll):
    'IA: Cuenta caras equivalentes antes de realizar instancias para comprobar el presupuesto de exportación.'
    return sum(int(ob.get('ruin_expanded_faces',len(ob.data.polygons))) for ob in coll.objects)


def export_copies(ob,coll,density=1):
    'IA: Materializa piezas GN solo tras validar presupuesto; devuelve copias independientes para unión exacta.'
    library=bpy.data.collections[ob['ruin_library']]
    templates=sorted(library.objects,key=lambda item:item.name)
    reduced=[];result=[]
    try:
        for template in templates:reduced.append(primitives.reduced_copy(template,density))
        for i,v in enumerate(ob.data.vertices):
            idx=ob.data.attributes['ruin_index'].data[i].value
            scale=ob.data.attributes['ruin_scale'].data[i].vector
            rotation=ob.data.attributes['ruin_rotation'].data[i].vector
            source=reduced[idx]
            clone=source.copy();clone.data=source.data.copy();coll.objects.link(clone)
            result.append(clone)
            matrix=Matrix.Translation(v.co)@Matrix.Rotation(rotation.z,4,'Z')@Matrix.Diagonal((*scale,1))
            clone.data.transform(ob.matrix_world@matrix)
    except Exception:
        primitives.remove_objects(result)
        raise
    finally:
        primitives.remove_objects(reduced)
    return result
