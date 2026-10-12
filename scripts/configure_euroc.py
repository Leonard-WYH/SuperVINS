#!/usr/bin/env python3
from pathlib import Path
import argparse,re,shutil
ws=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ws/'results/euroc');p.add_argument('--config',type=Path,default=ws/'config/euroc_mono_imu.yaml');a=p.parse_args()
a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True);(a.output/'pose_graph').mkdir(exist_ok=True);a.config.parent.mkdir(parents=True,exist_ok=True)
src=ws/'src/SuperVINS/config/euroc';s=(src/'euroc_mono_imu_config.yaml').read_text()
for k,v in {'matche_score_threshold':'0.5','estimate_extrinsic':'0','estimate_td':'0','cam0_calib':'"cam0_euroc.yaml"','cam1_calib':'"cam1_euroc.yaml"','output_path':'"'+str(a.output)+'"','pose_graph_save_path':'"'+str(a.output/'pose_graph')+'"'}.items():s=re.sub(r'^'+k+r':.*$',k+': '+v,s,flags=re.M)
a.config.write_text(s+'\n')
for f in ['cam0_mei.yaml','cam1_mei.yaml']:shutil.copy2(src/f,a.config.parent/f)
import yaml
for name in ['cam0','cam1']:
 sensor=ws/'data/V2_01_easy/mav0'/name/'sensor.yaml'
 if not sensor.exists():raise RuntimeError('Dataset calibration missing: '+str(sensor))
 c=yaml.safe_load(sensor.read_text());fx,fy,cx,cy=c['intrinsics'];k1,k2,p1,p2=c['distortion_coefficients']
 (a.config.parent/(name+'_euroc.yaml')).write_text('%YAML:1.0\n---\nmodel_type: PINHOLE\ncamera_name: '+name+'\nimage_width: 752\nimage_height: 480\ndistortion_parameters:\n   k1: '+str(k1)+'\n   k2: '+str(k2)+'\n   p1: '+str(p1)+'\n   p2: '+str(p2)+'\nprojection_parameters:\n   fx: '+str(fx)+'\n   fy: '+str(fy)+'\n   cx: '+str(cx)+'\n   cy: '+str(cy)+'\n')
print(a.config)
