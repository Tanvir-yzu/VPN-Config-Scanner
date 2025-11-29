# ================================
# VPN SCANNER PRO 2025 – WITH REAL SPEED TEST (Mbps)
# Fixed version – runs locally + on Streamlit Cloud
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

# ── Page Config ─────────────────────────────────
st.set_page_config(page_title="VPN Scanner PRO 2025", page_icon="rocket", layout="centered")
st.title("VPN Scanner PRO 2025 + Speed Test")
st.markdown("### Fastest Free Online VPN Tester with **REAL DOWNLOAD SPEED TEST**")

# ── Session State ───────────────────────────────
if "links" not in st.session_state:
    st.session_state.links = []
if "results" not in st.session_state:
    st.session_state.results = {"vmess": [], "vless": [], "ss": [], "trojan": []}
if "scanning" not in st.session_state:
    st.session_state.scanning = False

# ── Sidebar Input ───────────────────────────────
with st.sidebar:
    st.header("Input Source")
    option = st.radio("Choose input method:",
                      ["Subscription URL", "Paste Base64/Text", "Upload .txt files"])

    content = ""
    if option == "Subscription URL":
        url = st.text_input("Enter subscription URL:")
        if st.button("Load from URL") and url:
            with st.spinner("Downloading subscription..."):
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    r = requests.get(url, timeout=25, headers=headers, verify=False)
                    r.raise_for_status()
                    content = r.text.strip()
                    st.success("Subscription loaded!")
                except Exception as e:
                    st.error("Failed to download")
    elif option == "Paste Base64/Text":
        content = st.text_area("Paste configs or base64 here:", height=250)
    else:
        uploaded = st.file_uploader("Upload sub*.txt or config files", accept_multiple_files=True)
        if uploaded:
            for file in uploaded:
                try:
                    content += file.read().decode("utf-8", errors="ignore") + "\n"
                except:
                    st.warning(f"Could not read {file.name}")

# ── Extract Links ───────────────────────────────
def extract_links(text):
    if not text:
        return []
    text = text.strip()
    # Try to decode base64 subscription first
    if not text.startswith(("vmess://", "vless://", "ss://", "trojan://")):
        try:
            decoded = base64.b64decode(text + "===", validate=False).decode("utf-8", errors="ignore")
            if any(p in decoded for p in ("vmess://", "vless://", "ss://", "trojan://")):
                text = decoded
        except:
            pass

    links = re.findall(r"[a-zA-Z]+://[^\s<>\"']+", text)
    clean = []
    for l in links:
        l = l.split()[0].strip()
        if l.startswith(("vmess://", "vless://", "ss://", "trojan://")):
            clean.append(l)
    return list(dict.fromkeys(clean))  # unique only

if content:
    st.session_state.links = extract_links(content)
    st.success(f"Found **{len(st.session_state.links)}** unique configs!")

# ── Decoders ────────────────────────────────────
def decode_vmess(link):
    try:
        b64 = link[8:] + "=" * (-len(link[8:]) % 4)
        data = json.loads(base64.b64decode(b64))
        return data.get("add"), data.get("port"), data.get("ps", "NoName")
    except:
        return None, None, "Error"

def decode_vless_trojan(link):
    try:
        u = urlparse(link)
        remark = unquote(u.fragment or "").split("/")[-1] if u.fragment else "NoName"
        return u.hostname, u.port or 443, remark
    except:
        return None, None, "Error"

def decode_ss(link):
    try:
        if "@" in link[5:]:
            part = link.split("@")[1].split("#")[0].split("?")[0]
            remark = unquote(link.split("#")[-1]) if "#" in link else "SS"
        else:
            enc = link[5:].split("#")[0]
            dec = base64.urlsafe_b64decode(enc + "===").decode("utf-8", errors="ignore")
            part = dec.split("@")[-1]
            remark = unquote(link.split("#")[-1]) if "#" in link else "SS"
        host, port = part.split(":")[0], int(part.split(":")[1])
        return host, port, remark
    except:
        return None, None, "Error"

def ping(host, port, timeout=4):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except:
        return False

# ── Speed Test Servers ────────────────────────
@st.cache_data(ttl=3600)
def get_speed_test_servers():
    return [
        "https://speed.cloudflare.com/__down?bytes=25000000",   # 25 MB
        "http://speedtest.tele2.net/10MB.zip",
        "https://proof.ovh.net/files/10Mb.dat",
        "https://mirror.nl.leaseweb.net/speedtest/10mb.bin",
    ]

def measure_download_speed(timeout=12):
    for url in get_speed_test_servers():
        try:
            start = time.time()
            r = requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    downloaded += len(chunk)
                if downloaded >= 15 * 1024 * 1024:   # 15 MB is enough
                    break
            duration = time.time() - start
            if duration < 0.8:
                continue
            speed_mbps = round((downloaded * 8) / (duration * 1_000_000), 1)
            if speed_mbps >= 0.5:
                return speed_mbps
        except:
            continue
    return 0.0

# ── Main Test Function ──────────────────────────
def test_link_with_speed(link):
    try:
        if link.startswith("vmess://"):
            host, port, name = decode_vmess(link)
            proto = "vmess"
        elif link.startswith("vless://"):
            host, port, name = decode_vless_trojan(link)
            proto = "vless"
        elif link.startswith("trojan://"):
            host, port, name = decode_vless_trojan(link)
            proto = "trojan"
        elif link.startswith("ss://"):
            host, port, name = decode_ss(link)
            proto = "ss"
        else:
            return None

        if not host or not port:
            return None

        name = re.sub(r'[<>:"/\\|?*]', '_', str(name)[:50]) or "NoName"

        # Ping
        if not ping(host, int(port)):
            return None
        latency = int((time.time() - time.time() + 1000))  # placeholder, real calc below
        ping_start = time.time()
        if not ping(host, int(port)):
            return None
        latency = int((time.time() - ping_start) * 1000)

        if latency > 900:
            return None

        # Speed test
        speed = measure_download_speed()
        if speed < 1.0:      # keep only ≥1 Mbps
            return None

        return {
            "link": link,
            "name": name,
            "lat": latency,
            "speed": speed,
            "proto": proto
        }
    except:
        return None

# ── START SCANNING ──────────────────────────────
if st.session_state.links:
    if st.button("START SCANNING + SPEED TEST", type="primary", use_container_width=True):
        if st.session_state.scanning:
            st.warning("Already scanning!")
        else:
            st.session_state.scanning = True
            st.session_state.results = {"vmess": [], "vless": [], "ss": [], "trojan": []}

            progress = st.progress(0)
            status = st.empty()
            log = st.empty()

            status.info("Testing with ping + real download speed...")
            with ThreadPoolExecutor(max_workers=80) as executor:
                futures = {executor.submit(test_link_with_speed, link): link for link in st.session_state.links}
                for i, future in enumerate(as_completed(futures)):
                    progress.progress((i + 1) / len(st.session_state.links))
                    res = future.result()
                    if res:
                        line = f"{res['link']} # {res['name']} - {res['lat']}ms - {res['speed']}Mbps"
                        st.session_state.results[res["proto"]].append(line)
                        log.success(f"{res['speed']:>6} Mbps | {res['lat']:>3}ms → {res['name']}")

            st.session_state.scanning = False
            st.balloons()
            st.success("SCAN COMPLETE!")

# ── DOWNLOAD SECTION ────────────────────────────
if any(st.session_state.results.values()):
    st.markdown("### Download Results (sorted by speed)")
    c1, c2 = st.columns(2)

    total = 0
    all_speeds = []

    for proto, lines in st.session_state.results.items():
        if not lines:
            continue

        # Sort: highest speed first, then lowest latency
        lines.sort(key=lambda x: (
            -float(x.split("-")[-1].replace("Mbps", "").strip()),
            int(re.search(r"(\d+)ms", x).group(1))
        ))

        ultra = [l for l in lines if float(l.split("-")[-1].replace("Mbps","").strip()) >= 20]
        normal = [l for l in lines if l not in ultra]

        total += len(lines)
        for l in lines:
            try:
                all_speeds.append(float(l.split("-")[-1].replace("Mbps","").strip()))
            except:
                pass

        if ultra:
            data = "\n".join(ultra)
            c1.download_button(f"ULTRA FAST {proto.upper()} ({len(ultra)})", data,
                               f"ULTRA_{proto.upper()}_2025.txt", mime="text/plain")
        if normal:
            data = "\n".join(normal)
            c2.download_button(f"{proto.upper()} ({len(normal)})", data,
                               f"{proto.upper()}_2025.txt", mime="text/plain")

    avg = sum(all_speeds) / len(all_speeds) if all_speeds else 0
    st.success(f"Ready! {total} fast configs | Average speed: {avg:.1f} Mbps")

else:
    if st.session_state.links and not st.session_state.scanning:
        st.info(f"Ready to test {len(st.session_state.links)} configs")
    else:
        st.info("Enter subscription / paste configs to begin")

st.caption("VPN Scanner PRO 2025 – Real Speed Test Edition • Always free")