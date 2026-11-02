"""Control numérico temprano del ejercicio sin abrir Blender ni recalcular física."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def run(frame):
    'IA: Compara poses guardadas por el trabajador; excluye proyectiles y exige reposo previo, rotación estable y escala constante.'
    sample=np.load(ROOT/f'reports/shrapnel_poses_{frame}.npz')
    poses=sample['poses'];names=sample['names'].tolist()
    mask=np.array([not name.startswith('Metralla · ') for name in names])
    before=poses[0,mask];rest=poses[29,mask];after=poses[-1,mask]
    drift=np.linalg.norm(rest[:,:3]-before[:,:3],axis=1)*1000
    dot=np.abs(np.sum(rest[:,3:7]*before[:,3:7],axis=1))
    angles=np.degrees(2*np.arccos(np.clip(dot,0,1)))
    moved=np.linalg.norm(after[:,:3]-before[:,:3],axis=1)*1000
    labels=np.array(names)[mask]
    report=dict(frame=frame,preimpact_max_mm=float(drift.max()),
                preimpact_max_deg=float(angles.max()),
                moved_over_5mm=int((moved>5).sum()),
                scale_error=float(np.max(np.abs(after[:,7:]-before[:,7:]))),
                worst_preimpact=[dict(name=str(labels[i]),mm=float(drift[i])) for i in np.argsort(drift)[-8:][::-1]])
    (ROOT/f'reports/shrapnel_control_{frame}.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    assert report['preimpact_max_mm']<2,report
    assert report['preimpact_max_deg']<2,report
    assert report['scale_error']<1e-5,report


if __name__=='__main__':run(int(sys.argv[1]))
