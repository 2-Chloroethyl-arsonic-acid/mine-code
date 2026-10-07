# -*- coding: utf-8 -*-
"""无缝循环修复: 原 74 帧后追加 m 帧姿势渐变桥(73->0), 预乘 alpha 混合.
输出: Desktop/frames (exe旁覆盖) + dev frames (旧帧备份 frames_backup_旧走路)
"""
import glob, os, shutil, statistics
from PIL import Image, ImageChops

DESK = r"C:\Users\Administrator\Desktop"
DEV = os.path.join(DESK, "黄缘龟", "frames")
OVR = os.path.join(DESK, "frames")
BAK = os.path.join(DESK, "黄缘龟", "frames_backup_旧走路")
M = 8  # 渐变桥帧数

fs = sorted(glob.glob(os.path.join(DEV, "f*.png")))
print("old frames:", len(fs))
imgs = [Image.open(f).convert("RGBA") for f in fs]
W, H = imgs[0].size
print("size:", W, "x", H)

def to_pm(im):
    a = im.getchannel("A")
    r = ImageChops.multiply(im.getchannel("R"), a)
    g = ImageChops.multiply(im.getchannel("G"), a)
    b = ImageChops.multiply(im.getchannel("B"), a)
    return Image.merge("RGBA", (r, g, b, a))

def blend_pm(a_pm, b_pm, w):
    """预乘混合 w: 0=a, 1=b; 去预乘还原直通 RGBA"""
    bl = Image.blend(a_pm, b_pm, w)
    px = bl.load()
    for y in range(H):
        for x in range(W):
            av = px[x, y][3]
            if 0 < av < 255:
                pr, pg, pb = px[x, y][0], px[x, y][1], px[x, y][2]
                px[x, y] = (min(255, pr*255//av), min(255, pg*255//av),
                            min(255, pb*255//av), av)
            elif av == 0:
                px[x, y] = (0, 0, 0, 0)
    return bl

tail = to_pm(imgs[-1])
head = to_pm(imgs[0])
bridge = []
for k in range(1, M+1):
    bridge.append(blend_pm(tail, head, k / (M + 1)))

# 桥步长校验
def pose_vec(im):
    bb = im.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox()
    if not bb: return None
    crop = im.crop(bb)
    bg = Image.new("RGB", crop.size, (0, 0, 0))
    bg.paste(crop, mask=crop.getchannel("A"))
    return list(bg.convert("L").resize((48, 24), Image.LANCZOS).get_flattened_data())
def pd(a, b):
    if a is None or b is None: return 999.0
    return sum(abs(x-y) for x, y in zip(a, b)) / len(a)

pose = [pose_vec(im) for im in imgs]
pb = [pose_vec(b) for b in bridge]
steps = [pd(pose[-1], pb[0])] + [pd(pb[i], pb[i+1]) for i in range(M-1)] + [pd(pb[-1], pose[0])]
adj_old = statistics.median([pd(pose[i], pose[i+1]) for i in range(len(imgs)-1)])
old_seam = pd(pose[-1], pose[0])
print("old adjacent median: %.2f | old seam 73->0: %.2f" % (adj_old, old_seam))
print("bridge step diffs:", [round(s, 2) for s in steps], " max:", round(max(steps), 2))
# 探针: 桥首/末帧中心像素 vs 首尾帧
probe = (300, 150)
print("probe tail:", imgs[-1].load()[probe], "head:", imgs[0].load()[probe])
print("probe b0:", bridge[0].load()[probe], "b7:", bridge[-1].load()[probe])

# 写盘
os.makedirs(OVR, exist_ok=True)
os.makedirs(BAK, exist_ok=True)
for f in fs:
    shutil.copy2(f, os.path.join(BAK, os.path.basename(f)))
for d in (DEV, OVR):
    for f in glob.glob(os.path.join(d, "f*.png")):
        os.remove(f)
new_frames = imgs + bridge
for i, im in enumerate(new_frames, 1):
    im.save(os.path.join(OVR, "f%03d.png" % i))
    im.save(os.path.join(DEV, "f%03d.png" % i))
for extra in ("facing.txt", "timing.txt"):
    src = os.path.join(DEV, extra)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(OVR, extra))
        print("copied extra:", extra)
print("new frames:", len(new_frames))
print("DONE")
