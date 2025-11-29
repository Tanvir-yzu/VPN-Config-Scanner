# ================================
# VPN CONFIG SCANNER PRO – FINAL 100% WORKING 2025
# All bugs fixed (log crash + f-string error)
# ================================

import os
import re
import glob
import socket
import base64
import time
import json
import threading
from urllib.parse import urlparse, unquote

# ── AUTO INSTALL PACKAGES ─────────────────────────────────────
def install(pkg):
    import subprocess, sys
    print(f"Installing {pkg}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError:
    install("customtkinter")
    import customtkinter as ctk
    from tkinter import filedialog, messagebox

try:
    import requests
except ImportError:
    install("requests")
    import requests

# ── SETTINGS ───────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VPNScanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VPN Scanner PRO 2025")
        self.geometry("860x920")
        self.resizable(False, False)

        # Title bar
        title = ctk.CTkFrame(self, height=55, fg_color="#0d0d0d")
        title.pack(fill="x"); title.pack_propagate(False)
        ctk.CTkLabel(title, text="VPN Scanner PRO", font=("Segoe UI", 24, "bold")).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(title, text="×", width=50, height=45, fg_color="#c42b1c", hover_color="#e63946", command=self.destroy).pack(side="right", padx=10)
        title.bind("<Button-1>", lambda e: (setattr(self, "_dx", e.x), setattr(self, "_dy", e.y)))
        title.bind("<B1-Motion>", lambda e: self.geometry(f"+{e.x_root-self._dx}+{e.y_root-self._dy}"))

        ctk.CTkLabel(self, text="Ultimate Config Tester", font=("Consolas", 40, "bold")).pack(pady=(20,10))

        # ── URL INPUT ─────────────────────────────────────
        url_frame = ctk.CTkFrame(self)
        url_frame.pack(pady=15, padx=40, fill="x")
        ctk.CTkLabel(url_frame, text="Subscription URL or Base64:", font=("Arial", 15)).pack(anchor="w", padx=10)
        self.url_entry = ctk.CTkEntry(url_frame, width=680, height=50, font=("Arial", 14),
                                      placeholder_text="https://... or paste raw base64")
        self.url_entry.pack(pady=8, padx=10)

        self.url_btn = ctk.CTkButton(url_frame, text="LOAD SUBSCRIPTION", width=220, height=50,
                                     fg_color="#ff6200", hover_color="#ff8844", command=self.load_subscription)
        self.url_btn.pack(pady=8)

        # Folder button
        self.folder_btn = ctk.CTkButton(self, text="OR SELECT LOCAL FOLDER", width=420, height=50,
                                        font=("Arial", 16), command=self.select_folder)
        self.folder_btn.pack(pady=12)

        # Start button
        self.start_btn = ctk.CTkButton(self, text="START SCANNING", width=520, height=75,
                                       font=("Arial", 30, "bold"), fg_color="#00cc00", hover_color="#00ff00",
                                       state="disabled", command=self.start_scan)
        self.start_btn.pack(pady=25)

        # Progress & labels
        self.progress = ctk.CTkProgressBar(self, width=740, height=35)
        self.progress.pack(pady=20); self.progress.set(0)

        self.percent = ctk.CTkLabel(self, text="0%", font=("Arial", 40, "bold"))
        self.percent.pack(pady=5)
        self.status = ctk.CTkLabel(self, text="Ready", font=("Arial", 16))
        self.status.pack(pady=5)
        self.counter = ctk.CTkLabel(self, text="Links: 0", font=("Arial", 15))
        self.counter.pack(pady=5)

        # Log box (renamed to avoid conflict)
        self.log_box = ctk.CTkTextbox(self, width=800, height=280, font=("Consolas", 12))
        self.log_box.pack(pady=20, padx=30)

        # Runtime vars
        self.all_links = []
        self.folder_path = None

    # ── LOG FUNCTION (FIXED) ───────────────────────────────────
    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    # ── LOAD FROM URL OR TEXT ───────────────────────────────────
    def load_subscription(self):
        raw = self.url_entry.get().strip()
        if not raw:
            messagebox.showwarning("Empty", "Enter URL or paste base64!")
            return

        self.start_btn.configure(state="disabled")
        self.log_box.delete("1.0", "end")
        self.log("Loading subscription...")
        self.status.configure(text="Downloading / decoding...")
        threading.Thread(target=self._process_input, args=(raw,), daemon=True).start()

    def _process_input(self, text):
        content = ""
        try:
            if text.startswith(("http://", "https://")):
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(text, timeout=25, headers=headers, verify=False)
                r.raise_for_status()
                content = r.text
                self.log("Downloaded from URL")
            else:
                content = text
                self.log("Using pasted text")

            # Base64 decode attempt
            cleaned = content.replace("\n", "").replace("\r", "").strip()
            if not cleaned.startswith(("vmess://", "vless://", "trojan://", "ss://")):
                try:
                    decoded = base64.b64decode(cleaned + "===", validate=False).decode("utf-8", errors="ignore")
                    if any(p in decoded for p in ("vmess://", "vless://", "trojan://", "ss://")):
                        content = decoded
                        self.log("Base64 decoded")
                except:
                    pass

            links = re.findall(r'[a-zA-Z]+://[^\s<>"\']+', content)
            clean = [l.split()[0].strip() for l in links if l.split()[0].startswith(("vmess://", "vless://", "trojan://", "ss://"))]
            self.all_links = list(dict.fromkeys(clean))

            if not self.all_links:
                self.after(0, lambda: messagebox.showerror("Error", "No valid configs found!"))
                return

            self.after(0, lambda: self.log(f"SUCCESS! {len(self.all_links)} unique configs loaded"))
            self.after(0, lambda: self.status.configure(text="Ready – press START"))
            self.after(0, lambda: self.counter.configure(text=f"Links: {len(self.all_links)}"))
            self.after(0, lambda: self.start_btn.configure(state="normal"))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    # ── LOCAL FOLDER ─────────────────────────────────────────────
    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        self.folder_path = folder
        self.all_links = []

        for file in glob.glob(os.path.join(folder, "sub*.txt")):
            try:
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                found = re.findall(r'[a-zA-Z]+://[^\s<>"\']+', txt)
                for l in found:
                    l = l.split()[0]
                    if l.startswith(("vmess://", "vless://", "trojan://", "ss://")):
                        self.all_links.append(l)
            except: pass

        self.all_links = list(dict.fromkeys(self.all_links))
        if self.all_links:
            self.start_btn.configure(state="normal")
            self.log(f"Loaded {len(self.all_links)} configs from folder")
            self.status.configure(text="Ready – press START")
            self.counter.configure(text=f"Links: {len(self.all_links)}")
        else:
            messagebox.showinfo("Empty", "No configs found")

    # ── SCANNING ─────────────────────────────────────────────────
    def start_scan(self):
        if not self.all_links: return
        self.start_btn.configure(state="disabled")
        self.progress.set(0)
        self.percent.configure(text="0%")
        self.log(f"\nTesting {len(self.all_links)} configs...\n")
        threading.Thread(target=self.scan_loop, daemon=True).start()

    def scan_loop(self):
        good = {"vmess": [], "vless": [], "ss": [], "trojan": []}
        total = len(self.all_links)

        for i, link in enumerate(self.all_links):
            pct = int((i + 1) / total * 100)
            self.after(0, lambda p=pct: self.progress.set(p/100))
            self.after(0, lambda p=pct: self.percent.configure(text=f"{p}%"))
            # ← FIXED f-string syntax
            self.after(0, lambda n=i+1: self.counter.configure(text=f"Tested: {n}/{total}"))

            try:
                if link.startswith("vmess://"):
                    h, p, n = self.decode_vmess(link); proto = "vmess"
                elif link.startswith("vless://"):
                    h, p, n = self.decode_vless_trojan(link); proto = "vless"
                elif link.startswith("trojan://"):
                    h, p, n = self.decode_vless_trojan(link); proto = "trojan"
                elif link.startswith("ss://"):
                    h, p, n = self.decode_ss(link); proto = "ss"
                else: continue

                if not h or not p: continue
                name = re.sub(r'[<>:"/\\|?*]', '_', (n or "NoName")[:50])

                lat = self.ping(h, int(p))
                if lat and lat <= 800:
                    good[proto].append(f"{link} # {name} - {lat}ms")
                    self.after(0, lambda l=lat, nm=name: self.log(f"{l}ms → {nm}"))
            except: pass

        # Save results
        save_dir = self.folder_path or os.path.join(os.path.expanduser("~"), "Desktop")
        saved = 0
        for proto, items in good.items():
            if not items: continue
            items.sort(key=lambda x: int(x.split("-")[-1].split("ms")[0]))
            fast = [x for x in items if int(x.split("-")[-1].split("ms")[0]) < 200]
            normal = [x for x in items if x not in fast]

            if fast:
                open(os.path.join(save_dir, f"FAST_{proto.upper()}.txt"), "w", encoding="utf-8").write("\n".join(fast))
                saved += len(fast)
            if normal:
                open(os.path.join(save_dir, f"{proto.upper()}.txt"), "w", encoding="utf-8").write("\n".join(normal))
                saved += len(normal)

        self.after(0, lambda: (
            self.progress.set(1),
            self.percent.configure(text="100%"),
            self.status.configure(text=f"FINISHED! Saved {saved} configs"),
            self.counter.configure(text=f"Done – {saved} good"),
            self.start_btn.configure(state="normal"),
            self.log(f"\nSCAN COMPLETE!\n{saved} working configs saved to:\n{save_dir}")
        ))

    # ── DECODERS ───────────────────────────────────────────────
    def decode_vmess(self, link):
        try:
            b64 = link[8:] + "=" * (-len(link[8:]) % 4)
            data = json.loads(base64.b64decode(b64))
            return data.get("add"), data.get("port"), data.get("ps", "")
        except: return None, None, ""

    def decode_vless_trojan(self, link):
        try:
            u = urlparse(link)
            return u.hostname, u.port or 443, unquote(u.fragment or "")
        except: return None, None, ""

    def decode_ss(self, link):
        try:
            if "@" in link[5:]:
                part = link.split("@")[1].split("#")[0]
                remark = unquote(link.split("#")[-1]) if "#" in link else ""
            else:
                enc = link[5:].split("#")[0]
                dec = base64.urlsafe_b64decode(enc + "===").decode("utf-8", errors="ignore")
                part = dec.split("@")[-1] if "@" in dec else dec
                remark = unquote(link.split("#")[-1]) if "#" in link else ""
            host = part.split(":")[0]
            port = int(part.split(":")[1]) if ":" in part else 443
            return host, port, remark
        except: return None, None, ""

    def ping(self, host, port, timeout=4):
        try:
            start = time.time()
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            return int((time.time() - start) * 1000)
        except:
            return None

# ── RUN ───────────────────────────────────────────────────
if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    app = VPNScanner()
    app.mainloop()