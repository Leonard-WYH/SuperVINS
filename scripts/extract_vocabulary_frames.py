#!/usr/bin/env python3
from pathlib import Path
import cv2
ws=Path(__file__).resolve().parents[1];out=ws/'data/vocabulary_training';out.mkdir(parents=True,exist_ok=True)
c=cv2.VideoCapture(str(ws/'src/SuperVINS/resources/video.mp4'))
if not c.isOpened():raise RuntimeError('Demo video unavailable')
for sec in range(3,45):
 c.set(cv2.CAP_PROP_POS_MSEC,sec*1000);ok,im=c.read()
 if not ok:raise RuntimeError('Missing demo frame '+str(sec))
 if not cv2.imwrite(str(out/f'demo_{sec:03d}.png'),cv2.cvtColor(im[384:750,2:573],cv2.COLOR_BGR2GRAY)):raise RuntimeError('Failed to write crop')
print('42 demo camera crops; no V2_01_easy frames used')
