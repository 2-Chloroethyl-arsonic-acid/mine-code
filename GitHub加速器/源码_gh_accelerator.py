# -*- coding: utf-8 -*-
"""
GitHub 加速器（精简版 v1.1）
- 原理：GitHub 各域名在本网络下仅 DNS 被污染，改用可达 IP 直连即可恢复访问
- 功能：自动测速挑选最快 IP -> 写入 hosts -> 刷新 DNS；一键停止/还原
- v1.1：自动处理冲突（把指向 127.0.0.1 的屏蔽条目注释掉，停止时还原）；检测 Steam++ 并提醒
- 依赖：仅 Python 标准库（tkinter GUI）
"""
import ctypes
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext

APP_NAME = "GitHub 加速器"
VERSION = "1.1"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
HOSTS_BAK = os.path.join(os.environ.get("TEMP", "."), "hosts.github-acc.bak")
MARK_START = "# >>> GitHub加速器 START >>>"
MARK_END = "# <<< GitHub加速器 END <<<"
CONFLICT_MARK = "# [被GitHub加速器停用] "

CANDIDATES = {
    "github.com": ["20.27.177.113", "20.205.243.166", "140.82.114.3"],
    "api.github.com": ["20.205.243.168", "140.82.112.6"],
    "raw.githubusercontent.com": ["185.199.108.133", "185.199.109.133",
                                  "185.199.110.133", "185.199.111.133"],
    "objects.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
    "gist.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
    "codeload.github.com": ["20.205.243.166", "20.205.243.165", "140.82.112.9"],
    "avatars.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
    "github.githubassets.com": ["185.199.108.154", "185.199.109.154"],
    "camo.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
    "media.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
    "user-images.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
    "private-user-images.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
}
LOG_FILE = os.path.join(os.environ.get("TEMP", "."), "github-acc.log")


def log(msg):
    line = time.strftime("[%H:%M:%S] ") + msg
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    try:
        params = " ".join('"%s"' % a for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        return True
    except Exception:
        return False


def steampp_running():
    """检测 Steam++ 是否在运行（它会覆盖 hosts）"""
    try:
        out = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=15,
                             errors="ignore").stdout.lower()
        return "steam++" in out
    except Exception:
        return False


def tls_ping(host, ip, timeout=3.0):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        t0 = time.time()
        with socket.create_connection((ip, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return time.time() - t0
    except Exception:
        return None


def pick_fastest(host):
    best = (None, None)
    for ip in CANDIDATES.get(host, []):
        ts = [t for t in (tls_ping(host, ip) for _ in range(2)) if t is not None]
        if ts:
            ms = round(min(ts) * 1000)
            if best[1] is None or ms < best[1]:
                best = (ip, ms)
    return best


def read_hosts():
    with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_hosts(text):
    with open(HOSTS_PATH, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)


def flush_dns():
    try:
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=20)
        log("DNS 缓存已刷新")
    except Exception as e:
        log("刷新 DNS 失败: %s" % e)


def remove_block(text):
    lines, skip = [], False
    for ln in text.splitlines(keepends=True):
        if MARK_START in ln:
            skip = True; continue
        if MARK_END in ln:
            skip = False; continue
        if not skip:
            out = ln
            if out.startswith(CONFLICT_MARK):        # 恢复被停用的冲突条目
                out = out[len(CONFLICT_MARK):]
            lines.append(out)
    return "".join(lines)


def is_accelerated():
    try:
        return MARK_START in read_hosts()
    except Exception:
        return False


def build_hosts_text(mapping):
    """生成新的 hosts 内容：停用指向本机的冲突条目 + 追加加速块"""
    targets = set(mapping.keys())
    lines = []
    for ln in remove_block(read_hosts()).splitlines(keepends=True):
        s = ln.strip()
        m = re.match(r"^(127\.0\.0\.1|0\.0\.0\.0|::1)\s+(\S+)", s)
        if m and m.group(2).split("#")[0].strip() in targets:
            lines.append(CONFLICT_MARK + ln)          # 屏蔽条目 -> 停用
        else:
            lines.append(ln)
    text = "".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    text += "%s\n" % MARK_START
    text += "# 由 %s v%s 自动生成（%s）\n" % (APP_NAME, VERSION, time.strftime("%Y-%m-%d %H:%M"))
    for host, ip in mapping.items():
        text += "%-40s %s\n" % (ip, host)
    text += "%s\n" % MARK_END
    return text


def apply_acceleration(progress):
    if steampp_running():
        progress("⚠️ 检测到 Steam++ 正在运行：它会定时覆盖 hosts，建议先退出 Steam++！")
    results, mapping = [], {}
    for i, host in enumerate(CANDIDATES, 1):
        progress("测速中 (%d/%d) %s ..." % (i, len(CANDIDATES), host))
        ip, ms = pick_fastest(host)
        if ip:
            mapping[host] = ip
            results.append((host, ip, ms))
            progress("  ✓ %s -> %s (%d ms)" % (host, ip, ms))
        else:
            progress("  × %s 无可用 IP（已跳过）" % host)
    if not mapping:
        raise RuntimeError("所有域名测速均失败，请检查网络")
    if not os.path.exists(HOSTS_BAK):
        try:
            with open(HOSTS_BAK, "w", encoding="utf-8", errors="ignore") as f:
                f.write(read_hosts())
            log("已备份原始 hosts -> %s" % HOSTS_BAK)
        except Exception as e:
            log("备份 hosts 失败: %s" % e)
    write_hosts(build_hosts_text(mapping))
    flush_dns()
    return results


def stop_acceleration():
    write_hosts(remove_block(read_hosts()))
    flush_dns()
    return True


# ---------------- GUI ----------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("%s v%s" % (APP_NAME, VERSION))
        root.geometry("780x540")
        root.configure(bg="#f6f7f9")

        tk.Label(root, text="🐙 " + APP_NAME, font=("Microsoft YaHei", 16, "bold"),
                 bg="#f6f7f9", fg="#124029").pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(root, text="自动测速最优 IP 并写入 hosts，仅加速 GitHub 相关域名",
                 font=("Microsoft YaHei", 10), bg="#f6f7f9", fg="#666").pack(anchor="w", padx=16)

        bar = tk.Frame(root, bg="#f6f7f9")
        bar.pack(fill="x", padx=16, pady=10)
        self.btn_on = tk.Button(bar, text="🚀 一键加速", font=("Microsoft YaHei", 11, "bold"),
                                bg="#1F6B45", fg="white", activebackground="#175536",
                                width=14, command=self.on_click, relief="flat")
        self.btn_on.pack(side="left")
        self.btn_off = tk.Button(bar, text="⏹ 停止并还原", font=("Microsoft YaHei", 11),
                                 bg="#fff", fg="#333", width=14, relief="groove",
                                 command=self.off_click)
        self.btn_off.pack(side="left", padx=10)
        self.btn_test = tk.Button(bar, text="📶 仅测速", font=("Microsoft YaHei", 11),
                                  bg="#fff", fg="#333", width=10, relief="groove",
                                  command=self.test_click)
        self.btn_test.pack(side="left")

        self.status = tk.Label(root, text="", font=("Microsoft YaHei", 10), bg="#f6f7f9", fg="#1F6B45")
        self.status.pack(anchor="w", padx=16)

        self.txt = scrolledtext.ScrolledText(root, font=("Consolas", 9), bg="#ffffff",
                                             fg="#222", relief="flat")
        self.txt.pack(fill="both", expand=True, padx=16, pady=(6, 12))
        self.refresh_status()
        self.log("就绪。管理员权限：%s" % ("是" if is_admin() else "否（加速需管理员）"))
        if steampp_running():
            self.log("⚠️ 检测到 Steam++ 正在运行（它会覆盖 hosts），使用本工具前请先退出 Steam++。")

    def log(self, msg):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.root.update_idletasks()

    def refresh_status(self):
        self.status.config(text=("当前状态：✅ 已加速" if is_accelerated() else "当前状态：⚪ 未加速"))

    def guard_admin(self):
        if is_admin():
            return True
        if messagebox.askyesno(APP_NAME, "需要管理员权限修改 hosts 文件。\n是否以管理员身份重新启动？"):
            if elevate():
                self.root.destroy()
            else:
                messagebox.showerror(APP_NAME, "提权失败，请右键以管理员身份运行。")
        return False

    def on_click(self):
        if not self.guard_admin():
            return
        self.btn_on.config(state="disabled")
        threading.Thread(target=self._do_on, daemon=True).start()

    def _do_on(self):
        try:
            res = apply_acceleration(self.log)
            self.log("✅ 加速完成，共 %d 个域名生效：" % len(res))
            for host, ip, ms in res:
                self.log("   %-38s %s (%dms)" % (host, ip, ms))
        except Exception as e:
            self.log("❌ 加速失败: %s" % e)
            messagebox.showerror(APP_NAME, str(e))
        finally:
            self.btn_on.config(state="normal")
            self.refresh_status()

    def off_click(self):
        if not self.guard_admin():
            return
        try:
            stop_acceleration()
            self.log("已停止加速：加速条目已移除、被停用的屏蔽条目已恢复、DNS 已刷新。")
        except Exception as e:
            self.log("停止失败: %s" % e)
        self.refresh_status()

    def test_click(self):
        def run():
            for host in CANDIDATES:
                ip, ms = pick_fastest(host)
                self.log("%-40s %s %s" % (host, ip or "无可用", ("%dms" % ms) if ms else ""))
        threading.Thread(target=run, daemon=True).start()


def selftest():
    log("=== selftest v%s ===" % VERSION)
    ok = sum(1 for h in CANDIDATES if pick_fastest(h)[0])
    for host in CANDIDATES:
        ip, ms = pick_fastest(host)
        log("%-6s %-42s %s %s" % ("OK" if ip else "FAIL", host, ip or "", ("%dms" % ms) if ms else ""))
    log("=== %d/%d 可用 ===" % (ok, len(CANDIDATES)))
    return 0 if ok else 1


def dryrun():
    """模拟写入（不修改 hosts），结果存到 %TEMP%\\hosts.dryrun"""
    mapping = {h: CANDIDATES[h][0] for h in CANDIDATES}
    text = build_hosts_text(mapping)
    p = os.path.join(os.environ.get("TEMP", "."), "hosts.dryrun")
    open(p, "w", encoding="utf-8").write(text)
    log("dryrun 输出 -> %s" % p)
    log("冲突条目停用数: %d" % text.count(CONFLICT_MARK))
    try:
        sys.stdout.buffer.write(text.encode("utf-8", "ignore"))
    except Exception:
        pass
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--dryrun" in sys.argv:
        sys.exit(dryrun())
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
