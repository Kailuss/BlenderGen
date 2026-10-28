"""Reconstruye capturas de poses intermedias sin ejecutar nuevamente Bullet."""
import sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from blender_v032 import render
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['45']
last=int(args[0]);sample=np.load(ROOT/f'reports/meteor_v2_poses_{last}.npz')
poses=sample['poses'];names=sample['names'].tolist()
lab=next(s for s in bpy.data.scenes if s.get('ruinas_physics_lab'));source={o.name:o for o in lab.objects if o.type=='MESH'}
s=bpy.data.scenes.new('Control de poses');bpy.context.window.scene=s
pairs=[]
for i,name in enumerate(names):
    original=source.get(name)
    if original is None:continue
    ob=bpy.data.objects.new(name+' control',original.data);s.collection.objects.link(ob);ob.rotation_mode='QUATERNION';pairs.append((i,ob))
frames=sorted(set((1,30,min(36,last),last)))
for f in frames:
    for i,ob in pairs:ob.location=poses[f-1,i,:3];ob.rotation_quaternion=Quaternion(poses[f-1,i,3:7]);ob.scale=poses[f-1,i,7:]
    render(s,ROOT/f'reports/meteor_v2_control_{f:03d}.png',focus=(0,.055,.195),location=(.65,.90,.6),scale=.60)
meteor=next((i for i,n in enumerate(names) if source.get(n) and source[n].get('impactor')),None)
drift=np.linalg.norm(poses[29,:,:3]-poses[0,:,:3],axis=1)*1000
report={'frame':last,'preimpact_max_mm':float(drift.max()),'meteor_positions':{str(f):poses[f-1,meteor,:3].tolist() for f in range(30,last+1)},'moved_over_10mm':int((np.linalg.norm(poses[-1,:,:3]-poses[0,:,:3],axis=1)>.01).sum())}
(ROOT/f'reports/meteor_v2_control_{last}.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report),flush=True)
