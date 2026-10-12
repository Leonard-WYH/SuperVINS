#!/usr/bin/env python3
"""Restore ROS1 messages from EuRoC CSV/PNG without changing nanosecond stamps."""
import argparse,csv,json,pathlib
import cv2,numpy as np,rosbag,rospy,yaml
from sensor_msgs.msg import Image,Imu
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--dataset',type=pathlib.Path,default=root/'data/V2_01_easy');a=p.parse_args()
if not a.dataset.is_absolute():a.dataset=root/a.dataset
(root/'logs').mkdir(parents=True,exist_ok=True)
imu_csv=next(a.dataset.rglob('imu0/data.csv'));mav=imu_csv.parent.parent
out=root/'data/V2_01_easy.bag';meta={}
def rows(path):
 with path.open() as f:
  return [r for r in csv.reader(f) if r and not r[0].startswith('#')]
events=[]
for sensor in ['imu0','cam0','cam1']:
 rs=rows(mav/sensor/'data.csv');events.extend((int(r[0]),sensor,r) for r in rs)
 times=np.array([int(r[0]) for r in rs],dtype=np.int64);meta[sensor]={'count':len(rs),'first_ns':int(times[0]),'last_ns':int(times[-1]),'nominal_hz':float(1e9/np.median(np.diff(times))),'strictly_increasing':bool(np.all(np.diff(times)>0)),'sensor_yaml':yaml.safe_load((mav/sensor/'sensor.yaml').read_text())}
 if not meta[sensor]['strictly_increasing']:raise RuntimeError('Nonmonotonic timestamps')
events.sort(key=lambda x:x[0]);gt=rows(mav/'state_groundtruth_estimate0/data.csv');truth=root/'data/groundtruth_tum.txt'
with truth.open('w') as f:
 f.write('# timestamp tx ty tz qx qy qz qw; IMU/body pose from EuRoC state_groundtruth_estimate0\n')
 for r in gt:
  t=int(r[0]);f.write(f'{t//10**9}.{t%10**9:09d} '+' '.join(r[1:4]+r[5:8]+r[4:5])+'\n')
meta['groundtruth']={'count':len(gt),'source':str(mav/'state_groundtruth_estimate0/data.csv')};meta['bag_origin']='regenerated from CSV/PNG; both cameras plus IMU; original ns stamps; LZ4 compression'
if out.exists():raise RuntimeError('Bag already exists; refusing to overwrite '+str(out))
part=out.with_suffix('.bag.part')
with rosbag.Bag(str(part),'w',compression=rosbag.Compression.LZ4) as bag:
 for idx,(ns,sensor,r) in enumerate(events):
  stamp=rospy.Time(ns//10**9,ns%10**9)
  if sensor=='imu0':
   msg=Imu();msg.header.stamp=stamp;msg.header.frame_id='imu0';msg.orientation_covariance[0]=-1
   msg.angular_velocity.x,msg.angular_velocity.y,msg.angular_velocity.z=map(float,r[1:4]);msg.linear_acceleration.x,msg.linear_acceleration.y,msg.linear_acceleration.z=map(float,r[4:7]);topic='/imu0'
  else:
   im=cv2.imread(str(mav/sensor/'data'/r[1]),cv2.IMREAD_GRAYSCALE)
   if im is None or im.shape!=(480,752):raise RuntimeError('Invalid image '+r[1])
   msg=Image();msg.header.stamp=stamp;msg.header.frame_id=sensor;msg.height,msg.width=im.shape;msg.encoding='mono8';msg.is_bigendian=0;msg.step=im.shape[1];msg.data=im.tobytes();topic='/'+sensor+'/image_raw'
  bag.write(topic,msg,stamp)
  if idx%5000==0:print(idx,'/',len(events),flush=True)
part.rename(out)
with rosbag.Bag(str(out)) as bag:
 info=bag.get_type_and_topic_info().topics
 for sensor in ['imu0','cam0','cam1']:
  topic='/imu0' if sensor=='imu0' else '/'+sensor+'/image_raw'
  if info[topic].message_count!=meta[sensor]['count']:raise RuntimeError('Count mismatch')
meta['bag_bytes']=out.stat().st_size;(root/'logs/euroc_data_audit.json').write_text(json.dumps(meta,indent=2));print('PASS',out,flush=True)
