"""services /cache — ver docs/ARCHITECTURE.md para contratos y dependencias."""

from .. import meta
from .. import config
from .. import runtime
from ..geometry import primitives
from ..structure import layout
import bpy


def cache_key():
    'IA: Ranura de caché por calidad y modo: la vista previa omite biseles que la exportación sí aplica.'
    return (runtime.quality,runtime.preview)


def clear_cache(key=None):
    'IA: Elimina plantillas y sus mallas de una ranura o de todas; no borres objetos de la fuente activa.'
    keys=[key] if key else list(runtime.cache)
    for key in keys:
        entry=runtime.cache.pop(key,None)
        if not entry:
            continue
        primitives.remove_objects(entry['objects'])


def forget_cache():
    'IA: Suelta las referencias a plantillas sin tocar datos Blender; úsalo cuando undo o una carga de archivo las invalidan.'
    runtime.cache.clear()


def purge_orphan_templates():
    'IA: Borra plantillas huérfanas buscándolas por prefijo en bpy.data; no actúa si la caché sigue en uso.'
    if runtime.cache:
        return
    primitives.remove_objects(o for o in bpy.data.objects if o.name.startswith(config.CACHE_PREFIX) and o.users==0)


def clear_source():
    'IA: Elimina solo la colección procedural conocida y mallas sin usuarios.'
    coll=bpy.data.collections.get(config.COLLECTION)
    if not coll:
        return
    primitives.remove_objects(coll.objects)
    bpy.data.collections.remove(coll)


def cache_signature(context,p):
    'IA: Incluye parámetros de geometría; excluye solo daños que se reaplican sobre copia limpia.'
    ignored=set(config.CRACK_FIELDS)|{'preview_quality','export_quality','quick_edit'}
    if runtime.quality not in config.DAMAGE_QUALITIES:
        # Sin daño en esta calidad: cambiar desgaste o escombros no invalida la geometría guardada.
        ignored|={'wear','wear_level','rubble_amount'}
    return (context.scene.as_pointer(),runtime.quality,layout.distribution_seed(p),tuple((k,getattr(p,k)) for k in config.FIELDS if k not in ignored))


def save_cache(context,coll,signature):
    'IA: Guarda copia anterior a grietas y metadatos; no acumules desgaste sobre el resultado visible.'
    clear_cache(cache_key())
    templates=[]
    for ob in coll.objects:
        copy=ob.copy()
        copy.data=ob.data.copy()
        copy.name=config.CACHE_PREFIX+ob.name
        copy['_source_name']=ob.name
        templates.append(copy)
    runtime.cache[cache_key()]={'signature':signature,'objects':templates,'metadata':{k:meta.raw(context.scene,k) for k in config.CACHE_METADATA if meta.raw(context.scene,k) is not None}}


def restore_cache(context):
    'IA: Clona plantillas y restaura metadatos; nunca edites la plantilla en sitio.'
    clear_source()
    coll=bpy.data.collections.new(config.COLLECTION)
    context.scene.collection.children.link(coll)
    for template in runtime.cache[cache_key()]['objects']:
        ob=template.copy()
        ob.data=template.data.copy()
        ob.name=template['_source_name']
        ob.hide_render=False
        coll.objects.link(ob)
        ob.hide_set(False)
    for key,value in runtime.cache[cache_key()]['metadata'].items():
        meta.put_raw(context.scene,key,value)
    return coll
