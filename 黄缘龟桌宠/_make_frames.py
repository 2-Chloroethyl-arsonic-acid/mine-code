# -*- coding: utf-8 -*-
"""从指定目录的序列帧生成桌宠透明帧（保持视频原始朝向，写入 facing.txt）
用法: python _make_frames.py <源帧目录(可选，默认Temp\frames_src)> <目标目录(可选，默认frames)>
"""
from PIL import Image
import numpy as np, glob, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Administrator\AppData\Local\Temp\frames_src"
DST = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\Administrator\Desktop\黄缘龟\frames"

files = sorted(glob.glob(os.path.join(SRC, "*.png")))
print("帧数:", len(files))

# 头朝向检测（只检测不翻转，写入 facing.txt）
scores = []
for f in files[::6]:
    img = np.asarray(Image.open(f).convert("RGB"), dtype=np.float32)
    dist = np.sqrt((img ** 2).sum(axis=2))
    mask = dist > 40
    h, w = mask.shape
    top = mask[:int(h * 0.35), :]
    scores.append((top[:, :w//2].sum(), top[:, w//2:].sum()))
L = sum(s[0] for s in scores); R = sum(s[1] for s in scores)
faces_right = R >= L
print("头朝向: 右占比=%.2f → %s" % (R/(L+R), "朝右" if faces_right else "朝左"))

# 抠图保存
os.makedirs(DST, exist_ok=True)
for i, f in enumerate(files, 1):
    arr = np.asarray(Image.open(f).convert("RGB"), dtype=np.float32)
    dist = np.sqrt((arr ** 2).sum(axis=2))
    alpha = np.clip((dist - 35) * 11.6, 0, 255).astype(np.uint8)
    rgba = np.dstack([arr.astype(np.uint8), alpha])
    Image.fromarray(rgba, "RGBA").save(os.path.join(DST, "f%03d.png" % i))

# 朝向标记
with open(os.path.join(DST, "facing.txt"), "w", encoding="utf-8") as fh:
    fh.write("right" if faces_right else "left")
print("已生成:", len(files), "帧 + facing.txt =", "right" if faces_right else "left")
