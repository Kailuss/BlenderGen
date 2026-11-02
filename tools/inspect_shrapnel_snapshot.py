"""Inspección visual de poses intermedias sin repetir Bullet."""
import sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from blender_v032 import render


def run(frame):
    'IA: Crea una escena de diagnóstico con las mallas existentes y las poses capturadas, sin cuerpos físicos ni cambios guardados en el laboratorio.'
    sample=np.load(ROOT/f'reports/shrapnel_poses_{frame}.npz');poses=sample['poses'];names=sample['names'].tolist()
    lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'))
    source={o.name:o for o in lab.objects if o.type=='MESH' and not o.get('collision_floor') and not o.get('lab_collision_proxy')}
    scene=bpy.data.scenes.new('Control metralla');bpy.context.window.scene=scene
    for i,name in enumerate(names):
        original=source.get(name)
        if original is None:continue
        ob=bpy.data.objects.new(name+' control',original.data);scene.collection.objects.link(ob)
        ob.rotation_mode='QUATERNION';pose=poses[-1,i]
        ob.location=pose[:3];ob.rotation_quaternion=Quaternion(pose[3:7]);ob.scale=pose[7:]
    render(scene,ROOT/f'reports/shrapnel_control_{frame:03d}.png',focus=(0,.12,.23),location=(.60,-.70,.60),scale=.72)
    print('SNAPSHOT_RENDERED',frame,flush=True)


if __name__=='__main__':run(int(sys.argv[sys.argv.index('--')+1]))
