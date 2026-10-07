# -*- coding: utf-8 -*-
"""黄缘龟照片抠图：边缘泛洪填充 + 最大连通域 + 边缘羽化"""
from PIL import Image, ImageFilter
from collections import deque
import math, sys

SRC = r"C:\Users\Administrator\Desktop\黄缘龟\_pet_src.png"
OUT = r"C:\Users\Administrator\Desktop\黄缘龟\黄缘龟.png"
PREVIEW = r"C:\Users\Administrator\Desktop\黄缘龟\_抠图预览.png"

TOL = 55          # 颜色容差（背景与主体的分界灵敏度）
MIN_COMP = 600    # 最小连通域面积（滤掉噪点）

img = Image.open(SRC).convert("RGB")
w, h = img.size
px = img.load()

# ── 1. 统计边缘背景色（取四个边的像素） ──
border = []
for x in range(w):
    border.append(px[x, 0]); border.append(px[x, h - 1])
for y in range(h):
    border.append(px[0, y]); border.append(px[w - 1, y])
n = len(border)
mean = tuple(sum(c[i] for c in border) / n for i in range(3))
print("背景均值:", tuple(round(v, 1) for v in mean))

def dist(c):
    return math.sqrt((c[0]-mean[0])**2 + (c[1]-mean[1])**2 + (c[2]-mean[2])**2)

# ── 2. 从所有边缘像素泛洪填充背景 ──
bg = [[False] * w for _ in range(h)]
q = deque()
for x in range(w):
    for y in (0, h - 1):
        if dist(px[x, y]) <= TOL and not bg[y][x]:
            bg[y][x] = True; q.append((x, y))
for y in range(h):
    for x in (0, w - 1):
        if dist(px[x, y]) <= TOL and not bg[y][x]:
            bg[y][x] = True; q.append((x, y))
while q:
    x, y = q.popleft()
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx] and dist(px[nx, ny]) <= TOL:
            bg[ny][nx] = True
            q.append((nx, ny))

# ── 3. 反转得主体掩码，保留大连通域 ──
mask = [[not bg[y][x] for x in range(w)] for y in range(h)]
visited = [[False] * w for _ in range(h)]
keep = [[False] * w for _ in range(h)]
for sy in range(h):
    for sx in range(w):
        if mask[sy][sx] and not visited[sy][sx]:
            comp = []
            q = deque([(sx, sy)]); visited[sy][sx] = True
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not visited[ny][nx]:
                        visited[ny][nx] = True
                        q.append((nx, ny))
            if len(comp) >= MIN_COMP:
                for x, y in comp:
                    keep[y][x] = True
print("保留主体像素:", sum(sum(r) for r in keep))

# ── 4. 生成 alpha：腐蚀 1px 去白边 + 高斯羽化 ──
alpha = Image.new("L", (w, h), 0)
apx = alpha.load()
for y in range(h):
    for x in range(w):
        if keep[y][x]:
            apx[x, y] = 255
alpha = alpha.filter(ImageFilter.MinFilter(3))   # 腐蚀
alpha = alpha.filter(ImageFilter.GaussianBlur(1.2))  # 羽化

out = Image.new("RGBA", (w, h))
out.paste(img, (0, 0))
out.putalpha(alpha)
out.save(OUT)
print("已保存:", OUT, out.size)

# ── 5. 预览图（棋盘格背景） ──
cell = 10
pv = Image.new("RGB", (w, h))
ppx = pv.load()
for y in range(h):
    for x in range(w):
        ppx[x, y] = (230, 230, 230) if ((x // cell) + (y // cell)) % 2 == 0 else (255, 255, 255)
pv.paste(out, (0, 0), out)
pv.save(PREVIEW)
print("已保存预览:", PREVIEW)
