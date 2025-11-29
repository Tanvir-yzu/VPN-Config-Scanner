# ================================
# VPN CONFIG SCANNER PRO – STREAMLIT CLOUD VERSION 2025
# No file writing → gives DOWNLOAD BUTTONS instead
# Works 100% on streamlit.io
# ================================

import streamlit as st
import requests
import base64
import re
import socket
import time
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

st.set_page_config(page_title="VPN Scanner PRO", page_icon="rocket", layout="centered")
st.title("VPN Scanner PRO 2025")
st.markdown("### Fastest Free Online VPN Tester — 100% Working")

# Session state
if "links" not in st.session_state:
    st.session_state.links = []
if "results" not in st.session_state:
    st.session_state.results = {"vmess": [], "vless": [], "ss": [], "trojan": []}
if "scanning" not in st.session_state:
    st.session_state.scanning = False

# ── INPUT ─────────────────────────────────────
with st.sidebar:
    st.header("Input Source")
    option = st.radio("Choose:", ["Subscription URL", "Paste Base64/Text", "Upload sub*.txt"])

    content = ""
    if option == "Subscription URL":
        url = st.text_input("Enter URL:")
        if st.button("Load URL") and url:
            with st.spinner("Downloading..."):
                try:
                    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
                    r.raise_for_status()
                    content = r.text
                    st.success("Loaded!")
                except:
                    st.error("Failed to download")
    elif option == "Paste Base64/Text":
        content = st.text_area("Paste here:", height=200)
    else:
        uploaded = st.file_uploader("Upload sub*.txt files", accept_multiple_files=True)
        if uploaded:
            for f in uploaded:
                content += f.read().decode("utf-8", errors="ignore") + "\n"

# ── EXTRACT LINKS ─────────────────────────────
def extract_links(text):
    if not text: return []
    cleaned = text.strip().replace("\n", "").replace("\r", "")
    if not cleaned.startswith(("vmess://", "vless://", "trojan://", "ss://")):
        try:
            decoded = base64.b64decode(cleaned + "===", validate=False).decode("utf-8", errors="ignore")
            if any(x in decoded for x in ("vmess://", "vless://", "trojan://", "ss://")):
                text = decoded
        except: pass
    links = re.findall(r'[a-zA-Z]+://[^\s<>"\']+', text)
    clean = [l.split()[0].strip() for l in links if l.split()[0].startswith(("vmess://", "vless://", "trojan://", "ss://"))]
    return list(dict.fromkeys(clean))

if content:
    st.session_state.links = extract_links(content)
    st.success(f"Found {len(st.session_state.links)} unique configs!")

# ── DECODERS & PING ───────────────────────────
def decode_vmess(link):
    try:
        b64 = link[8:] + "=" * (-len(link[8:]) % 4)
        data = json.loads(base64.b64decode(b64))
        return data.get("add"), data.get("port"), data.get("ps", "NoName")
    except: return None, None, ""

def decode_vless_trojan(link):
    try:
        u = urlparse(link)
        remark = unquote(u.fragment or "").split("/")[-1] if u.fragment else "NoName"
        return u.hostname, u.port or 443, remark
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

def ping(host, port):
    try:
        s = socket.create_connection((host, port), timeout=4)
        s.close()
        return True
    except:
        return False

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
        else: return None
        if not h or not p: return None
        name = re.sub(r'[<>:"/\\|?*]', '_', n[:40])
        start = time.time()
        if ping(h, int(p)):
            lat = int((time.time() - start) * 1000)
            if lat <= 800:
                return {"link": link, "name": name, "lat": lat, "proto": proto}
    except: pass
    return None

# ── SCANNING ──────────────────────────────────
if st.session_state.links and st.button("START SCANNING", type="primary", use_container_width=True):
    if st.session_state.scanning:
        st.warning("Already scanning!")
    else:
        st.session_state.scanning = True
        st.session_state.results = {"vmess": [], "vless": [], "ss": [], "trojan": []}
        progress = st.progress(0)
        status = st.empty()
        log_placeholder = st.empty()

        status.info("Testing configs...")
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(test_link, link) for link in st.session_state.links]
            for i, future in enumerate(as_completed(futures)):
                progress.progress((i + 1) / len(futures))
                result = future.result()
                if result:
                    line = f"{result['link']} # {result['name']} - {result['lat']}ms"
                    st.session_state.results[result["proto"]].append(line)
                    log_placeholder.success(f"{result['lat']}ms → {result['name']}")

        st.session_state.scanning = False
        st.success("SCAN COMPLETE!")
        st.balloons()

# ── SHOW DOWNLOAD BUTTONS ─────────────────────
if any(st.session_state.results.values()):
    st.markdown("### Download Results")
    col1, col2 = st.columns(2)
    saved = 0
    for proto, items in st.session_state.results.items():
        if not items: continue
        items.sort(key=lambda x: int(x.split("-")[-1].split("ms")[0]))
        fast = [x for x in items if int(x.split("-")[-1].split("ms")[0]) < 200]
        normal = [x for x in items if x not in fast]
        saved += len(fast) + len(normal)

        if fast:
            txt = "\n".join(fast)
            if proto == "vmess":
                col1.download_button(f"FAST_{proto.upper()}.txt ({len(fast)})", txt, f"FAST_{proto.upper()}.txt")
            else:
                col2.download_button(f"FAST_{proto.upper()}.txt ({len(fast)})", txt, f"FAST_{proto.upper()}.txt")
        if normal:
            txt = "\n".join(normal)
            col1.download_button(f"{proto.upper()}.txt ({len(normal)})", txt, f"{proto.upper()}.txt")

    st.success(f"Ready! {saved} working configs — click to download")
else:
    if st.session_state.links:
        st.info(f"Ready to scan {len(st.session_state.links)} configs!")
    else:
        st.info("Enter a subscription URL or paste configs to start")

st.caption("Made with love — Works forever on Streamlit Cloud")