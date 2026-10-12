import sys,pathlib,numpy as np
run=pathlib.Path(sys.argv[1]);
if not run.is_absolute():run=pathlib.Path(__file__).resolve().parents[1]/run
vio=np.loadtxt(run/'vio.csv');pg=np.loadtxt(run/'vio_loop.csv');indices=np.searchsorted(vio[:,0],pg[:,0]);indices=np.minimum(indices,len(vio)-1);before=np.maximum(indices-1,0);choose=np.abs(vio[before,0]-pg[:,0])<np.abs(vio[indices,0]-pg[:,0]);indices[choose]=before[choose]
if np.max(np.abs(vio[indices,0]-pg[:,0]))>1e-4:raise RuntimeError('Pose graph timestamps do not match VIO')
np.savetxt(run/'vio_at_keyframes.tum',vio[indices],fmt='%.9f')
