"""Correcciones de presentación sobre la reproducción y cachés ya calculadas."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/Ejercicio02_metralla_20261028'


def run():
    'IA: Reancla lámparas al centro inferior local de su viga y ajusta densidad óptica sin modificar poses Bullet, fuentes ni cachés Mantaflow; guarda antes del render de control.'
    scene=bpy.context.scene;scene.frame_set(1)
    scene.camera.data.lens=38
    lamps=[]
    for ob in scene.objects:
        if ob.get('lab_chandelier'):
            assert ob.parent and ob.parent.type=='MESH'
            points=[Vector(p) for p in ob.parent.bound_box]
            ob.matrix_parent_inverse=Matrix.Identity(4)
            ob.location=((min(p.x for p in points)+max(p.x for p in points))/2,(min(p.y for p in points)+max(p.y for p in points))/2,min(p.z for p in points))
            lamps.append(ob.name)
        if ob.get('lab_smoke_domain'):
            for node in ob.data.materials[0].node_tree.nodes:
                if node.type=='MATH':node.inputs[1].default_value=80
    bpy.context.view_layer.update()
    for frame in (1,135,241):
        scene.frame_set(frame);bpy.context.view_layer.update()
        for name in lamps:
            ob=scene.objects[name]
            target=ob.parent.matrix_world@ob.location
            assert (ob.matrix_world.translation-target).length<1e-6
    scene.frame_set(1)
    config=json.loads((OUT/'render_config.json').read_text(encoding='utf8'))
    config.update(optical_density_multiplier=80,chandeliers_reanchored=lamps)
    (OUT/'render_config.json').write_text(json.dumps(config,indent=2),encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'05_render_listo.blend'))
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
    for device in pref.devices:device.use=device.type=='OPTIX' and '3090' in device.name
    scene.frame_set(135);scene.cycles.samples=128
    scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(ROOT/'reports/ejercicio02_render_135.png')
    bpy.ops.render.render(write_still=True)
    print('FINISH_REFINED',lamps,flush=True)


if __name__=='__main__':run()
