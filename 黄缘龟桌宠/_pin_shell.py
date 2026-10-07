# -*- coding: utf-8 -*-
"""钉壳对齐 v3: 种子泛洪跟踪壳(最大连通块)中心 -> 每帧平移把壳钉在 frame0 位置
输出 74 帧 -> Desktop/frames + dev frames (原帧已在 frames_backup_旧走路)
"""
import glob, os, shutil, statistics
from collections import deque
from PIL import Image, ImageChops

DESK = r"C:\Users\Administrator\Desktop"
DEV = os.path.join(DESK, "黄缘龟", "frames")
OVR = os.path.join(DESK, "frames")

fs = sorted(glob.glob(os.path.join(DEV, "f*.png")))
N = len(fs)
print("frames:", N)
imgs = [Image.open(f).convert("RGBA") for f in fs]
W, H = imgs[0].size

def shell_center(im, seed, thr=80):
    a = im.getchannel("A"); px = a.load()
    q = deque([seed]); seen = {seed}
    minx = maxx = seed[0]; miny = maxy = seed[1]; n = 1
    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < W and 0 <= ny < H and (nx,ny) not in seen:
                seen.add((nx,ny))
                if px[nx,ny] > thr:
                    q.append((nx,ny)); n += 1
                    if nx < minx: minx = nx
                    if nx > maxx: maxx = nx
                    if ny < miny: miny = ny
                    if ny > maxy: maxy = ny
    if n < 800:
        return None
    return ((minx+maxx)/2.0, (miny+maxy)/2.0)

# 跟踪壳中心
seed = (260, 140)
centers = []
for i, im in enumerate(imgs):
    c = shell_center(im, seed)
    if c is None:
        print("!! frame", i, "shell lost; using previous")
        c = centers[-1] if centers else (260.0, 140.0)
    centers.append(c)
    seed = (int(c[0]), int(c[1]))

ax, ay = centers[0]
print("anchor = shell center of frame0: (%.1f, %.1f)" % (ax, ay))
xs = [round(ax - c[0]) for c in centers]
ys = [round(ay - c[1]) for c in centers]
print("shifts x: min %d max %d | y: min %d max %d" % (min(xs), max(xs), min(ys), max(ys)))

out = []
for i in range(N):
    dx, dy = xs[i], ys[i]
    if dx == 0 and dy == 0:
        out.append(imgs[i])
    else:
        out.append(imgs[i].transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BICUBIC))

# 校验
def pm48(im):
    a = im.getchannel("A")
    r = ImageChops.multiply(im.getchannel("R"), a)
    g = ImageChops.multiply(im.getchannel("G"), a)
    b = ImageChops.multiply(im.getchannel("B"), a)
    return Image.merge("RGBA", (r, g, b, a)).resize((48, 24), Image.LANCZOS)
def pd(x, y):
    da = list(x.tobytes()); db = list(y.tobytes())
    return sum(abs(p-q) for p, q in zip(da, db)) / len(da)

def shell_drift(ims):
    s = (260, 140); cs = []
    for im in ims:
        c = shell_center(im, s)
        if c is None: c = s
        cs.append(c[0]); s = (int(c[0]), int(c[1]))
    return min(cs), max(cs)
print("OLD shell x drift: %.1f..%.1f" % shell_drift(imgs))
print("NEW shell x drift: %.1f..%.1f" % shell_drift(out))

sm = [pm48(im) for im in out]
adj = [pd(sm[i], sm[i+1]) for i in range(N-1)]
med = statistics.median(adj)
seam = pd(sm[-1], sm[0])
sm0 = [pm48(im) for im in imgs]
seam_old = pd(sm0[-1], sm0[0])
med_old = statistics.median([pd(sm0[i], sm0[i+1]) for i in range(N-1)])
print("OLD: median %.3f seam %.3f (x%.2f)" % (med_old, seam_old, seam_old/med_old))
print("NEW: median %.3f seam %.3f (x%.2f)" % (med, seam, seam/med))

# 写盘 (DEV + OVR)
for d in (DEV, OVR):
    for f in glob.glob(os.path.join(d, "f*.png")):
        os.remove(f)
for i, im in enumerate(out, 1):
    im.save(os.path.join(OVR, "f%03d.png" % i))
    im.save(os.path.join(DEV, "f%03d.png" % i))
for extra in ("facing.txt", "timing.txt"):
    src = os.path.join(DEV, extra)
    if os.path.exists(src) and not os.path.exists(os.path.join(OVR, extra)):
        shutil.copy2(src, os.path.join(OVR, extra))
print("wrote", N, "shell-aligned frames")
print("DONE")
