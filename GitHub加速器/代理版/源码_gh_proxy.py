# -*- coding: utf-8 -*-
"""
GitHub 加速器（本地 SNI 路由代理版）
机制（同 Steam++ / Watt Toolkit 的思路，但不做 TLS 中间人、不装证书）：
  1) hosts 把 GitHub 域名指向 127.0.0.1
  2) 本程序在 127.0.0.1:443 监听，从 TLS ClientHello 里读出 SNI 域名
  3) 为该域名即时挑选可用 IP（DoH 现查 + 内置池，失败自动换下一个）
  4) 原始 TCP 转发 —— 证书端到端，客户端看到的仍是 GitHub 真证书
"""
import json
import os
import socket
import struct
import sys
import threading
import time
import urllib.request

APP = "GitHub 加速器(代理版)"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if os.name == "nt" else "/etc/hosts"
MARK_START = "# >>> GitHub加速器(代理) START >>>"
MARK_END = "# <<< GitHub加速器(代理) END <<<"
LISTEN_HOST = os.environ.get("GHACC_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("GHACC_PORT", "443"))

DOMAINS = [
    "github.com", "api.github.com", "raw.githubusercontent.com",
    "objects.githubusercontent.com", "gist.githubusercontent.com",
    "codeload.github.com", "avatars.githubusercontent.com",
    "camo.githubusercontent.com", "media.githubusercontent.com",
    "user-images.githubusercontent.com", "private-user-images.githubusercontent.com",
    "github.githubassets.com", "collector.github.com",
    "central.github.com", "alive.github.com", "live.github.com",
]
DOMAIN_SET = set(DOMAINS)

# 内置候选池（DoH 查不到时兜底）
BASE_IPS = {
    "github.com": ["140.82.112.3", "140.82.113.3", "20.26.156.215", "20.205.243.166"],
    "api.github.com": ["20.205.243.168", "140.82.112.6"],
    "codeload.github.com": ["20.205.243.165", "140.82.112.9", "140.82.114.9"],
    "raw.githubusercontent.com": ["185.199.111.133", "185.199.108.133", "185.199.109.133", "185.199.110.133"],
    "objects.githubusercontent.com": ["185.199.111.133", "185.199.108.133"],
    "gist.githubusercontent.com": ["185.199.111.133", "185.199.108.133"],
    "avatars.githubusercontent.com": ["185.199.111.133", "185.199.108.133"],
    "camo.githubusercontent.com": ["185.199.111.133", "185.199.108.133"],
    "media.githubusercontent.com": ["185.199.111.133", "185.199.108.133"],
    "user-images.githubusercontent.com": ["185.199.111.133", "185.199.108.133"],
    "private-user-images.githubusercontent.com": ["185.199.111.133"],
    "github.githubassets.com": ["185.199.111.154", "185.199.108.154"],
}

LOG = None


def log(msg):
    line = time.strftime("[%H:%M:%S] ") + msg
    print(line, flush=True)
    if LOG:
        try:
            LOG.write(line + "\n"); LOG.flush()
        except Exception:
            pass


def doh_a(host, timeout=4.0):
    """阿里 DoH 查 A 记录（本网络可达）"""
    url = "https://dns.alidns.com/resolve?name=%s&type=A" % host
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "gh-acc/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        return [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
    except Exception:
        return []


class Pool:
    """每个域名的 IP 池：DoH 现查 + 兜底；后台握手预检，已验证 IP 优先"""
    def __init__(self, host):
        self.host = host
        self.bad = {}          # ip -> 解禁时间
        self.cached = []
        self.cached_at = 0
        self.verified = []     # 最近握手通过的 IP

    def refresh(self):
        ips = doh_a(self.host)
        if ips:
            self.cached = ips
        self.cached_at = time.time()

    def all_ips(self):
        if time.time() - self.cached_at > 120:
            self.refresh()
        seen, out = set(), []
        for ip in self.verified + list(self.cached) + BASE_IPS.get(self.host, []):
            if ip not in seen and self.bad.get(ip, 0) < time.time():
                seen.add(ip); out.append(ip)
        return out

    def candidates(self):
        return self.all_ips()

    def mark_bad(self, ip, secs=120):
        self.bad[ip] = time.time() + secs

    def verify(self):
        """TLS 握手预检（带 SNI），通过者进入 verified（优先后续连接）"""
        good = []
        for ip in self.all_ips():
            if tls_ok(self.host, ip):
                good.append(ip)
        if good:
            self.verified = good
        return good


def tls_ok(host, ip, timeout=3.0):
    """对 (ip,443) 做一次 TLS 握手，判断是否真可用"""
    import ssl as _ssl
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    try:
        with socket.create_connection((ip, 443), timeout=timeout) as s:
            with ctx.wrap_socket(s, server_hostname=host):
                return True
    except Exception:
        return False


POOLS = {h: Pool(h) for h in DOMAINS}


def verify_all():
    """后台巡检：定期检查各域名 IP 可用性"""
    while True:
        try:
            for h, pool in POOLS.items():
                good = pool.verify()
                if good:
                    log("巡检 %-38s 可用: %s" % (h, ",".join(good[:3])))
        except Exception:
            pass
        time.sleep(90)


def parse_sni(data):
    """从 TLS ClientHello 里取 SNI（只读明文头部，不涉解密）"""
    try:
        if len(data) < 5 or data[0] != 0x16:
            return None
        rec_len = struct.unpack("!H", data[3:5])[0]
        p = 5
        if p + 4 > len(data) or data[p] != 0x01:
            return None
        hs_len = (data[p+1] << 16) | (data[p+2] << 8) | data[p+3]
        p += 4 + 2 + 32                     # 跳过 handshake 头 + version + random
        sid_len = data[p]; p += 1 + sid_len
        cs_len = struct.unpack("!H", data[p:p+2])[0]; p += 2 + cs_len
        cm_len = data[p]; p += 1 + cm_len
        ext_total = struct.unpack("!H", data[p:p+2])[0]; p += 2
        end = min(p + ext_total, len(data))
        while p + 4 <= end:
            etype = struct.unpack("!H", data[p:p+2])[0]
            elen = struct.unpack("!H", data[p+2:p+4])[0]
            p += 4
            if etype == 0x00:               # server_name
                q = p + 2
                ntype = data[q]; nlen = struct.unpack("!H", data[q+1:q+3])[0]
                if ntype == 0:
                    return data[q+3:q+3+nlen].decode("ascii", "ignore").lower()
            p += elen
    except Exception:
        return None
    return None


def pipe(a, b):
    try:
        while True:
            data = a.recv(65536)
            if not data:
                break
            b.sendall(data)
    except Exception:
        pass
    finally:
        try:
            b.shutdown(socket.SHUT_WR)
        except Exception:
            pass


def handle(conn, addr):
    conn.settimeout(10)
    try:
        head = conn.recv(4096)
    except Exception:
        conn.close(); return
    if not head:
        conn.close(); return
    sni = parse_sni(head)
    if not sni or sni not in DOMAIN_SET:
        log("跳过非目标域名: %s" % (sni or "?"))
        conn.close(); return
    upstream = None
    tried = []
    for ip in POOLS[sni].candidates():
        try:
            upstream = socket.create_connection((ip, 443), timeout=4)
            upstream.settimeout(6)
            log("%-40s -> %s" % (sni, ip))
            break
        except Exception:
            POOLS[sni].mark_bad(ip)
            tried.append(ip)
    if not upstream:
        log("× %s 无可用 IP（试过 %s）" % (sni, ",".join(tried[:4])))
        conn.close(); return
    try:
        upstream.sendall(head)
    except Exception:
        POOLS[sni].mark_bad(upstream.getpeername()[0])
        conn.close(); upstream.close(); return
    conn.settimeout(None)
    threading.Thread(target=pipe, args=(conn, upstream), daemon=True).start()
    pipe(upstream, conn)
    try:
        conn.close(); upstream.close()
    except Exception:
        pass


def serve():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((LISTEN_HOST, LISTEN_PORT))
    srv.listen(200)
    log("%s 已启动: %s:%d（接管 %d 个域名）" % (APP, LISTEN_HOST, LISTEN_PORT, len(DOMAINS)))
    threading.Thread(target=verify_all, daemon=True).start()
    while True:
        try:
            conn, addr = srv.accept()
        except KeyboardInterrupt:
            break
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


# ---------- hosts 管理 ----------
def read_hosts():
    with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_hosts(text):
    with open(HOSTS_PATH, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)


def install_hosts():
    text = read_hosts()
    lines, skip = [], False
    for ln in text.splitlines(keepends=True):
        if MARK_START in ln: skip = True; continue
        if MARK_END in ln: skip = False; continue
        if not skip: lines.append(ln)
    out = "".join(lines)
    if not out.endswith("\n"):
        out += "\n"
    out += "%s\n" % MARK_START
    for h in DOMAINS:
        out += "127.0.0.1 %s\n" % h
    out += "%s\n" % MARK_END
    write_hosts(out)
    try:
        import subprocess
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=20)
    except Exception:
        pass
    log("hosts 已接管 %d 个域名并刷新 DNS" % len(DOMAINS))


def restore_hosts():
    text = read_hosts()
    lines, skip = [], False
    for ln in text.splitlines(keepends=True):
        if MARK_START in ln: skip = True; continue
        if MARK_END in ln: skip = False; continue
        if not skip: lines.append(ln)
    write_hosts("".join(lines))
    try:
        import subprocess
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=20)
    except Exception:
        pass
    log("hosts 已还原并刷新 DNS")


def selftest():
    log("=== SNI 解析自检 ===")
    # 构造一个最小 ClientHello 测试解析
    name = b"github.com"
    ext = b"\x00\x00" + struct.pack("!H", len(name) + 5) + struct.pack("!H", len(name) + 3) + b"\x00" + struct.pack("!H", len(name)) + name
    body = b"\x03\x03" + b"\x00" * 32 + b"\x00" + struct.pack("!H", 2) + b"\x13\x01" + b"\x01\x00" + struct.pack("!H", len(ext)) + ext
    hs = b"\x01" + struct.pack("!I", len(body))[1:] + body
    rec = b"\x16\x03\x01" + struct.pack("!H", len(hs)) + hs
    got = parse_sni(rec)
    log("SNI 解析: 期望 github.com / 实际 %s -> %s" % (got, "OK" if got == "github.com" else "FAIL"))
    for h in DOMAINS[:6]:
        ips = POOLS[h].candidates()
        log("%-40s 候选 %s" % (h, ",".join(ips[:4])))
    return 0 if got == "github.com" else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--install-hosts" in sys.argv:
        install_hosts(); sys.exit(0)
    if "--restore-hosts" in sys.argv:
        restore_hosts(); sys.exit(0)
    serve()
