#!/usr/bin/env python3
import argparse,json,pathlib,re,collections
import numpy as np
p=argparse.ArgumentParser();p.add_argument('run',type=pathlib.Path);a=p.parse_args();report={}
for f in ['vio.csv','loop_corrected_tum.txt','vio_loop.csv']:
 x=np.loadtxt(a.run/f,comments='#');x=np.atleast_2d(x)
 if x.shape[1]!=8 or len(x)<10 or not np.isfinite(x).all():raise RuntimeError('Invalid TUM trajectory '+f)
 if not np.all(np.diff(x[:,0])>0):raise RuntimeError('Nonmonotonic trajectory '+f)
 q=np.linalg.norm(x[:,4:8],axis=1)
 if np.max(np.abs(q-1))>1e-3:raise RuntimeError('Nonunit quaternion '+f)
 report[f]={'poses':len(x),'first_stamp':float(x[0,0]),'last_stamp':float(x[-1,0]),'finite':True,'max_quaternion_norm_error':float(np.max(np.abs(q-1))),'position_min':x[:,1:4].min(axis=0).tolist(),'position_max':x[:,1:4].max(axis=0).tolist()}
loop=(a.run/'loop.log').read_text(errors='replace');vio=(a.run/'vio.log').read_text(errors='replace')
report['accepted_lightglue_loops']=re.findall(r'\[LightGlue Loop\] ACCEPTED:.*',loop)
report['gpu_inference_warnings']=re.findall(r'\[WARN\] Matcher GPU inference failed:.*',vio+loop)
report['initializer_successes']=len(re.findall('Initialization finish',vio))
report['pose_graph_4dof_solves']=[{'initial_cost':float(i),'final_cost':float(f),'termination':t.strip()} for i,f,t in re.findall(r'\[PoseGraph 4DoF\].*?Initial cost: ([\deE+.-]+), Final cost: ([\deE+.-]+), Termination: ([A-Z_]+)',loop)]
# Compare streaming VIO and corrected positions at common timestamps.
v=np.loadtxt(a.run/'vio.csv');l=np.loadtxt(a.run/'loop_corrected_tum.txt');common,vi,li=np.intersect1d(v[:,0],l[:,0],return_indices=True);report['common_timestamps']=len(common);report['max_loop_correction_m']=float(np.linalg.norm(v[vi,1:4]-l[li,1:4],axis=1).max())
(a.run/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if report['gpu_inference_warnings']:raise RuntimeError('GPU inference failures during dataset')
if not report['accepted_lightglue_loops'] or report['max_loop_correction_m']<1e-6:raise RuntimeError('Loop closure/optimization not demonstrated')
if report['pose_graph_4dof_solves'] and not all(s['final_cost']<=s['initial_cost'] for s in report['pose_graph_4dof_solves']):raise RuntimeError('Pose graph cost increased')
