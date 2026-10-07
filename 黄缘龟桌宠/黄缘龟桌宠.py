# -*- coding: utf-8 -*-
"""
黄缘龟桌宠 - 任务栏爬行小宠物
Chinese Box Turtle Desktop Pet - Crawls on the Windows taskbar

运行方式: python 黄缘龟桌宠.py
需要安装: pip install PyQt5

Author: QClaw AI Assistant
"""

import sys
import os
import math
import random
import time
import struct
from pathlib import Path


def _asset_path(name):
    """资源路径：优先程序所在目录（exe旁/脚本旁，可随时更新素材），其次打包内置目录"""
    bases = []
    if getattr(sys, "frozen", False):
        bases.append(Path(sys.executable).resolve().parent)
        bases.append(Path(getattr(sys, "_MEIPASS", ".")))
    else:
        bases.append(Path(__file__).resolve().parent)
    for b in bases:
        p = b / name
        if p.exists():
            return p
    return bases[0] / name


def _log_path():
    """错误日志路径：程序所在目录（可写）"""
    return _program_dir() / "桌宠错误日志.txt"


def _program_dir():
    """程序所在目录（exe 或脚本）"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

# ── DPI 感知：避免高分屏/缩放导致窗口尺寸和位置计算错误 ──
try:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor DPI aware
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# ─────────────────────────────────────────────
# 依赖检查
# ─────────────────────────────────────────────
try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QMenu, QAction,
        QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
        QLabel, QVBoxLayout, QMessageBox
    )
    from PyQt5.QtCore import (
        Qt, QTimer, QPoint, QRect, QPropertyAnimation,
        QAbstractAnimation, QEasingCurve, pyqtSignal, QObject,
        QRectF, QSize
    )
    from PyQt5.QtGui import (
        QPixmap, QPainter, QImage, QColor, QPen, QBrush,
        QFont, QPainterPath, QIcon, QScreen, QTransform
    )
except ImportError:
    print("❌ 缺少 PyQt5，正在尝试安装...")
    os.system(f"{sys.executable} -m pip install PyQt5 -q")
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QMenu, QAction,
        QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
        QLabel, QVBoxLayout, QMessageBox
    )
    from PyQt5.QtCore import (
        Qt, QTimer, QPoint, QRect, QPropertyAnimation,
        QAbstractAnimation, QEasingCurve, pyqtSignal, QObject,
        QRectF, QSize
    )
    from PyQt5.QtGui import (
        QPixmap, QPainter, QImage, QColor, QPen, QBrush,
        QFont, QPainterPath, QIcon, QScreen, QTransform
    )


# ─────────────────────────────────────────────
# 绘制黄缘龟
# ─────────────────────────────────────────────
def draw_turtle(base_size=80):
    """
    绘制一只可爱的黄缘龟 (Cuora flavomarginata)
    特点：圆拱形背壳（茶褐色）、金黄色脊线、头两侧有黄色条纹
    返回 QPixmap
    """
    bs = int(base_size)
    w = bs * 4
    h = bs * 3
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    cx, cy = w // 2, h // 2

    # ── 壳 ──────────────────────────────────
    # 主体椭圆（深茶褐色）
    shell_color = QColor(101, 67, 33)   # 茶褐
    shell_dark  = QColor(60, 40, 15)
    shell_light = QColor(130, 85, 45)

    # 壳的阴影
    shadow = QPainterPath()
    shadow.addEllipse(cx - bs*115//100, cy - bs*55//100, bs*230//100, bs*190//100)
    painter.fillPath(shadow, QColor(0,0,0,60))

    # 背壳主体
    shell_path = QPainterPath()
    shell_path.addEllipse(cx - bs*110//100, cy - bs*85//100, bs*220//100, bs*170//100)
    painter.fillPath(shell_path, shell_color)

    # 壳面高光（顶部弧形）
    highlight = QPainterPath()
    highlight.addEllipse(cx - bs*95//100, cy - bs*95//100, bs*190//100, bs*120//100)
    painter.fillPath(highlight, shell_light)

    # 壳缝纹（盾片分隔线）
    painter.setPen(QPen(shell_dark, 1.5))
    # 椎盾（中心）
    painter.drawEllipse(cx - bs*35//100, cy - bs*45//100, bs*70//100, bs*60//100)
    # 颈盾前
    painter.drawLine(cx, cy - bs*85//100, cx, cy - bs*15//100)
    # 臀盾后
    painter.drawLine(cx, cy + bs*15//100, cx, cy + bs*85//100)
    # 横缝
    painter.drawLine(cx - bs*110//100, cy, cx + bs*110//100, cy)
    # 两侧缝
    painter.drawLine(cx - bs*105//100, cy - bs*40//100, cx + bs*105//100, cy - bs*40//100)
    painter.drawLine(cx - bs*105//100, cy + bs*40//100, cx + bs*105//100, cy + bs*40//100)

    # 壳边缘浅色描边
    painter.setPen(QPen(QColor(180, 140, 80), 2))
    painter.drawEllipse(cx - bs*110//100, cy - bs*85//100, bs*220//100, bs*170//100)

    # ── 头 ──────────────────────────────────
    head_color   = QColor(70, 110, 60)  # 深橄榄绿
    head_stripe  = QColor(220, 195, 55)  # 金黄色条纹

    # 头（椭圆形，左侧朝前）
    head_x = cx - bs * 165//100
    head_y = cy - bs * 38//100
    head_w = bs * 72//100
    head_h = bs * 58//100
    head_path = QPainterPath()
    head_path.addEllipse(head_x, head_y, head_w, head_h)
    painter.fillPath(head_path, head_color)

    # 头顶浅色
    head_top = QPainterPath()
    head_top.addEllipse(head_x + bs*5//100, head_y + bs*5//100, head_w*80//100, head_h*50//100)
    painter.fillPath(head_top, QColor(90, 130, 75))

    # 眼睛
    eye_px = head_x + head_w * 75//100
    eye_py = head_y + head_h * 30//100
    eye_r  = bs * 10//100
    # 眼白
    painter.setBrush(Qt.white)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(eye_px - eye_r, eye_py - eye_r, eye_r*2, eye_r*2)
    # 瞳孔
    painter.setBrush(QColor(20, 20, 20))
    painter.drawEllipse(eye_px - eye_r*60//100, eye_py - eye_r*60//100, eye_r*120//100, eye_r*120//100)
    # 高光
    painter.setBrush(Qt.white)
    painter.drawEllipse(eye_px - eye_r*30//100, eye_py - eye_r*45//100, eye_r*50//100, eye_r*50//100)

    # 黄色条纹（黄缘龟特征）
    painter.setPen(QPen(head_stripe, bs*55//1000))
    painter.setBrush(Qt.NoBrush)
    # 眼后条纹
    painter.drawLine(eye_px, eye_py - eye_r*80//100, eye_px - bs*30//100, head_y + head_h*10//100)
    painter.drawLine(eye_px, eye_py + eye_r*80//100, eye_px - bs*30//100, head_y + head_h*90//100)
    # 头顶中线
    painter.setPen(QPen(head_stripe, bs*4//100))
    painter.drawLine(head_x + bs*10//100, head_y + head_h*50//100, head_x - bs*5//100, head_y + head_h*50//100)

    # 嘴巴
    painter.setPen(QPen(QColor(40, 30, 15), bs*3//100))
    painter.drawLine(head_x + head_w*85//100, head_y + head_h*55//100, head_x + head_w, head_y + head_h*50//100)

    # 鼻子（两个小孔）
    painter.setBrush(QColor(30, 20, 10))
    nr = bs * 4//100
    painter.drawEllipse(head_x + head_w - nr*2, head_y + head_h*40//100, nr*150//100, nr)
    painter.drawEllipse(head_x + head_w - nr*2, head_y + head_h*60//100, nr*150//100, nr)

    # ── 前腿（左前）───────────────────────────
    leg_color = QColor(65, 100, 55)
    # 左前腿（伸出）
    painter.setBrush(leg_color)
    painter.setPen(QPen(QColor(45, 75, 35), 1))
    painter.drawEllipse(cx - bs*130//100, cy + bs*45//100, bs*45//100, bs*32//100)
    # 小爪子
    painter.setBrush(QColor(50, 50, 40))
    for i in range(3):
        nx = cx - bs*125//100 + i * bs*12//100
        painter.drawEllipse(nx, cy + bs*75//100, bs*7//100, bs*6//100)

    # ── 后腿（左后）───────────────────────────
    painter.setBrush(leg_color)
    painter.setPen(QPen(QColor(45, 75, 35), 1))
    painter.drawEllipse(cx + bs*90//100, cy + bs*45//100, bs*45//100, bs*32//100)
    # 小爪子
    painter.setBrush(QColor(50, 50, 40))
    for i in range(3):
        nx = cx + bs*95//100 + i * bs*12//100
        painter.drawEllipse(nx, cy + bs*75//100, bs*7//100, bs*6//100)

    # ── 右前腿（远处，浅一点）────────────────
    painter.setBrush(QColor(80, 115, 70))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(cx - bs*115//100, cy + bs*58//100, bs*38//100, bs*26//100)

    # ── 右后腿（远处）────────────────────────
    painter.setBrush(QColor(80, 115, 70))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(cx + bs*105//100, cy + bs*58//100, bs*38//100, bs*26//100)

    # ── 尾巴 ─────────────────────────────────
    painter.setBrush(leg_color)
    painter.setPen(Qt.NoPen)
    tail_x = cx + bs*125//100
    tail_y = cy + bs*5//100
    painter.drawEllipse(tail_x, tail_y, bs*30//100, bs*18//100)

    # ── 腹甲边缘 ─────────────────────────────
    painter.setPen(QPen(QColor(140, 110, 60), 1.5))
    painter.setBrush(Qt.NoBrush)
    painter.drawArc(cx - bs*90//100, cy + bs*10//100, bs*180//100, bs*80//100,
                    30*16, 120*16)

    # ── 龟壳上金黄色脊线（黄缘龟特征）────────
    painter.setPen(QPen(QColor(210, 185, 50), bs*45//1000))
    painter.drawLine(cx, cy - bs*65//100, cx, cy + bs*65//100)
    painter.drawLine(cx - bs*70//100, cy - bs*30//100, cx + bs*70//100, cy - bs*30//100)
    painter.drawLine(cx - bs*70//100, cy + bs*30//100, cx + bs*70//100, cy + bs*30//100)

    painter.end()
    return QPixmap.fromImage(img)


# ─────────────────────────────────────────────
# 企鹅表情帧（眨眼 / 开心）
# ─────────────────────────────────────────────
def draw_turtle_face(base_size=80, expression="normal"):
    """返回带表情的头部特写 Pixmap"""
    bs = int(base_size)
    w = bs * 220//100
    h = bs * 180//100
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)

    head_color  = QColor(70, 110, 60)
    stripe      = QColor(220, 195, 55)
    cx, cy = w // 2, h // 2

    # 头
    head_path = QPainterPath()
    head_path.addEllipse(cx - bs*90//100, cy - bs*80//100, bs*180//100, bs*160//100)
    painter.fillPath(head_path, head_color)
    # 高光
    hl = QPainterPath()
    hl.addEllipse(cx - bs*75//100, cy - bs*85//100, bs*150//100, bs*95//100)
    painter.fillPath(hl, QColor(90, 130, 75))

    # 眼睛
    ex = cx - bs*35//100
    ey = cy - bs*10//100
    er = bs*22//100

    if expression == "blink":
        # 眨眼
        painter.setPen(QPen(QColor(20,20,20), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(ex - er, ey, ex + er, ey)
        painter.drawLine(ex + bs*70//100 - er, ey, ex + bs*70//100 + er, ey)
    elif expression == "happy":
        # 眯眼笑
        painter.setPen(QPen(QColor(20,20,20), bs*5//100))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(ex - er, ey - er, er*2, er*2, 0, 180*16)
        painter.drawArc(ex + bs*70//100 - er, ey - er, er*2, er*2, 0, 180*16)
    else:
        # 正常
        painter.setBrush(Qt.white)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(ex - er, ey - er, er*2, er*2)
        painter.drawEllipse(ex + bs*70//100 - er, ey - er, er*2, er*2)
        painter.setBrush(QColor(20,20,20))
        painter.drawEllipse(ex - er*55//100, ey - er*55//100, er*110//100, er*110//100)
        painter.drawEllipse(ex + bs*70//100 - er*55//100, ey - er*55//100, er*110//100, er*110//100)
        # 高光
        painter.setBrush(Qt.white)
        painter.drawEllipse(ex - er*30//100, ey - er*45//100, er*45//100, er*45//100)
        painter.drawEllipse(ex + bs*70//100 - er*30//100, ey - er*45//100, er*45//100, er*45//100)

    # 黄色条纹
    painter.setPen(QPen(stripe, bs*6//100))
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(ex, ey - er*80//100, ex - bs*35//100, cy - bs*20//100)
    painter.drawLine(ex, ey + er*80//100, ex - bs*35//100, cy + bs*20//100)

    # 嘴
    if expression in ("happy", "happy2"):
        painter.setPen(QPen(QColor(40,30,15), bs*4//100))
        painter.drawArc(cx - bs*25//100, cy + bs*10//100, bs*50//100, bs*35//100, 0, 180*16)
    else:
        painter.setPen(QPen(QColor(40,30,15), bs*3//100))
        painter.drawLine(cx - bs*15//100, cy + bs*20//100, cx + bs*15//100, cy + bs*20//100)

    painter.end()
    return QPixmap.fromImage(img)


# ─────────────────────────────────────────────
# 主窗口 — 透明任务栏宠物
# ─────────────────────────────────────────────
class TurtlePet(QWidget):
    # 信号
    say_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.base_size = 80

        # 窗口属性
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setMouseTracking(True)

        # 屏幕 & 任务栏
        self.screen = QApplication.primaryScreen()
        self.screen_geo = self.screen.geometry()
        self.taskbar_height = self._get_taskbar_height()

        # ── 素材模式加载：视频序列帧 > 照片 > 程序绘制 ──
        self.video_mode = False
        self.video_frames = []
        self.photo_mode = False
        self.turtle_pixmap = None
        self.head_pixmap = None
        self.gait_vx = 1.2  # 默认移动速度(px/tick)

        # 视频帧模式：读取同目录 frames/ 下的序列帧
        try:
            frames_dir = _asset_path("frames")
            if frames_dir.is_dir():
                fs = sorted(frames_dir.glob("f*.png"))
                for fp in fs:
                    pm = QPixmap(str(fp))
                    if not pm.isNull():
                        self.video_frames.append(pm)
                if self.video_frames:
                    self.video_mode = True
                    # 步态匹配速度：视频尺度 210px/s → 显示高240 → 42px/s → 0.672px/tick(62.5fps)
                    self.gait_vx = 42.0 / 62.5
                    # 视频素材的固有朝向（frames/facing.txt，默认朝右）
                    self.video_faces_right = True
                    try:
                        ftxt = frames_dir / "facing.txt"
                        if ftxt.exists():
                            self.video_faces_right = (ftxt.read_text(encoding="utf-8").strip().lower() == "right")
                    except Exception:
                        pass
        except Exception:
            pass

        # 窗口尺寸（视频帧按帧尺寸，否则默认 320x240）
        if self.video_mode:
            self.pet_w = self.video_frames[0].width()
            self.pet_h = self.video_frames[0].height()
        else:
            self.pet_w = self.base_size * 4
            self.pet_h = self.base_size * 3

        # 初始位置（任务栏上方中央）
        start_x = self.screen_geo.width() // 2 - self.pet_w // 2
        start_y = self.screen_geo.height() - self.taskbar_height - self.pet_h
        # 安全网：强制将窗口钳制在屏幕可视区域内（防止分辨率变化后跑到屏幕外）
        try:
            avail = self.screen.availableGeometry()
            start_x = max(avail.left(), min(start_x, avail.right() - self.pet_w))
            start_y = max(avail.top(), min(start_y, avail.bottom() - self.pet_h))
        except Exception:
            pass
        self.pos_x = start_x
        self.pos_y = start_y
        self.setGeometry(start_x, start_y, self.pet_w, self.pet_h)

        # 尺寸缩放支持（所有动画等比例缩放）
        self.base_pet_w = self.pet_w
        self.base_pet_h = self.pet_h
        self.scale = 1.0
        self.gait_vx_base = self.gait_vx
        self.setFixedSize(self.pet_w, self.pet_h)

        # 可配置参数（持久化到 桌宠设置.json）
        self.interact_hold_ms = 10000   # 3.png 定格时长(ms)
        try:
            import json as _json
            cfg_path = _program_dir() / "桌宠设置.json"
            if cfg_path.exists():
                cfg = _json.loads(cfg_path.read_text(encoding="utf-8"))
                self.interact_hold_ms = max(1000, int(cfg.get("hold_ms", 10000)))
                self._saved_scale = float(cfg.get("scale", 1.0))
        except Exception:
            pass

        # 移动状态
        self.moving = False
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self._auto_move)
        self.move_timer.start(16)  # ~60fps

        # 动画帧（视频模式按 30fps 播放）
        self.frame_idx  = 0
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self._next_frame)
        self.frame_timer.start(1000 // 30 if self.video_mode else 120)

        # 表情
        self.expression = "normal"
        self.expr_timer = QTimer(self)
        self.expr_timer.timeout.connect(self._change_expression)
        self.expr_timer.start(3000)

        # 单击交互素材（单击 → 1.gif → 3.png 定格10秒 → 2.gif → 恢复走动）
        self.interact1_frames = []
        self.interact2_frames = []
        self.interact3_pixmap = None
        self.interaction = None          # None | "gif1" | "still3" | "gif2"
        self.interact_hold = QTimer(self)  # 3.png 定格计时
        self.interact_hold.setSingleShot(True)
        self.interact_hold.timeout.connect(self._on_hold_done)
        self.interact_interval1 = 140   # 1.mp4 帧间隔(ms)
        self.interact_interval2 = 140   # 2.mp4 帧间隔(ms)
        try:
            idir = _asset_path("interact")
            itxt = idir / "intervals.txt"
            if itxt.exists():
                parts = itxt.read_text(encoding="utf-8").strip().split(",")
                if len(parts) >= 2:
                    self.interact_interval1 = max(10, int(parts[0]))
                    self.interact_interval2 = max(10, int(parts[1]))
            p3 = idir / "3_fit.png"
            if p3.exists():
                pm = QPixmap(str(p3))
                if not pm.isNull():
                    self.interact3_pixmap = pm
            for gname, lst in (("1_", self.interact1_frames), ("2_", self.interact2_frames)):
                for fp in sorted(idir.glob(gname + "*.png")):
                    pm = QPixmap(str(fp))
                    if not pm.isNull():
                        lst.append(pm)
        except Exception:
            pass

        # 眨眼定时
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._blink)
        self.blink_timer.start(2500)

        # 非视频模式：程序绘制 + 照片抠图优先
        if not self.video_mode:
            self.turtle_pixmap = draw_turtle(self.base_size)
            self.head_pixmap   = draw_turtle_face(self.base_size, "normal")
            try:
                img_path = _asset_path("黄缘龟.png")
                if img_path.exists():
                    pm = QPixmap(str(img_path))
                    if not pm.isNull():
                        self.turtle_pixmap = pm.scaled(
                            self.pet_w, self.pet_h,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.photo_mode = True
            except Exception:
                pass

        # 速度向量（视频模式用步态匹配速度）
        self.vx = self.gait_vx
        self.vy = 0.0
        self.facing_right = True

        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        self.show()
        # 恢复上次保存的缩放（需在窗口显示后应用）
        try:
            if getattr(self, "_saved_scale", 1.0) != 1.0:
                self.apply_scale(self._saved_scale)
        except Exception:
            pass

    def _get_taskbar_height(self):
        """获取任务栏高度（修正版：用 SHAppBarMessage 读取真实任务栏尺寸）"""
        try:
            import ctypes
            from ctypes import wintypes
            ABM_GETTASKBARPOS = 0x00000005
            class APPBARDATA(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("hWnd", wintypes.HWND),
                    ("uCallbackMessage", wintypes.UINT),
                    ("uEdge", wintypes.UINT),
                    ("rc", wintypes.RECT),
                    ("lParam", wintypes.LPARAM),
                ]
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            if ctypes.windll.shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(abd)):
                rc = abd.rc
                # 任务栏在屏幕底部时，高度 = 下边 - 上边
                return max(0, rc.bottom - rc.top)
            return 40
        except Exception:
            return 40

    def _next_frame(self):
        # 交互序列：1.gif → 3.png定格 → 2.gif
        if self.interaction == "gif1":
            self.frame_idx += 1
            if self.frame_idx >= len(self.interact1_frames):
                self.interaction = "still3"
                self.frame_timer.stop()
                self.interact_hold.start(self.interact_hold_ms)  # 3.png 定格（可配置时长）
            self.update()
            return
        if self.interaction == "gif2":
            self.frame_idx += 1
            if self.frame_idx >= len(self.interact2_frames):
                self._end_interaction()
            self.update()
            return
        if self.video_mode:
            self.frame_idx = (self.frame_idx + 1) % len(self.video_frames)
        else:
            self.frame_idx = (self.frame_idx + 1) % 4
        self.update()

    def _start_interaction(self):
        """单击触发：播放 1.gif"""
        if not self.interact1_frames or self.interaction is not None:
            return
        self.interaction = "gif1"
        self.frame_idx = 0
        self.vx = 0
        self.moving = False
        self.frame_timer.start(self.interact_interval1)  # 1.mp4 帧间隔
        self.update()

    def _on_hold_done(self):
        """3.png 定格结束 → 播放 2.gif"""
        if self.interaction == "still3":
            self.interaction = "gif2"
            self.frame_idx = 0
            self.frame_timer.start(self.interact_interval2)  # 2.mp4 帧间隔
            self.update()

    def _end_interaction(self):
        """交互结束 → 恢复正常走动"""
        self.interaction = None
        self.frame_timer.start(1000 // 30 if self.video_mode else 120)
        gv = abs(self.gait_vx)
        self.vx = gv if self.facing_right else -gv
        self.moving = False
        self.update()

    def _blink(self):
        if self.photo_mode:
            return  # 照片模式不做眨眼
        if self.expression == "normal":
            self.expression = "blink"
            QTimer.singleShot(150, lambda: setattr(self, 'expression', 'normal'))

    def _change_expression(self):
        if self.video_mode or self.photo_mode:
            return  # 视频/照片模式：不变表情、不说话
        roll = random.random()
        if roll < 0.3:
            self.expression = "happy"
        elif roll < 0.5:
            self.expression = "happy2"
        else:
            self.expression = "normal"
        self.head_pixmap = draw_turtle_face(self.base_size, self.expression)

    def _auto_move(self):
        """自动在任务栏上爬行"""
        if not self.moving:
            self.moving = True

        self.pos_x += self.vx

        max_x = self.screen_geo.width() - self.width()
        min_x = 0

        if self.pos_x >= max_x:
            self.pos_x = max_x
            self.vx = -abs(self.vx)
            self.facing_right = False
        elif self.pos_x <= min_x:
            self.pos_x = 0
            self.vx = abs(self.vx)
            self.facing_right = True

        self.move(int(self.pos_x), int(self.pos_y))

    def _save_config(self):
        """保存设置到 桌宠设置.json"""
        try:
            import json
            data = {"scale": self.scale, "hold_ms": self.interact_hold_ms}
            with open(_program_dir() / "桌宠设置.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def apply_scale(self, s):
        """等比例缩放所有动画（保持底部中心锚点，步速同步缩放）"""
        s = max(0.3, min(3.0, s))
        if abs(s - self.scale) < 0.01:
            return
        g = self.frameGeometry()
        cx = g.center().x()
        bottom = g.bottom()
        self.scale = s
        new_w = max(20, int(round(self.base_pet_w * s)))
        new_h = max(20, int(round(self.base_pet_h * s)))
        self.setFixedSize(new_w, new_h)
        new_x = cx - new_w // 2
        new_y = bottom - new_h
        try:
            avail = self.screen.availableGeometry()
            new_x = max(avail.left(), min(new_x, avail.right() - new_w))
            new_y = max(avail.top(), min(new_y, avail.bottom() - new_h))
        except Exception:
            pass
        self.move(new_x, new_y)
        self.pos_x = float(new_x)
        self.pos_y = float(new_y)
        # 步速随尺寸缩放，保持步伐与地面一致
        self.gait_vx = self.gait_vx_base * s
        if self.interaction is None:
            gv = abs(self.gait_vx)
            self.vx = gv if self.facing_right else -gv
        self.update()

    def _resize_dialog(self):
        """设置对话框：大小滑块 + 3.png 持续时间输入"""
        from PyQt5.QtWidgets import QDialog, QSlider, QLabel, QVBoxLayout, QHBoxLayout, QSpinBox
        dlg = QDialog(self)
        dlg.setWindowTitle("乌龟设置")
        dlg.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(dlg)

        # 大小滑块
        lbl_size = QLabel("乌龟大小")
        layout.addWidget(lbl_size)
        row = QHBoxLayout()
        lbl_min = QLabel("小")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(50, 200)
        slider.setValue(int(self.scale * 100))
        lbl_val = QLabel("%d%%" % int(self.scale * 100))
        lbl_max = QLabel("大")
        row.addWidget(lbl_min)
        row.addWidget(slider, 1)
        row.addWidget(lbl_max)
        layout.addLayout(row)
        layout.addWidget(lbl_val, 0, Qt.AlignCenter)
        slider.valueChanged.connect(lambda v: (lbl_val.setText("%d%%" % v), self.apply_scale(v / 100.0)))
        slider.sliderReleased.connect(self._save_config)

        # 3.png 持续时间输入
        layout.addSpacing(8)
        lbl_hold = QLabel("缩壳/定格画面持续时间（秒）")
        layout.addWidget(lbl_hold)
        row2 = QHBoxLayout()
        spin = QSpinBox()
        spin.setRange(1, 120)
        spin.setValue(self.interact_hold_ms // 1000)
        spin.setSuffix(" 秒")
        row2.addWidget(spin, 1)
        layout.addLayout(row2)
        spin.valueChanged.connect(lambda v: (setattr(self, "interact_hold_ms", v * 1000), self._save_config()))

        dlg.resize(320, 170)
        dlg.exec_()

    def _show_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(245,240,230,240);
                border: 1px solid rgba(150,120,60,150);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(210,185,50,100);
            }
        """)

        act_size    = QAction("⚙️ 设置", menu)
        act_about   = QAction("ℹ️ 关于", menu)
        act_quit    = QAction("❌ 退出", menu)

        act_size.triggered.connect(self._resize_dialog)
        act_about.triggered.connect(self._about)
        act_quit.triggered.connect(self.close)

        menu.addAction(act_size)
        menu.addAction(act_about)
        menu.addSeparator()
        menu.addAction(act_quit)
        menu.exec_(self.mapToGlobal(pos))

    def _about(self):
        QMessageBox.about(self, "关于黄缘龟桌宠",
            "🐢 黄缘龟桌宠\n\n"
            "基于 PyQt5 构建的可爱桌面宠物\n"
            "黄缘龟会在任务栏上自动爬行\n"
            "右键菜单有更多互动哦~\n\n"
            "点击拖动可移动位置"
        )

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 单击交互：1.gif / 3.png / 2.gif
        if self.interaction == "gif1":
            pm = self.interact1_frames[min(self.frame_idx, len(self.interact1_frames)-1)]
        elif self.interaction == "gif2":
            pm = self.interact2_frames[min(self.frame_idx, len(self.interact2_frames)-1)]
        elif self.interaction == "still3" and self.interact3_pixmap is not None:
            pm = self.interact3_pixmap
        else:
            pm = None
        if pm is not None:
            if self.video_faces_right != self.facing_right:
                pm = pm.transformed(QTransform().scale(-1, 1))
            painter.drawPixmap(0, 0, self.width(), self.height(), pm)
            return

        if self.video_mode:
            # 视频帧：播放序列帧；当固有朝向与移动方向不一致时水平镜像（保证头朝移动方向）
            pm = self.video_frames[self.frame_idx]
            if self.video_faces_right != self.facing_right:
                pm = pm.transformed(QTransform().scale(-1, 1))
            painter.drawPixmap(0, 0, self.width(), self.height(), pm)
            return

        # 切换左右朝向（水平镜像）
        pm = self.turtle_pixmap
        if not self.facing_right:
            pm = self.turtle_pixmap.transformed(QTransform().scale(-1, 1))

        # 走路帧动画（轻微上下抖动）
        bob = [0, -3, -5, -3][self.frame_idx]
        painter.drawPixmap(0, bob, self.width(), self.height(), pm)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press_pos = e.globalPos()
            self._press_time = time.monotonic()
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            self.moving = False  # 暂停自动移动
            self.vx = 0

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            new_pos = e.globalPos() - self.drag_pos
            self.move(new_pos)
            self.pos_x = new_pos.x()
            self.pos_y = new_pos.y()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            # 交互进行中：不恢复走动，也不触发新交互
            if self.interaction is not None:
                return
            # 单击判定：位移小且时间短 → 触发交互动画
            moved = (e.globalPos() - self._press_pos).manhattanLength()
            dt = time.monotonic() - self._press_time
            if moved < 10 and dt < 0.4:
                self._start_interaction()
                return
            # 拖动结束：恢复移动（视频模式用步态匹配速度）
            gv = abs(self.gait_vx)
            self.vx = gv if self.facing_right else -gv
            self.moving = False

    def wheelEvent(self, e):
        # 滚轮调速
        delta = e.angleDelta().y()
        self.vx += delta * 0.002
        self.vx = max(0.1, min(4.0, self.vx))

    def close(self):
        self.interact_hold.stop()
        self.move_timer.stop()
        self.frame_timer.stop()
        self.expr_timer.stop()
        self.blink_timer.stop()
        super().close()
        # 窗口关闭后让进程彻底退出，避免出现“无窗口僵尸进程”
        app = QApplication.instance()
        if app is not None:
            app.quit()


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────
def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("黄缘龟桌宠")

        # 仅允许一个实例
        from PyQt5.QtCore import QSharedMemory
        shm = QSharedMemory("TurtlePet_SingleInstance_v1")
        if shm.attach():
            # 已有实例在运行：把它的窗口调到前台（不弹窗，避免用户以为没启动）
            try:
                import ctypes
                u = ctypes.windll.user32
                hwnd = u.FindWindowW(None, "黄缘龟桌宠")
                if hwnd:
                    u.ShowWindow(hwnd, 9)  # SW_RESTORE
                    u.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)  # TOPMOST+nomove+nosize+show
                    u.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # NOTOPMOST
                    u.SetForegroundWindow(hwnd)
            except Exception:
                pass
            sys.exit(0)
        shm.create(1)

        pet = TurtlePet()
        sys.exit(app.exec_())
    except Exception:
        import traceback
        try:
            log_path = _log_path()
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("===== " + time.strftime("%Y-%m-%d %H:%M:%S") + " =====\n")
                f.write(traceback.format_exc())
                f.write("\n")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
