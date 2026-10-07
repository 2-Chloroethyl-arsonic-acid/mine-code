# -*- coding: utf-8 -*-
"""测壳(最大连通不透明块)中心轨迹, 判断壳是否真有位移"""
import glob, os
from PIL import Image

DEV = r"C:\Users\Administrator\Desktop\黄缘龟\frames"
fs = sorted(glob.glob(os.path.join(DEV, "f*.png")))
print("frames:", len(fs))
imgs = [Image.open(f).convert("RGBA") for f in fs]
W, H = imgs[0].size

def shell_center(im, seed):
    a = im.getchannel("A")
    px = a.load()
    # BFS flood from seed over alpha>80
    from collections import deque
    q = deque([seed]); seen = {seed}
    minx, maxx, miny, maxy = seed[0], seed[0], seed[1], seed[1]
    n = 1
    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < W and 0 <= ny < H and (nx,ny) not in seen:
                seen.add((nx,ny))
                if px[nx,ny] > 80:
                    q.append((nx,ny))
                    n += 1
                    if nx < minx: minx = nx
                    if nx > maxx: maxx = nx
                    if ny < miny: miny = ny
                    if ny > maxy: maxy = ny
    if n < 500:
        return None
    return ((minx+maxx)/2, (miny+maxy)/2, n)

seed = (260, 140)
centers = []
for i, im in enumerate(imgs):
    r = shell_center(im, seed)
    if r is None:
        print("frame", i, "shell not found")
        centers.append(None)
        continue
    cx, cy, n = r
    centers.append((cx, cy))
    seed = (int(cx), int(cy))

cxs = [c[0] for c in centers if c]
cys = [c[1] for c in centers if c]
print("shell x-center: first %.1f last %.1f  min %.1f max %.1f (drift %.1f)" %
      (cxs[0], cxs[-1], min(cxs), max(cxs), cxs[-1]-cxs[0]))
print("shell y-center: first %.1f last %.1f  min %.1f max %.1f (drift %.1f)" %
      (cys[0], cys[-1], min(cys), max(cys), cys[-1]-cys[0]))
# 每8帧打点看轨迹
for i in range(0, len(centers), 8):
    if centers[i]:
        print("frame %3d: shell c=(%.1f, %.1f)" % (i, centers[i][0], centers[i][1]))
print("DONE")
