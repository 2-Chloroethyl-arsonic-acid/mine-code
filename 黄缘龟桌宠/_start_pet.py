# -*- coding: utf-8 -*-
"""静默启动桌宠：pythonw + CREATE_NO_WINDOW，完全不弹命令框；自动发现 pythonw"""
import subprocess, os, sys, glob

candidates = [
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python313\pythonw.exe",
    r"C:\Program Files\Python313\pythonw.exe",
    r"C:\Python313\pythonw.exe",
]
for pat in (r"C:\Users\Administrator\AppData\Local\Programs\Python\Python*\pythonw.exe",
            r"C:\Program Files\Python*\pythonw.exe"):
    candidates.extend(sorted(glob.glob(pat)))

pyw = next((c for c in candidates if os.path.exists(c)), None)
script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "黄缘龟桌宠.py")
if not pyw:
    sys.exit("pythonw not found")
if not os.path.exists(script):
    sys.exit("script not found: " + script)
subprocess.Popen([pyw, script], creationflags=0x08000000)  # CREATE_NO_WINDOW
print("launched silently: %s" % os.path.basename(pyw))
