# -*- coding: utf-8 -*-
"""GIF → 桌宠透明序列帧（绿幕抠像 + 朝向检测 + facing.txt）"""
from PIL import Image, ImageSequence
import numpy as np, os
from collections import deque

SRC = r"C:\Users\Administrator\Desktop\使用.gif"
DST = r"C:\Users\Administrator\Desktop\黄缘龟\frames"
TARGET = (528, 240)

os.makedirs(DST, exist_ok=True)
gif = Image.open(SRC)
frames = []
durations = []
for f in ImageSequence.Iterator(gif):
    frames.append(f.convert("RGBA"))
    durations.append(f.info.get("duration", 33))
print("帧数:", len(frames), "平均帧延迟: %.1f ms" % (sum(durations)/len(durations)))

def chroma_key(rgba):
    """绿幕抠像 + 内部镂空填充：绿色主导的像素变透明，但完全被不透明像素包围的空洞会补实"""
    arr = np.asarray(rgba, dtype=np.int16)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    green_dom = g - np.maximum(r, b)
    # 绿色主导 < 100 → 不透明；> 130 → 全透明；中间过渡（比之前宽松，保护脚部）
    chroma_a = np.clip((130 - green_dom) * (255.0 / 30.0), 0, 255).astype(np.uint8)
    combined = np.minimum(a, chroma_a).astype(np.uint8)
    out = np.dstack([arr[..., :3].astype(np.uint8), combined])
    return Image.fromarray(out, "RGBA")


def fill_interior_holes(rgba):
    """把不与图像边缘连通的透明区域（内部镂空）填充为不透明"""
    arr = np.array(rgba)  # copy，保证可写
    alpha = arr[..., 3]
    h, w = alpha.shape
    bg = alpha < 128
    visited = np.zeros_like(bg)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bg[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if bg[y, x] and not visited[y, x]:
                visited[y, x] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and bg[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True; q.append((nx, ny))
    hole = bg & ~visited
    if hole.any():
        arr[..., 3][hole] = 255
    return Image.fromarray(arr, "RGBA")

# 朝向检测（多段带最大不对称法：头侧在中段带延伸得离壳体中心最远）
test = np.asarray(chroma_key(frames[0]))
h, w = test.shape[:2]
mask = test[..., 3] > 128
ys, xs = np.where(mask)
y0, y1 = ys.min(), ys.max()
cx = (xs.min() + xs.max()) / 2.0
hh = y1 - y0
best = None
for lo, hi in ((0.2, 0.45), (0.3, 0.55), (0.4, 0.65), (0.25, 0.6)):
    band = mask[y0 + int(hh*lo):y0 + max(int(hh*hi), int(hh*lo)+1), :]
    cols = np.where(band.any(axis=0))[0]
    if len(cols) < 10:
        continue
    le = cx - cols.min(); re = cols.max() - cx
    if best is None or abs(re - le) > abs(best[1] - best[0]):
        best = (le, re)
faces_right = best is not None and best[1] > best[0]
print("头朝向: 左延伸=%.0f 右延伸=%.0f → %s" % (best[0], best[1], "朝右" if faces_right else "朝左"))

# 抠图保存（先收集，再做循环接缝平滑）
out_list = []
for i, f in enumerate(frames, 1):
    if f.size != TARGET:
        f = f.resize(TARGET, Image.LANCZOS)
    out_list.append(np.asarray(fill_interior_holes(chroma_key(f)), dtype=np.float32))

# 循环接缝平滑（默认关闭——渐变收势观感反而更突兀，需要时设为 True）
SEAM_SMOOTH = False
if SEAM_SMOOTH:
    K = 4
    for j in range(K):
        w = j / (K - 1) if K > 1 else 1.0
        idx = len(out_list) - K + j
        out_list[idx] = out_list[idx] * (1 - w) + out_list[0] * w
    print("循环接缝平滑: 末 %d 帧渐变至首帧，末帧=首帧" % K)

for i, arr in enumerate(out_list, 1):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(DST, "f%03d.png" % i))

with open(os.path.join(DST, "facing.txt"), "w", encoding="utf-8") as fh:
    fh.write("right" if faces_right else "left")
with open(os.path.join(DST, "timing.txt"), "w", encoding="utf-8") as fh:
    fh.write(",".join(str(max(10, d)) for d in durations))
print("完成:", len(frames), "帧 →", DST, "| facing =", "right" if faces_right else "left")
