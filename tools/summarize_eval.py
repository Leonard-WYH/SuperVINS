import json,pathlib,sys,zipfile,numpy as np
run=pathlib.Path(sys.argv[1]);result={}
for name in ['vio','loop','pose_graph','vio_keyframes']:
 with zipfile.ZipFile(run/'evaluation'/f'{name}_ape.zip') as z:
  result[name]={'stats':json.loads(z.read('stats.json')),'info':json.loads(z.read('info.json'))}
  import io
  transform=np.load(io.BytesIO(z.read('alignment_transformation_sim3.npy')))
  result[name]['alignment_SE3']=transform.tolist()
  result[name]['associated_poses']=len(np.load(io.BytesIO(z.read('error_array.npy'))))
  from evo.tools import file_interface
  source={'vio':'vio.csv','loop':'loop_corrected_tum.txt','pose_graph':'vio_loop.csv','vio_keyframes':'vio_at_keyframes.tum'}[name]
  track=file_interface.read_tum_trajectory_file(str(run/source));track.transform(transform);file_interface.write_tum_trajectory_file(str(run/'evaluation'/f'{name}_aligned.tum'),track)
  # Keep exact evaluated aligned poses from EVO's result archive.
  for f in z.namelist():
   if f.endswith('.tum'): (run/'evaluation'/f'{name}_{pathlib.Path(f).name}').write_bytes(z.read(f))
resources=json.loads((run/'resources.json').read_text())
result['cpu']={}
for node in ['vio','loop','rviz','rosbag']:
 vals=[r['nodes'][node] for r in resources if node in r.get('nodes',{})]
 if vals:result['cpu'][node]={'mean_cpu_pct':float(np.mean([r['cpu_pct'] for r in vals])),'p95_cpu_pct':float(np.percentile([r['cpu_pct'] for r in vals],95)),'max_rss_mib':max(r['rss_mib'] for r in vals),'scope':vals[-1].get('scope','direct launched PID only; child executables excluded')}
gpu=[]
for r in resources:
 try:gpu.append(list(map(float,r['gpu'].split(','))))
 except (KeyError,ValueError):pass
if gpu:
 v=np.array(gpu);result['whole_gpu']={'mean_utilization_pct':float(v[:,0].mean()),'max_memory_mib':float(v[:,1].max()),'mean_power_w':float(v[:,2].mean()),'note':'whole-device values include desktop and any background applications; process GPU memory is in resources.json'}
result['gpu_process_memory']={}
for name in ['vio','loop','rviz','rosbag']:
 vals=[]
 for sample in resources:
  n=sample.get('nodes',{}).get(name,{})
  ids=set(n.get('pids',[n.get('pid')]))
  total=0.;matched=False
  for row in sample.get('gpu_processes','').splitlines():
   try:
    pid,mem=row.split(',');pid=int(pid);mem=float(mem)
    if pid in ids:total+=mem;matched=True
   except ValueError:continue
  if matched:vals.append(total)
 if vals:result['gpu_process_memory'][name]={'max_mib':max(vals),'mean_mib':float(np.mean(vals))}
result['runtime']=json.loads((run/'runtime_summary.json').read_text());(run/'evaluation/summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(8,6))
gt=file_interface.read_tum_trajectory_file(str(run.parents[1]/'data/groundtruth_tum.txt'))
ax.plot(gt.positions_xyz[:,0],gt.positions_xyz[:,1],color='black',lw=2,label='EuRoC ground truth')
for name,color in [('vio','green'),('loop','darkorange'),('pose_graph','red')]:
 t=file_interface.read_tum_trajectory_file(str(run/'evaluation'/f'{name}_aligned.tum'));ax.plot(t.positions_xyz[:,0],t.positions_xyz[:,1],color=color,lw=1.2,label=name)
ax.set(xlabel='x [m]',ylabel='y [m]',title='V2_01_easy: SE(3)-aligned trajectories');ax.axis('equal');ax.grid(alpha=.3);ax.legend();fig.tight_layout();fig.savefig(run/'evaluation/trajectories_xy.png',dpi=180);plt.close(fig)
