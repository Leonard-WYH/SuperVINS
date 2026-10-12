#!/usr/bin/env python3
"""Create a run-specific YAML whose resource paths are relative to that YAML."""
from pathlib import Path
import argparse
import os
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=Path('results/euroc'))
parser.add_argument('--config', type=Path, default=Path('config/euroc_mono_imu.yaml'))
args = parser.parse_args()

def project_path(value):
    return (value if value.is_absolute() else ROOT / value).resolve()

args.output = project_path(args.output)
args.config = project_path(args.config)
args.output.mkdir(parents=True, exist_ok=True)
(args.output / 'pose_graph').mkdir(exist_ok=True)
args.config.parent.mkdir(parents=True, exist_ok=True)
template = ROOT / 'config/euroc_mono_imu.yaml'
text = template.read_text()

def read_path(key):
    match = re.search(r'^' + key + r':\s*["\']([^"\']+)["\']', text, re.M)
    if not match:
        raise RuntimeError('Missing path in configuration: ' + key)
    return (template.parent / match.group(1)).resolve()

updates = {}
for key in ['cam0_calib', 'cam1_calib']:
    source = read_path(key)
    target = args.config.parent / source.name
    if source != target:
        shutil.copy2(source, target)
    updates[key] = target.name
for key in ['extractor_weight_path', 'matcher_weight_path', 'voc_relative_path', 'brief_pattern_path']:
    source = read_path(key)
    if not source.is_file():
        raise RuntimeError('Resource missing: ' + str(source))
    updates[key] = os.path.relpath(source, args.config.parent)
updates['output_path'] = os.path.relpath(args.output, args.config.parent)
updates['pose_graph_save_path'] = os.path.relpath(args.output / 'pose_graph', args.config.parent)
for key, value in updates.items():
    text = re.sub(r'^' + key + r':.*$', key + ': "' + value + '"', text, flags=re.M)
args.config.write_text(text.rstrip() + '\n')
print(args.config)
