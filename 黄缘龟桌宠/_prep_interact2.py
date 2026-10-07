# -*- coding: utf-8 -*-
"""1.mp4/2.mp4/3.png → 交互帧（黑底泛洪抠图，降采样加速，尺寸对齐走动乌龟 491x195）"""
from PIL import Image, ImageFilter
import numpy as np, glob, os
from collections import deque

SRC1 = r"C:\Users\Administrator\AppData\Local\Temp\v1_full"
SRC2 = r"C:\Users\Administrator\AppData\Local\Temp\v2_full"
DST = r"C:\Users\Administrator\Desktop\黄缘龟\interact"
TARGET = (491, 195)
CANVAS = (528, 240)
FPS = 24
DS = 4   # 掩码降采样倍数

def key_black_fast(rgba):
    """黑底泛洪抠图（掩码在 1/DS 分辨率计算，放大回全尺寸）"""
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
    # 保留最大连通域（小图 BFS）
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
        keep_id = comps[0][1]
        subject = (label == keep_id)
    # 放大回全尺寸（LANCZOS 自带柔和边缘）
    alpha = np.asarray(Image.fromarray((subject*255).astype(np.uint8)).resize((w, h), Image.LANCZOS), dtype=np.uint8)
    out = np.dstack([arr[..., :3].astype(np.uint8), alpha])
    return Image.fromarray(out, "RGBA")

def content_bbox(img):
    arr = np.asarray(img)
    m = arr[..., 3] > 40
    ys, xs = np.where(m)
    if not len(xs):
        return None
    return (xs.min(), ys.min(), xs.max(), ys.max())

def scale_centered(img, scale):
    iw, ih = img.size
    nw, nh = max(1, int(iw*scale)), max(1, int(ih*scale))
    img2 = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0,0,0,0))
    canvas.paste(img2, ((CANVAS[0]-nw)//2, (CANVAS[1]-nh)//2), img2)
    return canvas

def fit_scale(box):
    bw, bh = box[2]-box[0]+1, box[3]-box[1]+1
    return min(TARGET[0]/bw, TARGET[1]/bh)

def process_video(src_dir, prefix, ref_idx):
    files = sorted(glob.glob(os.path.join(src_dir, "*.png")))
    imgs = [key_black_fast(Image.open(f).convert("RGBA")) for f in files]
    box = content_bbox(imgs[ref_idx])
    s = fit_scale(box)
    print("%s: %d帧, 参考内容 %dx%d, 缩放 %.3f" % (prefix, len(imgs), box[2]-box[0]+1, box[3]-box[1]+1, s))
    for i, img in enumerate(imgs, 1):
        scale_centered(img, s).save(os.path.join(DST, "%s%02d.png" % (prefix, i)))
    return len(imgs)

n1 = process_video(SRC1, "1_", 0)
n2 = process_video(SRC2, "2_", -1)

p3 = Image.open(os.path.join(DST, "3.png")).convert("RGBA")
box3 = content_bbox(p3)
s3 = fit_scale(box3)
print("3.png: 内容 %dx%d, 缩放 %.3f" % (box3[2]-box3[0]+1, box3[3]-box3[1]+1, s3))
scale_centered(p3, s3).save(os.path.join(DST, "3_fit.png"))

with open(os.path.join(DST, "intervals.txt"), "w", encoding="utf-8") as f:
    f.write("%d,%d" % (1000//FPS, 1000//FPS))
print("完成: 1_01..%02d, 2_01..%02d, 3_fit.png, intervals=%dms" % (n1, n2, 1000//FPS))
