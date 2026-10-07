# -*- coding: utf-8 -*-
"""预乘通道级验证: 走一趟重建后的 82 帧, 检查每个相邻步(含接缝)的视觉差异"""
import glob, os, statistics
from PIL import Image, ImageChops

DEV = r"C:\Users\Administrator\Desktop\黄缘龟\frames"
fs = sorted(glob.glob(os.path.join(DEV, "f*.png")))
print("frames now:", len(fs))
imgs = [Image.open(f).convert("RGBA") for f in fs]

def pm_small(im):
    a = im.getchannel("A")
    r = ImageChops.multiply(im.getchannel("R"), a)
    g = ImageChops.multiply(im.getchannel("G"), a)
    b = ImageChops.multiply(im.getchannel("B"), a)
    pm = Image.merge("RGBA", (r, g, b, a))
    return pm.resize((48, 24), Image.LANCZOS)

def pd(a, b):
    da = list(a.tobytes()); db = list(b.tobytes())
    return sum(abs(x-y) for x, y in zip(da, db)) / len(da)

small = [pm_small(im) for im in imgs]
adj = [pd(small[i], small[i+1]) for i in range(len(small)-1)]
med = statistics.median(adj)
print("all-step median: %.3f  p90: %.3f  max: %.3f" % (med, sorted(adj)[int(len(adj)*0.9)], max(adj)))
seam = pd(small[-1], small[0])
print("wrap seam (last->first): %.3f  (median x%.2f)" % (seam, seam/med))
# 找出最大的几个步(应该是桥之前的普通帧 vs 桥内)
order = sorted(range(len(adj)), key=lambda i: -adj[i])
print("top5 largest steps:", [(i+1, round(adj[i],3)) for i in order[:5]])
print("bridge region steps (74..82):", [round(adj[i],3) for i in range(73, len(adj))])
print("DONE")
