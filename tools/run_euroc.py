#!/usr/bin/env python3
import argparse,collections,csv,json,math,os,pathlib,signal,socket,subprocess,time,xmlrpc.client
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--bag',type=pathlib.Path,default=ROOT/'data/V2_01_easy.bag');p.add_argument('--rate',type=float,default=1);p.add_argument('--duration',type=float);p.add_argument('--no-rviz',action='store_true');p.add_argument('--startup-only',action='store_true');a=p.parse_args()
if not a.startup_only and not a.bag.exists():raise RuntimeError('Missing EuRoC bag')
uri=os.environ['ROS_MASTER_URI'];port=int(uri.rsplit(':',1)[1]);probe=socket.socket()
if probe.connect_ex(('127.0.0.1',port))==0:raise RuntimeError('Master port already occupied; refusing to change existing ROS session')
probe.close();run=ROOT/'results'/('startup_' if a.startup_only else 'V2_01_easy_');run=run.with_name(run.name+time.strftime('%Y%m%d_%H%M%S'));run.mkdir(parents=True)
(run/'time_consumption').mkdir()
cfg=run/'euroc_mono_imu.yaml';subprocess.run(['/usr/bin/python3',str(ROOT/'scripts/configure_euroc.py'),'--output',str(run),'--config',str(cfg)],check=True)
processes=[];streams=[]
def start(name,args):
 f=(run/(name+'.log')).open('w');streams.append(f);proc=subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=run);processes.append((name,proc));return proc
counts=collections.Counter();stamps=collections.defaultdict(list);arrivals=collections.defaultdict(list);path_lengths={};resources=[];subs=[];start_wall=time.monotonic();last_odom_wall=None;bad_odometry=False
try:
 core=start('roscore',['roscore','-p',str(port)]);master=xmlrpc.client.ServerProxy(uri)
 for _ in range(100):
  try:
   if master.getPid('/reproduction')[0]==1:break
  except Exception:pass
  time.sleep(.1)
 else:raise RuntimeError('Master did not start')
 subprocess.run(['rosparam','set','/use_sim_time','true'],check=True)
 vio=start('vio',[str(ROOT/'devel/lib/supervins/supervins_node'),str(cfg)])
 loop=start('loop',[str(ROOT/'devel/lib/supervins_loop_fusion/supervins_loop_fusion_node'),str(cfg)])
 if not a.no_rviz:start('rviz',['roslaunch','supervins','supervins_rviz.launch'])
 import rospy
 from nav_msgs.msg import Odometry,Path
 from sensor_msgs.msg import Image
 rospy.init_node('supervins_reproduction_monitor',anonymous=True,disable_signals=True)
 def callback(msg,topic):
  global last_odom_wall,bad_odometry
  counts[topic]+=1;stamps[topic].append(msg.header.stamp.to_sec());arrivals[topic].append(time.monotonic())
  if isinstance(msg,Path):path_lengths[topic]=len(msg.poses)
  if isinstance(msg,Odometry):
   q=msg.pose.pose.orientation;t=msg.pose.pose.position
   if not all(math.isfinite(v) for v in [t.x,t.y,t.z,q.x,q.y,q.z,q.w]):bad_odometry=True
   last_odom_wall=time.monotonic()
 for topic,typ in [('/cam0/image_raw',Image),('/supervins_estimator/image_track',Image),('/supervins_estimator/odometry',Odometry),('/supervins_estimator/path',Path),('/supervins_loop_fusion/loop_corrected_path',Path),('/supervins_loop_fusion/pose_graph_path',Path)]:subs.append(rospy.Subscriber(topic,typ,callback,callback_args=topic,queue_size=100))
 for _ in range(120):
  if vio.poll() is not None or loop.poll() is not None:raise RuntimeError('SLAM node exited during startup')
  pubs={t for t,_ in rospy.get_published_topics()}
  if '/supervins_estimator/odometry' in pubs and '/supervins_loop_fusion/loop_corrected_path' in pubs:break
  time.sleep(.25)
 else:raise RuntimeError('SLAM nodes did not advertise outputs')
 print('READY',run,flush=True)
 player=None
 if not a.startup_only:
  args=['rosbag','play','--clock','--quiet','--delay=3','--rate='+str(a.rate)]
  if a.duration:args+=['--duration='+str(a.duration)]
  args+=[str(a.bag.resolve())];player=start('rosbag',args)
 cpu={name:psutil.Process(proc.pid) for name,proc in processes};tracked={}
 for v in cpu.values():v.cpu_percent()
 finished=None
 while True:
  now=time.monotonic()
  if vio.poll() is not None or loop.poll() is not None:raise RuntimeError('SLAM node exited')
  if bad_odometry:raise RuntimeError('Nonfinite odometry')
  sample={'wall_s':now-start_wall,'nodes':{}}
  for name,proc in cpu.items():
   try:
    members=[proc]+proc.children(recursive=True);pct=0.;rss=0.;pids=[]
    for member in members:
     if member.pid not in tracked:tracked[member.pid]=member;member.cpu_percent()
     member=tracked[member.pid];pct+=member.cpu_percent();rss+=member.memory_info().rss/2**20;pids.append(member.pid)
    sample['nodes'][name]={'pid':proc.pid,'pids':pids,'cpu_pct':pct,'rss_mib':rss,'scope':'process and descendants; RSS sum may double-count shared pages'}
   except psutil.Error:pass
  try:
   sample['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,power.draw','--format=csv,noheader,nounits'],text=True,timeout=3).strip()
   sample['gpu_processes']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=3).strip()
  except Exception as e:sample['gpu_error']=str(e)
  resources.append(sample)
  if a.startup_only and now-start_wall>20:break
  if player and player.poll() is not None:
   if player.returncode!=0:raise RuntimeError('rosbag play failed')
   if finished is None:finished=now
   # Allow CPU estimator and asynchronous pose graph to consume queues.
   if now-finished>15 and (last_odom_wall is None or now-last_odom_wall>5):break
   if now-finished>90:raise RuntimeError('Estimator backlog did not drain in 90 seconds')
  time.sleep(1)
 if not a.startup_only:
  for topic in ['/supervins_estimator/path','/supervins_loop_fusion/loop_corrected_path','/supervins_loop_fusion/pose_graph_path']:
   if path_lengths.get(topic,0)<10:raise RuntimeError('Too few poses on '+topic)
 print('PASS startup' if a.startup_only else 'PASS dataset output; inspect loop.log for confirmed closures',flush=True)
 if not a.no_rviz:
  try:
   tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True,timeout=5)
   import re
   match=re.search(r'(0x[0-9a-f]+) "supervins_rviz_config[^\n]*RViz"',tree)
   if match:subprocess.run(['import','-window',match.group(1),str(run/'rviz_final.png')],check=True,timeout=15)
  except Exception as e:print('RViz screenshot failed:',e,flush=True)
finally:
 summary={'startup_only':a.startup_only,'bag':str(a.bag),'rate':a.rate,'counts':dict(counts),'last_path_lengths':path_lengths,'rates':{},'finite_odometry':not bad_odometry}
 for topic,ts in stamps.items():
  if len(ts)>1 and ts[-1]>ts[0]:summary['rates'][topic]={'stamp_hz':(len(ts)-1)/(ts[-1]-ts[0]),'wall_hz':(len(ts)-1)/(arrivals[topic][-1]-arrivals[topic][0]),'first_stamp':ts[0],'last_stamp':ts[-1]}
 (run/'runtime_summary.json').write_text(json.dumps(summary,indent=2));(run/'resources.json').write_text(json.dumps(resources,indent=2))
 for name,proc in reversed(processes):
  if proc.poll() is None:
   try:os.killpg(proc.pid,signal.SIGINT);proc.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=5)
 for f in streams:f.close()
 print('RESULT_DIR='+str(run),flush=True)
