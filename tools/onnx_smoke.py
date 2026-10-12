#!/usr/bin/env python3
import argparse,json,time,collections,pathlib
import numpy as np
import onnxruntime as ort
p=argparse.ArgumentParser();p.add_argument('--root',default=str(pathlib.Path(__file__).resolve().parents[1]));p.add_argument('--legacy',action='store_true');p.add_argument('--input',type=pathlib.Path);p.add_argument('--report',default='onnx_smoke');a=p.parse_args();root=pathlib.Path(a.root)
print('ORT',ort.__version__,'available',ort.get_available_providers(),flush=True)
weights=root/'src/SuperVINS/supervins_estimator/weights_dpl'
profiles=[]
def session(name):
 so=ort.SessionOptions();so.intra_op_num_threads=1;so.inter_op_num_threads=1;so.graph_optimization_level=ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED;so.enable_profiling=True;so.profile_file_prefix=str(root/'results'/name)
 s=ort.InferenceSession(str(weights/(name+'.onnx')),sess_options=so,providers=[('CUDAExecutionProvider',{'device_id':0,'cudnn_conv_algo_search':'DEFAULT'})])
 s.disable_fallback()
 print(name,'providers',s.get_providers(),flush=True)
 if 'CUDAExecutionProvider' not in s.get_providers(): raise RuntimeError('CUDA EP did not initialize: CPU-only fallback is a failure')
 print('inputs',[(v.name,v.shape,v.type) for v in s.get_inputs()],flush=True)
 print('outputs',[(v.name,v.shape,v.type) for v in s.get_outputs()],flush=True)
 profiles.append((name,s));return s
sp=session('superpoint');image=np.load(a.input or root/'results/smoke_input.npy');outs=[];times=[]
for im in [image,np.roll(image,6,axis=3)]:
 for i in range(4):
  t=time.perf_counter();o=sp.run(None,{'image':im});times.append((time.perf_counter()-t)*1000)
  if not all(np.isfinite(v).all() for v in o):raise RuntimeError('Nonfinite SuperPoint output')
 outs.append(o)
 print('SP',[(v.shape,str(v.dtype)) for v in o],flush=True)
lg=session('superpoint_lightglue_fused')
k0,sc0,d0=outs[0];k1,sc1,d1=outs[1]
h,w=image.shape[-2:]
k0=(k0.astype('float32')-np.array([w/2,h/2],dtype='float32'))/(max(w,h)/2)
k1=(k1.astype('float32')-np.array([w/2,h/2],dtype='float32'))/(max(w,h)/2)
feed=dict(zip([v.name for v in lg.get_inputs()],[k0,k1,d0,d1]));mt=[]
for i in range(6):
 t=time.perf_counter();matches=lg.run(None,feed);mt.append((time.perf_counter()-t)*1000)
 if not all(np.isfinite(v).all() for v in matches):raise RuntimeError('Nonfinite LightGlue output')
print('LG',[(v.shape,str(v.dtype)) for v in matches],flush=True)
if len(matches[0])==0 or np.count_nonzero(matches[1]>.5)==0:raise RuntimeError('No useful matches')
report={'ort_version':ort.__version__,'input':str(a.input or 'repository overview figure')+' plus 6-pixel horizontal roll; diagnostic only','sp_keypoints':[int(x[0].shape[1]) for x in outs],'sp_ms':times,'lg_matches':int(len(matches[0])),'lg_matches_above_0_5':int(np.count_nonzero(matches[1]>.5)),'lg_ms':mt,'finite':True,'providers':{}}
for name,s in profiles:
 fn=s.end_profiling();events=json.load(open(fn));counts=collections.Counter(e.get('args',{}).get('provider') for e in events if e.get('cat')=='Node' and e.get('args',{}).get('provider'));report['providers'][name]=dict(counts)
 if counts['CUDAExecutionProvider']==0:raise RuntimeError('No CUDA kernels in profiling for '+name)
np.savez(root/'results'/(a.report+'_matches.npz'),k0=outs[0][0],k1=outs[1][0],matches=matches[0],scores=matches[1])
(root/'results'/(a.report+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
