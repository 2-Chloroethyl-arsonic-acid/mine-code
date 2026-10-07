# -*- coding: utf-8 -*-
"""修复卡顿帧(45,50) + 整体水平翻转 → 新视频帧序列"""
from PIL import Image
import numpy as np, glob, os

SRC = r"C:\Users\Administrator\AppData\Local\Temp\glitch_full"
DST = r"C:\Users\Administrator\AppData\Local\Temp\glitch_fixed"
os.makedirs(DST, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC, "*.png")))
print("载入帧数:", len(files))
frames = [np.asarray(Image.open(f).convert("RGB"), dtype=np.float32) for f in files]
N = len(frames)

# 卡顿帧（0-indexed）：45, 50 —— 用前后帧线性插值替换
FIX = [45, 50]
for i in FIX:
    if 0 < i < N - 1:
        before = frames[i-1]; after = frames[i+1]
        frames[i] = (before + after) / 2.0
        print("修复帧 %d: 替换为 (帧%d + 帧%d)/2" % (i, i-1, i+1))

# 整体水平翻转
frames = [f[:, ::-1, :] for f in frames]

# 保存
for i, f in enumerate(frames):
    Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), "RGB").save(
        os.path.join(DST, "fx%03d.png" % i))
print("已保存修复+翻转后帧:", len(frames), "→", DST)
