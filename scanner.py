# ================================
# VPN CONFIG SCANNER – FULLY WORKING 2025
# Works on Windows, macOS, Linux
# Shows real % progress + saves FAST configs
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

# Auto-install customtkinter if missing
try:
    import customtkinter as ctk
    from tkinter import filedialog
except ImportError:
    print("Installing customtkinter automatically...")
    os.system("pip install customtkinter --upgrade")
    import customtkinter as ctk
    from tkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VPNScanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VPN Config Scanner")
        self.geometry("780x800")
        self.resizable(False, False)

        # === Title Bar ===
        title_bar = ctk.CTkFrame(self, height=50, fg_color="#0d0d0d")
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(title_bar, text="VPN Config Scanner", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(title_bar, text="×", width=40, height=40, fg_color="#c42b1c", hover_color="#e63946", command=self.destroy).pack(side="right", padx=10)

        # Drag window
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.move_window)

        # === Logo ===
        ctk.CTkLabel(self, text="[EPOdONIOS]", font=ctk.CTkFont(size=40, weight="bold", slant="italic")).pack(pady=(20, 10))

        # === Select Folder Button ===
        self.folder_btn = ctk.CTkButton(self, text="Select Folder with sub*.txt files", width=400, height=50,
                                        font=ctk.CTkFont(size=16), command=self.select_folder)
        self.folder_btn.pack(pady=15)

        # === Start Button ===
        self.start_btn = ctk.CTkButton(self, text="START SCANNING", width=400, height=60,
                                       font=ctk.CTkFont(size=22, weight="bold"),
                                       fg_color="#00cc00", hover_color="#00ff00",
                                       state="disabled", command=self.start_scan)
        self.start_btn.pack(pady=10)

        # === Progress Bar ===
        self.progress_bar = ctk.CTkProgressBar(self, width=600, height=25)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        # === Labels ===
        self.status_label = ctk.CTkLabel(self, text="Select a folder to begin scanning", font=ctk.CTkFont(size=15))
        self.status_label.pack(pady=5)

        self.percent_label = ctk.CTkLabel(self, text="0%", font=ctk.CTkFont(size=24, weight="bold"))
        self.percent_label.pack(pady=5)

        self.counter_label = ctk.CTkLabel(self, text="Links checked: 0 / 0", font=ctk.CTkFont(size=14))
        self.counter_label.pack(pady=5)

        # === Log Box ===
        self.log_box = ctk.CTkTextbox(self, width=720, height=280, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.pack(pady=20, padx=30)

        # Variables
        self.folder_path = None
        self.total_links = 0
        self.checked = 0

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def move_window(self, event):
        x = event.x_root - self.x
        y = event.y_root - self.y
        self.geometry(f"+{x}+{y}")

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_btn.configure(text="Folder Selected!")
            self.start_btn.configure(state="normal")
            self.log(f"Selected folder:\n{folder}\n")
            self.status_label.configure(text="Ready to scan!")

    def start_scan(self):
        if not self.folder_path:
            return

        self.start_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.counter_label.configure(text="Collecting links...")
        self.log_box.delete("1.0", "end")
        self.log("Starting scan...\n")

        threading.Thread(target=self.scan_all, daemon=True).start()

    def scan_all(self):
        all_links = []

        # Collect all links
        for filepath in glob.glob(os.path.join(self.folder_path, "sub*.txt")):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    links = re.findall(r'(vmess://[^\s\n]+|vless://[^\s\n]+|trojan://[^\s\n]+|ss://[^\s\n]+)', content)
                    for link in links:
                        all_links.append(link.strip())
            except:
                pass

        self.total_links = len(all_links)
        if self.total_links == 0:
            self.after(0, lambda: self.log("No links found in sub*.txt files!"))
            self.after(0, lambda: self.start_btn.configure(state="normal"))
            return

        self.after(0, lambda: self.log(f"Found {self.total_links} links. Starting latency test...\n"))

        good_configs = {"vmess": [], "vless": [], "ss": [], "trojan": []}

        for i, link in enumerate(all_links):
            self.checked = i + 1
            percent = int((self.checked / self.total_links) * 100)

            self.after(0, lambda p=percent: self.progress_bar.set(p / 100))
            self.after(0, lambda p=percent: self.percent_label.configure(text=f"{p}%"))
            self.after(0, lambda: self.counter_label.configure(text=f"Checked: {self.checked}/{self.total_links}"))
            self.after(0, lambda: self.status_label.configure(text=f"Testing: {link[:70]}..."))

            try:
                if link.startswith("vmess://"):
                    host, port, name = self.decode_vmess(link)
                    proto = "vmess"
                elif link.startswith("vless://") or link.startswith("trojan://"):
                    host, port, name = self.decode_vless_trojan(link)
                    proto = "vless" if link.startswith("vless") else "trojan"
                elif link.startswith("ss://"):
                    host, port, name = self.decode_ss(link)
                    proto = "ss"
                else:
                    continue

                if not host or not port: continue
                name = re.sub(r'[<>:"/\\|?*]', '_', name or "NoName")[:40]

                latency = self.test_latency(host, port)
                if latency and latency <= 800:
                    good_configs[proto].append(f"{link} # {name} - {latency}ms")
                    self.after(0, lambda l=latency: self.log(f"Success: {latency}ms → {name}"))

            except:
                pass

        # Save results
        saved = 0
        for proto, items in good_configs.items():
            if not items: continue
            items.sort(key=lambda x: int(x.split("-")[-1].split("ms")[0]))

            fast = [x for x in items if int(x.split("-")[-1].split("ms")[0]) < 200]
            normal = [x for x in items if x not in fast]

            if fast:
                open(os.path.join(self.folder_path, f"FAST_{proto.upper()}.txt"), "w", encoding="utf-8").write("\n".join(fast))
                saved += len(fast)
            if normal:
                open(os.path.join(self.folder_path, f"{proto.upper()}.txt"), "w", encoding="utf-8").write("\n".join(normal))
                saved += len(normal)

        # Finish
        self.after(0, lambda: (
            self.progress_bar.set(1),
            self.percent_label.configure(text="100%"),
            self.status_label.configure(text=f"COMPLETED! Saved {saved} configs"),
            self.counter_label.configure(text=f"Finished – {saved} working links"),
            self.start_btn.configure(state="normal"),
            self.log(f"\nSCAN FINISHED!\nSaved {saved} fast configs to your folder!")
        ))

    # === Decoders ===
    def decode_vmess(self, link):
        try:
            b64 = link[8:]
            b64 += "=" * (-len(b64) % 4)
            data = json.loads(base64.b64decode(b64))
            return data.get("add"), data.get("port"), data.get("ps")
        except:
            return None, None, ""

    def decode_vless_trojan(self, link):
        try:
            u = urlparse(link)
            return u.hostname, u.port or 443, unquote(u.fragment or u.path.split("@")[0])
        except:
            return None, None, ""

    def decode_ss(self, link):
        try:
            if "@" in link[5:]:
                part = link.split("@")[1].split("#")[0]
                remark = unquote(link.split("#")[-1]) if "#" in link else ""
            else:
                enc = link[5:].split("#")[0]
                dec = base64.urlsafe_b64decode(enc + "===").decode("utf-8", errors="ignore")
                part = dec.split("@")[1] if "@" in dec else dec
                remark = unquote(link.split("#")[-1]) if "#" in link else ""
            host, port = part.split(":")[0], int(part.split(":")[1] if ":" in part else 443)
            return host, port, remark
        except:
            return None, None, ""

    def test_latency(self, host, port, timeout=4):
        try:
            start = time.time()
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            return int((time.time() - start) * 1000)
        except:
            return None

# ================================
# RUN THE APP
# ================================
if __name__ == "__main__":
    app = VPNScanner()
    app.mainloop()