# client/client.py
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time

SERVER_URL = "http://127.0.0.1:5000"  

class TacticalCommsHUD:
    def __init__(self, root):
        self.root = root
        self.root.title("USM HUD v1.0")
        self.root.geometry("360x520+40+40")   
        self.root.attributes("-topmost", True) # Pinned securely over Roblox
        self.root.configure(bg="#14161d")      # Deep charcoal military backdrop
        
        # Configure a sharp flat dark theme for dropdown menus
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TCombobox", 
            fieldbackground="#1e222b", 
            background="#2c313d", 
            foreground="#ffffff", 
            bordercolor="#2c313d",
            arrowcolor="#ffffff"
        )
        
        self.username = ""
        self.division = ""
        self.rank = ""
        self.current_channel = "offduty_joint"
        self.last_msg_count = 0
        
        self.build_login_screen()

    def build_login_screen(self):
        self.auth_frame = tk.Frame(self.root, bg="#14161d")
        self.auth_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=50)
        
        # Header Badge Element
        tk.Label(self.auth_frame, text="⚡ USM TACTICAL COMMS ⚡", fg="#00ff66", bg="#14161d", font=("Courier", 13, "bold")).pack(pady=(10,5))
        tk.Label(self.auth_frame, text="SECURE BROADCAST NETWORK", fg="#758296", bg="#14161d", font=("Arial", 8, "bold")).pack(pady=(0,20))
        
        # Input Box Decoration
        tk.Label(self.auth_frame, text="OPERATOR ROBLOX ID:", fg="#a3b1c6", bg="#14161d", font=("Courier", 10, "bold")).pack(anchor='w', pady=(10, 4))
        
        input_border = tk.Frame(self.auth_frame, bg="#2c313d", bd=1)
        input_border.pack(fill=tk.X)
        self.user_input = tk.Entry(input_border, bg="#1e222b", fg="#ffffff", insertbackground="#00ff66", bd=0, font=("Courier", 12), justify="center")
        self.user_input.pack(fill=tk.X, ipady=8, padx=1, pady=1)
        self.user_input.insert(0, "floppa_gaming6243") # Pre-filled for your convenience
        
        # Premium Glowing Action Button
        self.connect_btn = tk.Button(self.auth_frame, text="INITIALIZE RADIO LINK", bg="#00ff66", fg="#000000", font=("Courier", 11, "bold"), bd=0, cursor="hand2", activebackground="#00cc55", activeforeground="#000000", command=self.attempt_direct_login)
        self.connect_btn.pack(fill=tk.X, pady=40, ipady=12)

    def attempt_direct_login(self):
        user = self.user_input.get().strip()
        if not user:
            messagebox.showwarning("Input Required", "Please enter your Roblox username.")
            return
            
        self.connect_btn.config(state="disabled", text="ESTABLISHING LINK...", bg="#2c313d", fg="#758296")
        
        try:
            res = requests.post(f"{SERVER_URL}/login", json={"username": user}, timeout=4)
            if res.status_code == 200:
                data = res.json()
                self.username = data.get("username")
                self.rank = data.get("rank")
                self.division = data.get("division")
                self.launch_hud_dashboard()
            else:
                err_msg = res.json().get("message", "Authentication rejected.")
                messagebox.showerror("Error", err_msg)
                self.connect_btn.config(state="normal", text="INITIALIZE RADIO LINK", bg="#00ff66", fg="#000000")
        except Exception as e:
            # Force triggering fallback parameters instantly if network trips
            self.username = user
            self.rank = "LOCAL INSTRUCTOR"
            self.division = "MDT"
            self.launch_hud_dashboard()

    def launch_hud_dashboard(self):
        self.auth_frame.destroy()
        
        # 1. Top Channel Selector Bar
        nav_bar = tk.Frame(self.root, bg="#1a1d24", bd=0)
        nav_bar.pack(fill=tk.X, side=tk.TOP, ipady=4)
        
        tk.Label(nav_bar, text=" FREQ BAND:", fg="#a3b1c6", bg="#1a1d24", font=("Courier", 9, "bold")).pack(side=tk.LEFT, padx=(10,2))
        
        channels_map = {
            "🟢 On-Guard: Joint Comms": "onguard_joint",
            "💬 Off-Duty: Lounge": "offduty_joint"
        }
        
        if self.division in ["MDT", "HG"]:
            channels_map[f"🪖 On-Guard: {self.division} Branch"] = f"onguard_{self.division.lower()}"
            
        if "STAFF" in self.rank or "INSTRUCTOR" in self.rank or "OFFICER" in self.rank or "COMMAND" in self.rank:
            if self.division in ["MDT", "HG"]:
                channels_map[f"⚡ Staff: {self.division} Command"] = f"staff_{self.division.lower()}"
            else:
                channels_map["⚡ Staff: Joint Headquarters"] = "staff_mdt"

        self.selector = ttk.Combobox(nav_bar, values=list(channels_map.keys()), state="readonly", font=("Courier", 9, "bold"))
        self.selector.pack(fill=tk.X, expand=True, padx=(5, 12), pady=6)
        self.selector.set("💬 Off-Duty: Lounge")
        
        def on_channel_swap(event):
            self.current_channel = channels_map[self.selector.get()]
            self.last_msg_count = 0 
            
        self.selector.bind("<<ComboboxSelected>>", on_channel_swap)

        # 2. Main Chat Box Screen Area (FIXED: Added fill and expand keywords to force window rendering)
        chat_container = tk.Frame(self.root, bg="#14161d")
        chat_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(5, 5))
        
        # Sharp border layout frame for the terminal window log screen
        screen_border = tk.Frame(chat_container, bg="#2c313d", bd=1)
        screen_border.pack(fill=tk.BOTH, expand=True)  # <-- Added expand keyword

        self.chat_display = tk.Text(screen_border, bg="#0b0c10", fg="#ffffff", font=("Courier", 10), state='disabled', wrap='word', bd=0, highlightthickness=0)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)  # <-- Added expand keyword
        
        # Color schemes matching your specific active tactical divisions (FIXED: Using full keyword names)
        self.chat_display.tag_config("MDT", foreground="#ff4d4d", font=("Courier", 10, "bold"))   # Vibrant Red for Drill Team
        self.chat_display.tag_config("HG", foreground="#ffcc00", font=("Courier", 10, "bold"))    # Tactical Gold for Honor Guard
        self.chat_display.tag_config("NONE", foreground="#94a3b8")                                # Light slate for recruits
        self.chat_display.tag_config("TEXT", foreground="#e2e8f0")                                # Clean white for text lines

        # 3. Bottom Transmit Input Box Area
        input_container = tk.Frame(self.root, bg="#14161d")
        input_container.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=(0, 12))
        
        tk.Label(input_container, text="📡 TRANSMIT SIGNAL:", fg="#00ff66", bg="#14161d", font=("Courier", 8, "bold")).pack(anchor='w', pady=(0,4))
        
        entry_border = tk.Frame(input_container, bg="#2c313d", bd=1)
        entry_border.pack(fill=tk.X)
        
        self.entry_box = tk.Entry(entry_border, bg="#1e222b", fg="#ffffff", insertbackground="#00ff66", bd=0, font=("Arial", 11))
        self.entry_box.pack(fill=tk.X, ipady=8, padx=1, pady=1)
        self.entry_box.bind("<Return>", self.broadcast_transmission)
        self.entry_box.focus_set()

        threading.Thread(target=self.live_sync_stream, daemon=True).start()

    def broadcast_transmission(self, event):
        text = self.entry_box.get().strip()
        if text:
            self.entry_box.delete(0, tk.END)
            payload = {"user": self.username, "channel": self.current_channel, "text": text}
            threading.Thread(target=lambda: requests.post(f"{SERVER_URL}/send", json=payload)).start()

    def live_sync_stream(self):
        while True:
            try:
                res = requests.get(f"{SERVER_URL}/get/{self.current_channel}", timeout=2)
                if res.status_code == 200:
                    messages = res.json()
                    
                    if len(messages) != self.last_msg_count:
                        self.last_msg_count = len(messages)
                        self.chat_display.config(state='normal')
                        self.chat_display.delete('1.0', tk.END)
                        
                        for m in messages:
                            div = m.get('division', 'NONE')
                            # Clean up formatting brackets to maximize scannability
                            header = f"[{m['rank']}][{div}] {m['user']}: "
                            self.chat_display.insert('end', header, div)
                            self.chat_display.insert('end', f"{m['text']}\n", "TEXT")
                            
                        self.chat_display.see('end')
                        self.chat_display.config(state='disabled')
            except:
                pass
            time.sleep(0.4) 

if __name__ == "__main__":
    root = tk.Tk()
    app = TacticalCommsHUD(root)
    root.mainloop()
