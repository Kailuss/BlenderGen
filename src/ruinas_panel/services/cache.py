"""services /cache — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import config
from .. import runtime
from ..structure import layout
import bpy


def clear_cache(quality=None):
    'IA: Elimina plantillas y sus mallas; no borres objetos de la fuente activa.'
    keys=[quality] if quality else list(runtime.cache)
    for key in keys:
        entry=runtime.cache.pop(key,None)
        if not entry:
            continue
        for ob in entry['objects']:
            mesh=ob.data
            bpy.data.objects.remove(ob,do_unlink=True)
            if mesh.users==0:
                bpy.data.meshes.remove(mesh)


def clear_source():
    'IA: Elimina solo la colección procedural conocida y mallas sin usuarios.'
    coll=bpy.data.collections.get(config.COLLECTION)
    if not coll:
        return
    for ob in list(coll.objects):
        mesh=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if mesh.users==0:
            bpy.data.meshes.remove(mesh)
    bpy.data.collections.remove(coll)


def cache_signature(context,p):
    'IA: Incluye parámetros de geometría; excluye solo daños que se reaplican sobre copia limpia.'
    ignored=set(config.CRACK_FIELDS)|{'preview_quality','export_quality','quick_edit'}
    return (context.scene.as_pointer(),runtime.quality,layout.distribution_seed(p),tuple((k,getattr(p,k)) for k in config.FIELDS if k not in ignored))


def save_cache(context,coll,signature):
    'IA: Guarda copia anterior a grietas y metadatos; no acumules desgaste sobre el resultado visible.'
    clear_cache(runtime.quality)
    templates=[]
    for ob in coll.objects:
        copy=ob.copy()
        copy.data=ob.data.copy()
        copy.name='__RUIN_CACHE__'+ob.name
        copy['_source_name']=ob.name
        templates.append(copy)
    runtime.cache[runtime.quality]={'signature':signature,'objects':templates,'metadata':{k:context.scene[k] for k in config.CACHE_METADATA if k in context.scene}}


def restore_cache(context):
    'IA: Clona plantillas y restaura metadatos; nunca edites la plantilla en sitio.'
    clear_source()
    coll=bpy.data.collections.new(config.COLLECTION)
    context.scene.collection.children.link(coll)
    for template in runtime.cache[runtime.quality]['objects']:
        ob=template.copy()
        ob.data=template.data.copy()
        ob.name=template['_source_name']
        ob.hide_render=False
        coll.objects.link(ob)
        ob.hide_set(False)
    for key,value in runtime.cache[runtime.quality]['metadata'].items():
        context.scene[key]=value
    return coll
