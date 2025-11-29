# ================================
# VPN CONFIG SCANNER PRO – STREAMLIT VERSION 2025
# Web-based, super fast, saves to Downloads folder
# Run with: streamlit run scanner.py
# ================================

import streamlit as st
import requests
import base64
import re
import socket
import time
import os
import threading
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIG ─────────────────────────────────────
st.set_page_config(page_title="VPN Scanner PRO", page_icon="rocket", layout="centered")
st.title("VPN Config Scanner PRO 2025")
st.markdown("### Fastest & Most Beautiful VPN Tester — 100% Working")

# Auto-detect Downloads folder
downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
if not os.path.exists(downloads_dir):
    downloads_dir = os.path.expanduser("~/Desktop")

# Session state
if "links" not in st.session_state:
    st.session_state.links = []
if "scanning" not in st.session_state:
    st.session_state.scanning = False

# ── SIDEBAR ───────────────────────────────────
with st.sidebar:
    st.header("Input")
    option = st.radio("Choose source:", ["Subscription URL", "Paste Base64/Text", "Upload sub*.txt files"])

    if option == "Subscription URL":
        url = st.text_input("Enter subscription URL:", placeholder="https://example.com/sub")
        if st.button("Load from URL") and url:
            with st.spinner("Downloading..."):
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    r = requests.get(url, timeout=20, headers=headers, verify=False)
                    r.raise_for_status()
                    content = r.text
                    st.success("Downloaded!")
                except:
                    st.error("Failed to download URL")
                    content = ""
    elif option == "Paste Base64/Text":
        content = st.text_area("Paste base64 or raw links here:", height=200)
    else:
        uploaded_files = st.file_uploader("Upload sub*.txt files", accept_multiple_files=True)
        content = ""
        if uploaded_files:
            for f in uploaded_files:
                content += f.read().decode("utf-8", errors="ignore") + "\n"

# ── EXTRACT LINKS ─────────────────────────────
def extract_links(text):
    if not text:
        return []
    # Try base64 decode first
    cleaned = text.strip().replace("\n", "")
    if not cleaned.startswith(("vmess://", "vless://", "trojan://", "ss://")):
        try:
            decoded = base64.b64decode(cleaned + "===", validate=False).decode("utf-8", errors="ignore")
            if any(x in decoded for x in ("vmess://", "vless://", "trojan://", "ss://")):
                text = decoded
        except:
            pass
    
    links = re.findall(r'[a-zA-Z]+://[^\s<>"\']+', text)
    clean = [l.split()[0].strip() for l in links if l.split()[0].startswith(("vmess://", "vless://", "trojan://", "ss://"))]
    return list(dict.fromkeys(clean))

if "content" not in locals():
    content = ""

if content:
    st.session_state.links = extract_links(content)
    st.success(f"Found {len(st.session_state.links)} unique configs!")

# ── DECODERS ──────────────────────────────────
def decode_vmess(link):
    try:
        b64 = link[8:] + "=" * (-len(link[8:]) % 4)
        data = base64.b64decode(b64).decode()
        import json
        j = json.loads(data)
        return j.get("add"), j.get("port"), j.get("ps", "NoName")
    except: return None, None, ""

def decode_vless_trojan(link):
    try:
        u = urlparse(link)
        return u.hostname, u.port or 443, unquote(u.fragment or "").split("/")[-1]
    except: return None, None, ""

def decode_ss(link):
    try:
        if "@" in link[5:]:
            part = link.split("@")[1].split("#")[0]
        else:
            enc = link[5:].split("#")[0]
            dec = base64.urlsafe_b64decode(enc + "===").decode("utf-8", errors="ignore")
            part = dec.split("@")[-1]
        host, port = part.split(":")[0], int(part.split(":")[1])
        remark = unquote(link.split("#")[-1]) if "#" in link else "SS"
        return host, port, remark
    except: return None, None, ""

def ping(host, port, timeout=4):
    try:
        start = time.time()
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return int((time.time() - start) * 1000)
    except:
        return None

# ── SCAN FUNCTION ─────────────────────────────
def test_link(link):
    try:
        if link.startswith("vmess://"):
            h, p, n = decode_vmess(link); proto = "vmess"
        elif link.startswith("vless://"):
            h, p, n = decode_vless_trojan(link); proto = "vless"
        elif link.startswith("trojan://"):
            h, p, n = decode_vless_trojan(link); proto = "trojan"
        elif link.startswith("ss://"):
            h, p, n = decode_ss(link); proto = "ss"
        else:
            return None

        if not h or not p: return None
        name = re.sub(r'[<>:"/\\|?*]', '_', (n or "NoName")[:40])
        lat = ping(h, int(p))
        if lat and lat <= 800:
            return {"link": link, "name": name, "latency": lat, "proto": proto}
    except:
        pass
    return None

# ── START SCANNING ────────────────────────────
if st.session_state.links and st.button("START SCANNING", type="primary", use_container_width=True):
    if st.session_state.scanning:
        st.warning("Already scanning!")
    else:
        st.session_state.scanning = True
        progress = st.progress(0)
        status = st.empty()
        log = st.empty()
        results = {"vmess": [], "vless": [], "ss": [], "trojan": []}

        status.info("Scanning configs...")

        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(test_link, link): link for link in st.session_state.links}
            done = 0
            for future in as_completed(futures):
                done += 1
                progress.progress(done / len(st.session_state.links))
                result = future.result()
                if result:
                    results[result["proto"]].append(f"{result['link']} # {result['name']} - {result['latency']}ms")
                    log.success(f"{result['latency']}ms → {result['name']}")

        # Save to Downloads
        saved = 0
        for proto, items in results.items():
            if not items: continue
            items.sort(key=lambda x: int(x.split("-")[-1].split("ms")[0]))
            fast = [x for x in items if int(x.split("-")[-1].split("ms")[0]) < 200]
            normal = [x for x in items if x not in fast]

            if fast:
                path = os.path.join(downloads_dir, f"FAST_{proto.upper()}.txt")
                open(path, "w", encoding="utf-8").write("\n".join(fast))
                saved += len(fast)
            if normal:
                path = os.path.join(downloads_dir, f"{proto.upper()}.txt")
                open(path, "w", encoding="utf-8").write("\n".join(normal))
                saved += len(normal)

        st.session_state.scanning = False
        st.success(f"FINISHED! Saved {saved} configs to Downloads folder!")
        st.balloons()

else:
    if st.session_state.links:
        st.info(f"Ready to scan {len(st.session_state.links)} configs!")
    else:
        st.info("Enter a URL, paste text, or upload files to begin")

st.caption(f"Results saved to: {downloads_dir}")