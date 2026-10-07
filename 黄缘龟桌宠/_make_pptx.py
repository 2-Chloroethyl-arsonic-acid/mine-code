# -*- coding: utf-8 -*-
"""生成班会分享 PPT: 寻学法之径，赴成长之途 (16:9, 微软雅黑, 墨蓝+暖金+米纸)"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import copy

# ---------- 调色板 ----------
INK   = RGBColor(0x24, 0x3B, 0x53)   # 墨蓝(主文字)
INK2  = RGBColor(0x3E, 0x5C, 0x76)   # 墨蓝浅
GOLD  = RGBColor(0xC0, 0x8A, 0x2D)   # 暖金(强调)
GOLD_L= RGBColor(0xEF, 0xDF, 0xB8)   # 浅金底
CREAM = RGBColor(0xFB, 0xF6, 0xEC)   # 米纸底
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MUTED = RGBColor(0x7A, 0x82, 0x8A)
CARD_B= RGBColor(0xF1, 0xEA, 0xDA)   # 卡片米

FONT = "微软雅黑"
SW, SH = Inches(13.333), Inches(7.5)

prs = Presentation()
prs.slide_width, prs.slide_height = SW, SH
BLANK = prs.slide_layouts[6]

def set_font(run, size=None, bold=None, color=None, name=FONT, italic=None):
    f = run.font
    if size is not None: f.size = Pt(size)
    if bold is not None: f.bold = bold
    if color is not None: f.color.rgb = color
    if italic is not None: f.italic = italic
    f.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', name)

def txbox(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
          space_after=6, line_spacing=1.12):
    """lines: list of (text, size, bold, color) 或 list of list(runs)"""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        if isinstance(ln, list):
            for (t, s, b, c) in ln:
                r = p.add_run(); r.text = t
                set_font(r, s, b, c)
        else:
            t, s, b, c = ln
            r = p.add_run(); r.text = t
            set_font(r, s, b, c)
    return tb

def rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE,
         line_w=None, shadow=False, adj=None):
    sp = slide.shapes.add_shape(shape, x, y, w, h)
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w or 1)
    sp.shadow.inherit = False
    if adj is not None:
        try: sp.adjustments[0] = adj
        except Exception: pass
    return sp

def bg(slide, color=CREAM):
    rect(slide, 0, 0, SW, SH, fill=color)

def header(slide, num, title, sub=None):
    """内容页标题区: 页码+标题+金线"""
    txbox(slide, Inches(0.55), Inches(0.32), Inches(0.7), Inches(0.5),
          [(num, 15, True, GOLD)])
    rect(slide, Inches(0.62), Inches(0.78), Inches(0.30), Pt(3.2), fill=GOLD)
    txbox(slide, Inches(1.0), Inches(0.28), Inches(9.2), Inches(0.7),
          [(title, 27, True, INK)])
    if sub:
        txbox(slide, Inches(1.03), Inches(0.92), Inches(10.5), Inches(0.4),
              [(sub, 12.5, False, MUTED)])

def pageno(slide, i, total):
    txbox(slide, Inches(12.35), Inches(7.02), Inches(0.8), Inches(0.35),
          [("%d / %d" % (i, total), 10, False, MUTED)], align=PP_ALIGN.RIGHT)

def deco_circles(slide):
    c1 = rect(slide, Inches(12.15), Inches(-0.75), Inches(1.9), Inches(1.9),
              fill=GOLD_L, shape=MSO_SHAPE.OVAL)
    c1.fill.fore_color.rgb = GOLD_L
    c2 = rect(slide, Inches(12.75), Inches(5.9), Inches(0.55), Inches(0.55),
              fill=GOLD, shape=MSO_SHAPE.OVAL)
    c3 = rect(slide, Inches(-0.5), Inches(6.4), Inches(1.3), Inches(1.3),
              fill=GOLD_L, shape=MSO_SHAPE.OVAL)

TOTAL = 11
notes_all = {}

def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text

# ================= S1 封面 =================
s = prs.slides.add_slide(BLANK); bg(s)
deco_circles(s)
rect(s, Inches(0.9), Inches(1.02), Inches(1.7), Pt(2.6), fill=GOLD)
txbox(s, Inches(0.92), Inches(1.25), Inches(6), Inches(0.5),
      [("学习方法 · 主题班会分享", 16, False, INK2)])
txbox(s, Inches(0.9), Inches(2.05), Inches(11.6), Inches(1.35),
      [("寻学法之径", 51, True, INK)])
txbox(s, Inches(0.9), Inches(3.15), Inches(11.6), Inches(1.35),
      [("赴成长之途", 51, True, INK)])
rect(s, Inches(0.95), Inches(4.55), Inches(2.6), Pt(2.6), fill=GOLD)
txbox(s, Inches(0.95), Inches(4.8), Inches(11.5), Inches(0.55),
      [("学而有法 · 行则将至", 19, False, GOLD)])
txbox(s, Inches(0.95), Inches(6.15), Inches(11), Inches(0.9),
      [("分享人：________　班级：________　日期：2026.9", 13, False, MUTED)])
note(s, "开场：同学们好，今天班会的主题是学习方法。先问大家一个问题——"
        "你有没有过'看起来很努力，成绩却不理想'的困惑？如果有，今天的内容就是为你准备的。")

# ================= S2 目录 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "01", "今天聊什么", "四个部分，一次讲透「怎么学」")
items = [
    ("02", "为什么要有方法", "努力 ≠ 蛮力，方法才是杠杆"),
    ("03", "学习误区自查", "看看你有没有'假努力'"),
    ("04", "好方法工具箱", "预习听课复习 · 错题 · 时间 · 状态"),
    ("05", "一起行动", "从今天起，只改一个小习惯"),
]
for i, (num, t, d) in enumerate(items):
    x = Inches(0.9 + (i % 2) * 5.9)
    y = Inches(2.0 + (i // 2) * 2.15)
    card = rect(s, x, y, Inches(5.55), Inches(1.75), fill=WHITE, line=GOLD_L,
                shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1.2, adj=0.06)
    c = rect(s, x + Inches(0.35), y + Inches(0.42), Inches(0.92), Inches(0.92),
             fill=GOLD, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = num; set_font(r, 20, True, WHITE)
    txbox(s, x + Inches(1.55), y + Inches(0.38), Inches(3.85), Inches(1.1),
          [(t, 18, True, INK), (d, 11.5, False, MUTED)], space_after=4)
note(s, "今天分四步走：先讲清楚为什么方法重要，再对照自查误区，"
        "然后给出可以马上用的工具，最后每个人给自己定一个小目标。")

# ================= S3 为什么要有方法 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "02", "为什么要有方法？", "同样的时间，方法不同，结果天差地别")
# 左卡
l = rect(s, Inches(0.9), Inches(2.1), Inches(5.7), Inches(3.6), fill=WHITE,
         line=RGBColor(0xE3,0xD5,0xB5), shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1, adj=0.05)
txbox(s, Inches(1.25), Inches(2.4), Inches(5), Inches(0.5),
      [("❌ 盲学：靠时间堆", 18, True, RGBColor(0xA8,0x6B,0x5A))])
txbox(s, Inches(1.25), Inches(3.05), Inches(5.05), Inches(2.4),
      [("· 笔记抄了厚厚一本，却不进脑子", 13.5, False, INK2),
       ("· 题刷了一堆，错的还是错", 13.5, False, INK2),
       ("· 熬夜到很晚，白天上课犯困", 13.5, False, INK2),
       ("· 越学越累，越累越焦虑", 13.5, False, INK2)], space_after=8)
# 右卡
r = rect(s, Inches(6.75), Inches(2.1), Inches(5.7), Inches(3.6), fill=WHITE,
         line=GOLD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1.5, adj=0.05)
txbox(s, Inches(7.1), Inches(2.4), Inches(5), Inches(0.5),
      [("✅ 巧学：让方法发力", 18, True, GOLD)])
txbox(s, Inches(7.1), Inches(3.05), Inches(5.05), Inches(2.4),
      [("· 预习带着问题，听课有的放矢", 13.5, False, INK2),
       ("· 当天复习，对抗遗忘曲线", 13.5, False, INK2),
       ("· 错题归类重做，错了不再错", 13.5, False, INK2),
       ("· 越学越顺，越顺越有成就感", 13.5, False, INK2)], space_after=8)
txbox(s, Inches(1.0), Inches(6.1), Inches(11.4), Inches(0.6),
      [("方法不是捷径，而是", 15, False, INK),
       ("杠杆", 15, True, GOLD),
       ("——同样的努力，放在正确的点上，效果翻倍。", 15, False, INK)])
note(s, "先摆事实：班里一定有同学看起来不费力却学得好，差别往往不在智商，"
        "而在方法。方法不是偷懒的捷径，是让努力更有价值的杠杆。")

# ================= S4 误区自查 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "03", "学习误区自查", "中了几个？别急，先承认，再破解")
mis = [
    ("误区①", "笔记 = 板书复印机", "只动手不动脑，抄完再也没翻开过"),
    ("误区②", "刷题量 = 安全感", "用'今天做了50题'安慰自己，错因从不复盘"),
    ("误区③", "熬夜 = 努力勋章", "感动了自己，透支了明天的注意力"),
    ("误区④", "预习 = 上课前翻翻书", "没有带着问题，预习等于没预"),
]
for i, (t1, t2, d) in enumerate(mis):
    x = Inches(0.9 + (i % 2) * 5.9)
    y = Inches(2.0 + (i // 2) * 2.25)
    rect(s, x, y, Inches(5.55), Inches(1.95), fill=WHITE, line=RGBColor(0xE8,0xDC,0xC4),
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1, adj=0.07)
    txbox(s, x + Inches(0.35), y + Inches(0.3), Inches(1.5), Inches(0.45),
          [(t1, 13, True, RGBColor(0xB0,0x6A,0x5A))])
    txbox(s, x + Inches(1.7), y + Inches(0.28), Inches(3.7), Inches(0.5),
          [(t2, 16.5, True, INK)])
    txbox(s, x + Inches(0.38), y + Inches(1.0), Inches(4.85), Inches(0.85),
          [(d, 12, False, MUTED)], space_after=0)
note(s, "大家可以心里默默对号入座，这四条是'假努力'最常见的表现。"
        "自查的目的不是批评自己，而是看清问题出在哪。")

# ================= S5 误区破解对照 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "04", "破解：从「假努力」到「真有效」", "一句话记住一个改变")
pairs = [
    ("把笔记当复印机", "听课记思路、记疑问，课后补成自己的话"),
    ("盲目刷题求数量", "刷题三问：错在哪？为什么？下次怎么避？"),
    ("熬夜换时长", "效率优先；睡眠是学习的一部分，不丢人"),
    ("预习就是翻书", "预习 = 花10分钟找出'看不懂的地方'并标记"),
]
y = Inches(1.9)
for bad, good in pairs:
    rect(s, Inches(0.9), y, Inches(5.35), Inches(1.02), fill=RGBColor(0xF6,0xEC,0xDE),
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.12)
    txbox(s, Inches(1.15), y + Inches(0.2), Inches(4.9), Inches(0.65),
          [("✗  " + bad, 13.5, False, RGBColor(0xA8,0x6B,0x5A))])
    rect(s, Inches(6.55), y + Inches(0.14), Inches(0.55), Inches(0.55), fill=GOLD, shape=MSO_SHAPE.OVAL)
    txbox(s, Inches(6.62), y + Inches(0.17), Inches(0.5), Inches(0.5),
          [("→", 18, True, WHITE)], align=PP_ALIGN.CENTER)
    rect(s, Inches(7.35), y, Inches(5.1), Inches(1.02), fill=WHITE, line=GOLD_L,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1, adj=0.12)
    txbox(s, Inches(7.6), y + Inches(0.2), Inches(4.65), Inches(0.65),
          [("✓  " + good, 13.5, False, INK)])
    y += Inches(1.22)
note(s, "对照左边的问题，右边给了一句话解法。大家不用全做，先挑最容易的一条。"
        "接下来四个板块，就是把这些解法展开成具体工具。")

# ================= S6 方法① 学习闭环 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "05", "好方法①：学习闭环", "预习 → 听课 → 复习 → 检测，缺一环都打折")
steps = [
    ("预习", "带着问题听课", "10分钟·标记不懂处"),
    ("听课", "解决80%问题", "跟着思路走·记疑问"),
    ("复习", "当天及时做", "对抗遗忘曲线"),
    ("检测", "做题·讲出来", "会讲才是真会"),
]
for i, (t, m, d) in enumerate(steps):
    x = Inches(0.75 + i * 3.05)
    rect(s, x, Inches(2.35), Inches(2.75), Inches(2.1), fill=WHITE, line=GOLD_L,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1.2, adj=0.08)
    c = rect(s, x + Inches(0.95), Inches(2.62), Inches(0.85), Inches(0.85),
             fill=INK, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = str(i+1); set_font(r, 22, True, WHITE)
    txbox(s, x + Inches(0.1), Inches(3.7), Inches(2.55), Inches(0.55),
          [(t, 19, True, INK)], align=PP_ALIGN.CENTER)
    txbox(s, x + Inches(0.15), Inches(4.25), Inches(2.45), Inches(0.4),
          [(m, 12, True, GOLD)], align=PP_ALIGN.CENTER)
    txbox(s, x + Inches(0.15), Inches(4.72), Inches(2.45), Inches(0.8),
          [(d, 11, False, MUTED)], align=PP_ALIGN.CENTER)
    if i < 3:
        txbox(s, x + Inches(2.75), Inches(3.02), Inches(0.35), Inches(0.5),
              [("→", 22, True, GOLD)], align=PP_ALIGN.CENTER)
txbox(s, Inches(0.9), Inches(5.35), Inches(11.6), Inches(1.3),
      [("为什么复习最容易被偷走？", 14, True, INK),
       ("艾宾浩斯遗忘曲线：学完 1 天后遗忘最快。当天睡前花 10 分钟回顾，比考前突击 2 小时更有效。",
        13, False, INK2)], space_after=6)
note(s, "学习不是单点动作，是一条闭环。预习是为了带着问题来听课；"
        "复习要'当天'，因为遗忘在第一天最快；检测最狠的一招是'讲给别人听'。")

# ================= S7 方法② 错题本 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "06", "好方法②：错题本的正确打开方式", "错题本不是抄写本，是你的成长地图")
steps2 = [
    ("① 归类", "别抄题，先贴标签", "粗心？概念不清？思路断？按错因归类"),
    ("② 重做", "遮住答案定期重做", "一周后重做一遍，做对才叫真会"),
    ("③ 讲出来", "费曼学习法", "能把题讲给同学听，才算真正掌握"),
]
for i, (t, m, d) in enumerate(steps2):
    x = Inches(0.9 + i * 3.95)
    rect(s, x, Inches(2.35), Inches(3.6), Inches(2.6), fill=WHITE, line=GOLD_L,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1.2, adj=0.07)
    txbox(s, x + Inches(0.4), Inches(2.75), Inches(2.9), Inches(0.5),
          [(t, 21, True, GOLD)])
    txbox(s, x + Inches(0.4), Inches(3.35), Inches(2.9), Inches(0.5),
          [(m, 15, True, INK)])
    txbox(s, x + Inches(0.4), Inches(4.0), Inches(2.85), Inches(0.85),
          [(d, 12, False, MUTED)], space_after=0)
txbox(s, Inches(0.95), Inches(5.5), Inches(11.5), Inches(0.9),
      [("💡 一句话：错题的价值不在'抄'，在'不再错'。错题本越用越薄，成绩越走越高。",
        14, False, INK)], space_after=0)
note(s, "很多同学错题本抄得工整，却从不重看，那是感动自己。"
        "正确姿势是三步：按错因归类、遮答案重做、把题讲给别人。")

# ================= S8 方法③ 时间管理 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "07", "好方法③：时间管理三板斧", "不是没时间，是时间没被认真对待")
tm = [
    ("番茄钟", "25分钟专注 + 5分钟休息", "一轮一轮来，让专注可计量"),
    ("四象限", "先做重要不紧急的事", "预习、复习都属于这一类"),
    ("碎片时间", "课间·排队·等车", "背 3 个单词，也比发呆强"),
]
for i, (t, m, d) in enumerate(tm):
    x = Inches(0.9 + i * 3.95)
    rect(s, x, Inches(2.35), Inches(3.6), Inches(2.7), fill=WHITE, line=GOLD_L,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1.2, adj=0.07)
    rect(s, x + Inches(0.3), Inches(2.6), Inches(0.14), Inches(2.15), fill=GOLD)
    txbox(s, x + Inches(0.65), Inches(2.75), Inches(2.8), Inches(0.5),
          [(t, 20, True, INK)])
    txbox(s, x + Inches(0.65), Inches(3.4), Inches(2.8), Inches(1.0),
          [(m, 13.5, True, GOLD)], space_after=2)
    txbox(s, x + Inches(0.65), Inches(4.45), Inches(2.8), Inches(0.6),
          [(d, 11.5, False, MUTED)], space_after=0)
txbox(s, Inches(0.95), Inches(5.6), Inches(11.5), Inches(0.7),
      [("⏰ 建议：每天睡前 5 分钟，写下明天最重要的 3 件事。", 14, False, INK)])
note(s, "时间管理不用花哨：番茄钟帮你在家进入状态；四象限提醒你别总被'紧急'绑架；"
        "碎片时间积少成多。今晚就可以试试写明天的三件事。")

# ================= S9 方法④ 状态管理 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "08", "好方法④：状态，是学习的地基", "学不进去，往往不是不努力，是状态不对")
st = [
    ("环境", "书桌只留当下要用的", "手机放另一个房间·物理隔离"),
    ("节奏", "学45分钟，动一动", "久坐犯困，站起来效率反而高"),
    ("身体", "睡眠 ≥ 7小时 + 运动", "大脑在睡眠里整理知识"),
]
for i, (t, m, d) in enumerate(st):
    x = Inches(0.9 + i * 3.95)
    rect(s, x, Inches(2.35), Inches(3.6), Inches(2.55), fill=WHITE, line=GOLD_L,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1.2, adj=0.07)
    txbox(s, x + Inches(0.4), Inches(2.75), Inches(2.9), Inches(0.55),
          [(t, 19, True, INK)])
    txbox(s, x + Inches(0.4), Inches(3.45), Inches(2.85), Inches(0.9),
          [(m, 13.5, True, GOLD)], space_after=2)
    txbox(s, x + Inches(0.4), Inches(4.4), Inches(2.85), Inches(0.5),
          [(d, 11.5, False, MUTED)], space_after=0)
txbox(s, Inches(0.95), Inches(5.5), Inches(11.5), Inches(0.9),
      [("🌙 别把'熬夜'当成努力，把'睡好'当成策略。", 15, True, INK)])
note(s, "想专注，先伺候好状态：干净的环境、适度的运动、充足的睡眠。"
        "这三样不花一分钱，却是效率最大的杠杆。")

# ================= S10 行动环节 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
header(s, "09", "现场行动：写下你的小改变", "30 秒，只选一条，从今天开始")
rect(s, Inches(0.9), Inches(2.15), Inches(11.55), Inches(3.3), fill=WHITE,
     line=GOLD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_w=1.6, adj=0.06)
txbox(s, Inches(1.5), Inches(2.55), Inches(10.4), Inches(0.6),
      [("请写下：未来两周，我要坚持的一个学习方法：", 18, True, INK)])
rect(s, Inches(1.5), Inches(3.45), Inches(10.35), Inches(1.15), fill=RGBColor(0xF6,0xEF,0xE0),
     shape=MSO_SHAPE.RECTANGLE)
txbox(s, Inches(1.75), Inches(4.85), Inches(10), Inches(0.5),
      [("（例：① 每天睡前回顾当天内容 10 分钟  ② 错题一周后重做一遍  ③ 写作业前先收手机）",
        12, False, MUTED)])
txbox(s, Inches(1.5), Inches(6.0), Inches(10.4), Inches(0.7),
      [("写完的同学举个手，我随机请 2–3 位分享，互相偷师 😄", 15, True, GOLD)])
note(s, "到这里给大家 30 秒写下一个'两周内要坚持的小方法'。"
        "写比想有用——白纸黑字就是承诺。随机请两三位同学分享，气氛活跃一些。")

# ================= S11 结尾 =================
s = prs.slides.add_slide(BLANK); bg(s); deco_circles(s)
rect(s, Inches(0.9), Inches(1.6), Inches(11.55), Inches(4.2), fill=INK,
     shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.05)
txbox(s, Inches(1.6), Inches(2.35), Inches(10.2), Inches(1.0),
      [("路虽远，行则将至；事虽难，做则必成。", 26, True, WHITE)],
      align=PP_ALIGN.CENTER)
txbox(s, Inches(1.6), Inches(3.6), Inches(10.2), Inches(1.0),
      [("学而有法 · 行则将至", 18, False, GOLD_L)], align=PP_ALIGN.CENTER)
txbox(s, Inches(1.6), Inches(4.6), Inches(10.2), Inches(0.7),
      [("—— 与每一位正在路上的你共勉", 13, False, RGBColor(0xC9,0xD4,0xDE))],
      align=PP_ALIGN.CENTER)
txbox(s, Inches(0.9), Inches(6.35), Inches(11.55), Inches(0.6),
      [("你的独家学习方法是什么？欢迎课下继续交流～", 14, False, INK2)],
      align=PP_ALIGN.CENTER)
note(s, "结尾送大家一句话：路虽远，行则将至。方法不在多，"
        "选一条坚持下去，两周后看看变化。谢谢大家！")

prs.save(r"C:\Users\Administrator\Desktop\寻学法之径赴成长之途-班会分享.pptx")
print("saved, slides:", len(prs.slides._sldIdLst))
