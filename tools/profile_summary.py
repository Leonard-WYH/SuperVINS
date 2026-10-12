import pathlib,json,collections
root=pathlib.Path(__file__).resolve().parents[1];summary={}
for family in ['cpp_sp','cpp_lg']:
 p=max((root/'results').glob(family+'_*.json'),key=lambda p:p.stat().st_mtime)
 events=json.loads(p.read_text());kernels=[e for e in events if e.get('cat')=='Node' and e.get('args',{}).get('provider')];counts=collections.Counter(e['args']['provider'] for e in kernels)
 if not counts['CUDAExecutionProvider']:raise RuntimeError('No CUDA nodes '+family)
 summary[family]={'profile':str(p),'node_event_counts':dict(counts),'cuda_op_types':dict(collections.Counter(e['args'].get('op_name') for e in kernels if e['args']['provider']=='CUDAExecutionProvider'))}
(root/'results/cpp_gpu_profile_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
