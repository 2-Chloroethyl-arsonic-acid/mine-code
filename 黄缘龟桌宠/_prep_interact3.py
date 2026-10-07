# -*- coding: utf-8 -*-
"""透明GIF(实际黑底) → 交互帧：黑底泛洪抠图 + 对齐走动尺寸；3.png 调小"""
from PIL import Image, ImageSequence
import numpy as np, os
from collections import deque

BASE = r"C:\Users\Administrator\Desktop\黄缘龟\interact"
TARGET = (491, 195)     # 走动乌龟尺寸
TARGET3 = (390, 155)    # 3.png 调小后的目标（高度≈155）
CANVAS = (528, 240)
FPS = 33                # GIF 30ms/帧 ≈ 33fps
DS = 4

def key_black_fast(rgba):
    arr = np.asarray(rgba, dtype=np.float32)
    h, w = arr.shape[:2]
    dist = np.sqrt(arr[..., 0]**2 + arr[..., 1]**2 + arr[..., 2]**2)
    sh, sw = h // DS, w // DS
    small = np.asarray(Image.fromarray(dist.astype(np.uint8)).resize((sw, sh), Image.BOX), dtype=np.float32)
    bg = small < 45
    visited = np.zeros_like(bg)
    q = deque()
    for x in range(sw):
        for y in (0, sh-1):
            if bg[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    for y in range(sh):
        for x in (0, sw-1):
            if bg[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < sw and 0 <= ny < sh and bg[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True; q.append((nx, ny))
    subject = ~visited
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
        subject = (label == comps[0][1])
    alpha = np.asarray(Image.fromarray((subject*255).astype(np.uint8)).resize((w, h), Image.LANCZOS), dtype=np.uint8)
    return Image.fromarray(np.dstack([arr[..., :3].astype(np.uint8), alpha]), "RGBA")

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

for gname, prefix in (("1_new.gif", "1_"), ("2_new.gif", "2_")):
    gif = Image.open(os.path.join(BASE, gname))
    frames = [f.convert("RGBA") for f in ImageSequence.Iterator(gif)]
    imgs = [key_black_fast(f) for f in frames]
    box = content_bbox(imgs[0] if prefix == "1_" else imgs[-1])
    s = fit_scale(box, TARGET)
    print("%s: %d帧, 参考内容 %dx%d, 缩放 %.3f → %dx%d" % (gname, len(imgs), box[2]-box[0]+1, box[3]-box[1]+1, s,
          int((box[2]-box[0]+1)*s), int((box[3]-box[1]+1)*s)))
    for i, img in enumerate(imgs, 1):
        scale_centered(img, s).save(os.path.join(BASE, "%s%02d.png" % (prefix, i)))

# 3.png 调小
p3 = Image.open(os.path.join(BASE, "3.png")).convert("RGBA")
box3 = content_bbox(p3)
s3 = fit_scale(box3, TARGET3)
print("3.png: 内容 %dx%d, 缩放 %.3f → %dx%d (调小)" % (box3[2]-box3[0]+1, box3[3]-box3[1]+1, s3,
      int((box3[2]-box3[0]+1)*s3), int((box3[3]-box3[1]+1)*s3)))
scale_centered(p3, s3).save(os.path.join(BASE, "3_fit.png"))

with open(os.path.join(BASE, "intervals.txt"), "w", encoding="utf-8") as f:
    f.write("30,30")
print("完成: 帧间隔 30ms (33fps)")
