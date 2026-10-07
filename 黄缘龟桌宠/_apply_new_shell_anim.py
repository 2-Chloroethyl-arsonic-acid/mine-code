# -*- coding: utf-8 -*-
"""把 1_透明背景_PNG序列 (47f, 1280x720, 透明底) 转成桌宠 interact/1_*.png + 3_fit.png
对齐基准: 黄缘龟/interact/1_01.png (528x240) 的内容包围盒
用法: python _apply_new_shell_anim.py
"""
import shutil, glob, os
from PIL import Image

DESK = r"C:\Users\Administrator\Desktop"
SRC = os.path.join(DESK, "1_透明背景_PNG序列")
DEV = os.path.join(DESK, "黄缘龟", "interact")
OVR = os.path.join(DESK, "interact")          # exe 旁覆盖目录(优先于打包内置)
bak_src_ref = os.path.join(DESK, "黄缘龟", "interact_backup_旧缩壳")
CANVAS = (528, 240)

def bbox(pil_img, thr=12):
    a = pil_img.getchannel("A")
    b = a.point(lambda v: 255 if v > thr else 0)
    return b.getbbox()

def load(fp):
    im = Image.open(fp).convert("RGBA")
    # 去掉边缘杂点后再取内容框
    return im

# 1) 旧 1_01 参考(优先备份，避免二次运行时被新帧污染)
ref_path = os.path.join(bak_src_ref, "1_01.png") if os.path.exists(bak_src_ref) else os.path.join(DEV, "1_01.png")
ref = load(ref_path)
rb = bbox(ref)
print("old 1_01 bbox:", rb)
# 内容尺寸(参考=完全伸出状态)
new_fs = sorted(glob.glob(os.path.join(SRC, "f*.png")))
print("new frames:", len(new_fs))
im1 = load(new_fs[0])
nb = bbox(im1)
print("new f001 bbox:", nb)
rh = rb[3] - rb[1]
scale = rh / (nb[3] - nb[1])    # 统一缩放: 以 f001(完全伸出)高度对齐旧内容
W, H = im1.size
fw = int(round(W * scale)); fh = int(round(H * scale))
dx = rb[0] - int(round(nb[0] * scale))   # 锚定: f001 内容左上角对齐旧内容左上角
# 用中心对齐更稳(旧内容 490 宽 vs 新内容 492 宽几乎一致): 取中心对齐
cx_old = (rb[0] + rb[2]) // 2
cx_new = int(round((nb[0] + nb[2]) * scale / 2))
dx = cx_old - cx_new
cy_old = (rb[1] + rb[3]) // 2
cy_new = int(round((nb[1] + nb[3]) * scale / 2))
dy = cy_old - cy_new
print(f"transform: scale={scale:.4f} full={fw}x{fh} paste_dx={dx} dy={dy}")

def transform(src_im):
    s = src_im.resize((fw, fh), Image.LANCZOS)
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(s, (dx, dy))
    return out

# 2) 生成 1_ 序列
os.makedirs(OVR, exist_ok=True)
for i, fp in enumerate(new_fs, 1):
    out = transform(load(fp))
    out.save(os.path.join(OVR, f"1_{i:02d}.png"))
# 3) 3_fit.png = 最后一帧(完全缩入壳)
transform(load(new_fs[-1])).save(os.path.join(OVR, "3_fit.png"))
print("wrote 47 frames + 3_fit.png to", OVR)

# 4) 旧资产备份 + 覆盖 dev 目录
bak = os.path.join(DESK, "黄缘龟", "interact_backup_旧缩壳")
os.makedirs(bak, exist_ok=True)
for f in glob.glob(os.path.join(DEV, "1_*.png")) + glob.glob(os.path.join(DEV, "3_fit.png")) + glob.glob(os.path.join(DEV, "intervals.txt")):
    shutil.copy2(f, os.path.join(bak, os.path.basename(f)))
print("backup old assets ->", bak)
for f in glob.glob(os.path.join(DEV, "1_*.png")):
    os.remove(f)
for i, fp in enumerate(new_fs, 1):
    shutil.copy2(os.path.join(OVR, f"1_{i:02d}.png"), os.path.join(DEV, f"1_{i:02d}.png"))
shutil.copy2(os.path.join(OVR, "3_fit.png"), os.path.join(DEV, "3_fit.png"))
print("dev interact updated")

# 5) 2_ 序列 + intervals 同步到 exe 旁覆盖目录
for f in glob.glob(os.path.join(DEV, "2_*.png")):
    shutil.copy2(f, os.path.join(OVR, os.path.basename(f)))
with open(os.path.join(OVR, "intervals.txt"), "w", encoding="utf-8") as fh:
    fh.write("42,30\n")     # 新缩壳 47帧@24fps≈42ms；出壳保持 30ms
with open(os.path.join(DEV, "intervals.txt"), "w", encoding="utf-8") as fh:
    fh.write("42,30\n")
print("OVR files:", sorted(os.listdir(OVR)))
