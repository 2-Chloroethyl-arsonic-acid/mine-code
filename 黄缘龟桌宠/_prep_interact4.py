# -*- coding: utf-8 -*-
"""新透明GIF处理：1_t(去绿幕残留) / 2_t(去灰青背景) → 交互帧 + 尺寸对齐"""
from PIL import Image, ImageSequence
import numpy as np, os
from collections import deque

BASE = r"C:\Users\Administrator\Desktop\黄缘龟\interact"
TARGET = (491, 195)
CANVAS = (528, 240)
DS = 4

def mask_to_alpha(mask_small, w, h):
    alpha = np.asarray(Image.fromarray((mask_small*255).astype(np.uint8)).resize((w, h), Image.LANCZOS), dtype=np.uint8)
    return alpha

def largest_component(subject):
    sh, sw = subject.shape
    label = np.zeros_like(subject, dtype=np.int32)
    comps = []
    for sy in range(sh):
        for sx in range(sw):
            if subject[sy, sx] and label[sy, sx] == 0:
                cid = len(comps) + 1
                cnt = 0
                q2 = deque([(sx, sy)]); label[sy, sx] = cid
                while q2:
                    x, y = q2.popleft(); cnt += 1
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < sw and 0 <= ny < sh and subject[ny, nx] and label[ny, nx] == 0:
                            label[ny, nx] = cid; q2.append((nx, ny))
                comps.append((cnt, cid))
    if comps:
        comps.sort(reverse=True)
        return label == comps[0][1]
    return subject

def flood_bg(cond_small):
    """从边框泛洪 cond 区域"""
    sh, sw = cond_small.shape
    visited = np.zeros_like(cond_small)
    q = deque()
    for x in range(sw):
        for y in (0, sh-1):
            if cond_small[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    for y in range(sh):
        for x in (0, sw-1):
            if cond_small[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < sw and 0 <= ny < sh and cond_small[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True; q.append((nx, ny))
    return visited

def key_green(rgba):
    """去绿幕残留（绿主导>阈值 → 透明），保留原有 alpha"""
    arr = np.asarray(rgba, dtype=np.float32)
    h, w = arr.shape[:2]
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    green_dom = g - np.maximum(r, b)
    sh, sw = h // DS, w // DS
    gd_small = np.asarray(Image.fromarray(np.clip(green_dom+128, 0, 255).astype(np.uint8)).resize((sw, sh), Image.BOX), dtype=np.float32) - 128
    bg = gd_small > 60
    visited = flood_bg(bg)
    subject = ~visited
    subject = largest_component(subject)
    alpha = mask_to_alpha(subject, w, h)
    orig_a = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((w, h), Image.BOX), dtype=np.uint8) if False else a
    final = np.minimum(orig_a.astype(np.uint8), alpha)
    return Image.fromarray(np.dstack([arr[..., :3].astype(np.uint8), final]), "RGBA")

def key_color(rgba, bg_color, tol=50):
    """按背景色泛洪抠除（灰青色背景）"""
    arr = np.asarray(rgba, dtype=np.float32)
    h, w = arr.shape[:2]
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    dist = np.sqrt((r-bg_color[0])**2 + (g-bg_color[1])**2 + (b-bg_color[2])**2)
    sh, sw = h // DS, w // DS
    d_small = np.asarray(Image.fromarray(np.clip(dist, 0, 255).astype(np.uint8)).resize((sw, sh), Image.BOX), dtype=np.float32)
    bg = d_small < tol
    visited = flood_bg(bg)
    subject = ~visited
    subject = largest_component(subject)
    alpha = mask_to_alpha(subject, w, h)
    final = np.minimum(a.astype(np.uint8), alpha)
    return Image.fromarray(np.dstack([arr[..., :3].astype(np.uint8), final]), "RGBA")

def fill_holes(rgba):
    arr = np.array(rgba)
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

def content_bbox(img):
    arr = np.asarray(img)
    m = arr[..., 3] > 40
    ys, xs = np.where(m)
    return (xs.min(), ys.min(), xs.max(), ys.max())

def scale_centered(img, scale):
    iw, ih = img.size
    nw, nh = max(1, int(iw*scale)), max(1, int(ih*scale))
    img2 = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0,0,0,0))
    canvas.paste(img2, ((CANVAS[0]-nw)//2, (CANVAS[1]-nh)//2), img2)
    return canvas

def fit_scale(box, target):
    bw, bh = box[2]-box[0]+1, box[3]-box[1]+1
    return min(target[0]/bw, target[1]/bh)

jobs = [
    ("1_t.gif", "1_", key_green, None, 30),
    ("2_t.gif", "2_", None, (76, 105, 113), 60),
]
for gname, prefix, kg, bgc, ms in jobs:
    gif = Image.open(os.path.join(BASE, gname))
    frames = [f.convert("RGBA") for f in ImageSequence.Iterator(gif)]
    imgs = []
    for f in frames:
        img = fill_holes(kg(f)) if kg else fill_holes(key_color(f, bgc))
        imgs.append(img)
    box = content_bbox(imgs[0] if prefix == "1_" else imgs[-1])
    s = fit_scale(box, TARGET)
    print("%s: %d帧, 参考内容 %dx%d, 缩放 %.3f → %dx%d" % (gname, len(imgs), box[2]-box[0]+1, box[3]-box[1]+1, s,
          int((box[2]-box[0]+1)*s), int((box[3]-box[1]+1)*s)))
    for i, img in enumerate(imgs, 1):
        scale_centered(img, s).save(os.path.join(BASE, "%s%02d.png" % (prefix, i)))

with open(os.path.join(BASE, "intervals.txt"), "w", encoding="utf-8") as f:
    f.write("%d,%d" % (jobs[0][4], jobs[1][4]))
print("完成: intervals = 30,60 ms")
