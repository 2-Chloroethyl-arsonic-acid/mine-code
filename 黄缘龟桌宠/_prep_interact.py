# -*- coding: utf-8 -*-
"""交互素材预处理：1.gif/2.gif 绿幕抠图适配窗口；3.png 裁切适配"""
from PIL import Image, ImageSequence
import numpy as np, os
from collections import deque

BASE = r"C:\Users\Administrator\Desktop\黄缘龟\interact"
TARGET = (528, 240)   # 与桌宠窗口一致

def chroma_key(rgba):
    arr = np.asarray(rgba, dtype=np.int16)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    green_dom = g - np.maximum(r, b)
    chroma_a = np.clip((130 - green_dom) * (255.0 / 30.0), 0, 255).astype(np.uint8)
    return np.dstack([arr[..., :3].astype(np.uint8), np.minimum(a, chroma_a).astype(np.uint8)])

def fill_holes(rgba_arr):
    arr = np.array(rgba_arr)
    alpha = arr[..., 3]
    h, w = alpha.shape
    bg = alpha < 128
    visited = np.zeros_like(bg)
    q = deque()
    for x in range(w):
        for y in (0, h-1):
            if bg[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    for y in range(h):
        for x in (0, w-1):
            if bg[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and bg[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True; q.append((nx, ny))
    arr[..., 3][bg & ~visited] = 255
    return Image.fromarray(arr, "RGBA")

def fit_canvas(img_rgba):
    """保持宽高比缩放并居中放入 528x240 透明画布"""
    arr = np.asarray(img_rgba)
    m = arr[..., 3] > 8
    if not m.any():
        return Image.new("RGBA", TARGET, (0,0,0,0))
    ys, xs = np.where(m)
    box = (max(0, xs.min()-4), max(0, ys.min()-4), min(arr.shape[1], xs.max()+5), min(arr.shape[0], ys.max()+5))
    img = img_rgba.crop(box)
    iw, ih = img.size
    s = min(TARGET[0]/iw, TARGET[1]/ih)
    img = img.resize((max(1, int(iw*s)), max(1, int(ih*s))), Image.LANCZOS)
    canvas = Image.new("RGBA", TARGET, (0,0,0,0))
    canvas.paste(img, ((TARGET[0]-img.width)//2, (TARGET[1]-img.height)//2), img)
    return canvas

# 1.gif / 2.gif → 序列帧
for gname, prefix in (("1.gif", "1_"), ("2.gif", "2_")):
    gif = Image.open(os.path.join(BASE, gname))
    for i, f in enumerate(ImageSequence.Iterator(gif), 1):
        f = f.convert("RGBA")
        keyed = fill_holes(chroma_key(f))
        fit_canvas(keyed).save(os.path.join(BASE, "%s%02d.png" % (prefix, i)))
    print("%s → %s%02d..%02d.png" % (gname, prefix, 1, gif.n_frames))

# 3.png → 裁切适配
p3 = Image.open(os.path.join(BASE, "3.png")).convert("RGBA")
fit_canvas(p3).save(os.path.join(BASE, "3_fit.png"))
print("3.png → 3_fit.png (居中适配 %dx%d)" % TARGET)
print("完成")
