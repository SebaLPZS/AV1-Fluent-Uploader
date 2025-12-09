# uploader_with_drawer.py
import tkinter as tk
from tkinter import ttk, filedialog, Menu, messagebox
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except Exception:
    # If tkinterdnd2 is not available, provide a fallback for basic file dialog use.
    TkinterDnD = tk
    DND_FILES = None
import requests
import pyperclip
import os
import time
import json
from threading import Thread
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
import urllib.parse
from plyer import notification
from bs4 import BeautifulSoup
import webbrowser
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw 
from io import BytesIO
import platformdirs


APP_NAME = "AV1 Fluent Uploader"
APP_AUTHOR = "sebalz1"


app_data_dir = platformdirs.user_data_dir(
    appname=APP_NAME, 
    appauthor=APP_AUTHOR, 
    ensure_exists=True
)

CONFIG_FILE = os.path.join(app_data_dir, "configup.json")
HISTORY_FILE = os.path.join(app_data_dir, "historyup.json")

THUMBNAIL_URL = "https://autocompressor.net/usercontent/images/07c5cc292dc72de9.jpg"
litterbox_expiration = "1h"
# ------------------------------------------------------------------

video_thumbnail = None
file_icon = None

BASE_FONT_FAMILY = "Segoe UI"
BASE_FONT_SIZE = 10
BASE_FONT_TUPLE = (BASE_FONT_FAMILY, BASE_FONT_SIZE)
BOLD_FONT_TUPLE = (BASE_FONT_FAMILY, BASE_FONT_SIZE, "bold")
TITLE_FONT_TUPLE = (BASE_FONT_FAMILY, 18, "bold") 
# ----------------------------------------

# --- Config load/save ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
        except Exception:
            config = {"host": "Catbox"}
else:
    config = {"host": "Catbox"}

def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# --- History helpers ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_history_entry(filename, host, url, clip_name=""): 
    """Adds an entry to history with an ISO timestamp and the clip's display name."""
    entry = {
        "filename": filename,
        "host": host,
        "url": url,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "clip_name": clip_name 
    }
    entry["is_video"] = filename.lower().endswith((".mp4", ".mov", ".webm", ".avi"))

    history = load_history()
    history.insert(0, entry)  # newest first
    save_history(history)
    return entry

# --- Notifications ---
def notify(title, message):
    try:
        notification.notify(title=title, message=message[:255], timeout=5)
    except Exception:
        # fallback to messagebox if plyer not available
        try:
            messagebox.showinfo(title, message)
        except Exception:
            print(title, message)

# --- Upload functions ---
def _make_progress_callback(progress_callback, encoder):
    total_size = encoder.len
    last_uploaded = 0
    last_time = time.time()
    stable_instant_speed = 0.0

    overall_start_time = time.time() 
    
    MIN_TIME_DELTA = 0.2  
    
    def callback(monitor):
        nonlocal last_uploaded, last_time, stable_instant_speed

        current_time = time.time()
        uploaded = monitor.bytes_read
        
        time_delta_since_last_measurement = current_time - last_time
        
        if time_delta_since_last_measurement >= MIN_TIME_DELTA: 
            bytes_delta = uploaded - last_uploaded
            
            if time_delta_since_last_measurement > 0:
                calculated_speed = bytes_delta / time_delta_since_last_measurement
                if calculated_speed > 0: 
                    stable_instant_speed = calculated_speed
            
            last_uploaded = uploaded
            last_time = current_time
        
        overall_elapsed = current_time - overall_start_time
        overall_speed = uploaded / overall_elapsed if overall_elapsed > 0 else 0.0
        
        remaining = total_size - uploaded
        eta = remaining / overall_speed if overall_speed > 0 else 0.0
        
        speed_to_display = stable_instant_speed if stable_instant_speed > 0 else overall_speed

        progress_callback(uploaded, total_size, speed_to_display, eta)
        
    return callback

def upload_to_catbox(file_path, progress_callback):
    mime_type = 'video/mp4' if file_path.lower().endswith(".mp4") else 'application/octet-stream'
    with open(file_path, 'rb') as f:
        encoder = MultipartEncoder({
            'reqtype': 'fileupload',
            'fileToUpload': (os.path.basename(file_path), f, mime_type)
        })
        monitor = MultipartEncoderMonitor(encoder, _make_progress_callback(progress_callback, encoder))
        response = requests.post('https://catbox.moe/user/api.php', data=monitor, headers={'Content-Type': monitor.content_type})
        if response.status_code == 200:
            return response.text.strip()
        else:
            raise Exception(f"Error uploading to Catbox (status {response.status_code})")

def upload_to_fileditch(file_path, progress_callback):
    mime_type = 'video/mp4' if file_path.lower().endswith(".mp4") else 'application/octet-stream'
    with open(file_path, 'rb') as f:
        encoder = MultipartEncoder(fields={
            'files[]': (os.path.basename(file_path), f, mime_type)
        })
        monitor = MultipartEncoderMonitor(encoder, _make_progress_callback(progress_callback, encoder))
        headers = {
            'Content-Type': monitor.content_type,
            'User-Agent': 'Mozilla/5.0',
            'Origin': 'https://fileditch.com',
            'Referer': 'https://fileditch.com/'
        }
        response = requests.post('https://up1.fileditch.com/upload.php', data=monitor, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get("success"):
                return json_data["files"][0]["url"]
            else:
                raise Exception("Error: fileditch did not return success=true")
        else:
            raise Exception(f"Error uploading to Fileditch (status {response.status_code})")

def upload_to_litterbox(file_path, progress_callback):
    mime_type = 'video/mp4' if file_path.lower().endswith(".mp4") else 'application/octet-stream'
    with open(file_path, 'rb') as f:
        encoder = MultipartEncoder(fields={
            'reqtype': 'fileupload',
            'time': litterbox_expiration,
            'fileToUpload': (os.path.basename(file_path), f, mime_type)
        })
        monitor = MultipartEncoderMonitor(encoder, _make_progress_callback(progress_callback, encoder))
        headers = {'Content-Type': monitor.content_type}
        response = requests.post('https://litterbox.catbox.moe/resources/internals/api.php', data=monitor, headers=headers)
        if response.status_code == 200 and response.text.startswith("https://"):
            return response.text.strip()
        else:
            raise Exception(f"Error uploading to Litterbox (status {response.status_code}): {response.text}")

def get_direct_fileditch_link(file_page_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(file_page_url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    video_tag = soup.find("video")
    if video_tag:
        source_tag = video_tag.find("source")
        if source_tag and source_tag.has_attr("src"):
            return source_tag["src"]
    raise Exception("Direct video link not found on Fileditch page.")

def build_av1_link(file_url):
    encoded_video = urllib.parse.quote(file_url, safe="")
    encoded_img = urllib.parse.quote(THUMBNAIL_URL, safe="")
    return f"https://autocompressor.net/av1?v={encoded_video}&i={encoded_img}&w=1920&h=1080"

# --- GUI and logic ---
def process_video():
    file_path = selected_file.get()
    name = name_entry.get().strip() 
    host = host_var.get()
    config["host"] = host
    save_config()

    if not file_path or not os.path.exists(file_path):
        notify("Error", "No file selected")
        return

    is_video = file_path.lower().endswith(".mp4")

    if is_video and not name:
        notify("Error", "Enter a name for the clip")
        return

    progress_bar["value"] = 0
    status_label.config(text="Uploading file...")
    root.update()

    def progress_callback(uploaded, total, speed, eta):
        percent = (uploaded / total) * 100
        progress_bar["value"] = percent
        mb_uploaded = uploaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        speed_mb = speed / (1024 * 1024)
        eta_str = time.strftime('%M:%S', time.gmtime(eta))
        status_label.config(text=f"Uploaded: {mb_uploaded:.1f}/{mb_total:.1f} MB | Speed: {speed_mb:.2f} MB/s | ETA: {eta_str}")
        root.update()

    def thread_func():
        try:
            if host == "Catbox":
                file_url = upload_to_catbox(file_path, progress_callback)
            elif host == "Fileditch":
                file_page_url = upload_to_fileditch(file_path, progress_callback)
                file_url = get_direct_fileditch_link(file_page_url) if is_video else file_page_url
            elif host == "Litterbox":
                file_url = upload_to_litterbox(file_path, progress_callback)
            else:
                raise Exception("Host not supported")

            full_filename = os.path.basename(file_path)
            
            clip_name_to_save = ""
            if is_video:
                final_display_name = name 
                
                av1_link = build_av1_link(file_url)
                markdown = f"[{final_display_name}]({av1_link})"
                final_url = av1_link
                clip_name_to_save = final_display_name
            else:
                final_display_name = full_filename
                
                markdown = file_url 
                final_url = file_url
                clip_name_to_save = final_display_name

            try:
                pyperclip.copy(markdown)
            except Exception:
                pass
            status_label.config(text="Done! Copied to clipboard.")
            notify("File uploaded", "Link copied to clipboard")

            try:
                add_history_entry(os.path.basename(file_path), host, final_url, clip_name_to_save) 
                try:
                    refresh_history_list()
                except Exception:
                    pass
            except Exception as e_hist:
                print("History save error:", e_hist)

        except Exception as e:
            status_label.config(text="Error")
            notify("Error", str(e))

    Thread(target=thread_func).start()

# --- File selection handlers ---
def on_file_selected(path):
    selected_file.set(path)
    drop_button.config(text=os.path.basename(path))
    upload_button.config(state="normal")
    if not path.lower().endswith(".mp4"):
        name_entry.delete(0, tk.END)
        name_entry.insert(0, "This file does not need a name")
        name_entry.config(state="disabled", foreground="#777")
    else:
        name_entry.config(state="normal", foreground="black")
        name_entry.delete(0, tk.END)

def on_drop(event):
    try:
        path = root.tk.splitlist(event.data)[0]
        on_file_selected(path)
    except Exception:
        pass

def on_click_drop():
    file_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
    if file_path:
        on_file_selected(file_path)

def select_host(h):
    host_var.set(h)
    config["host"] = h
    save_config()
    for btn in [catbox_btn, fileditch_btn, litterbox_btn]:
        btn.configure(style="TButton")
    if h == "Catbox":
        catbox_btn.configure(style="Selected.TButton")
    elif h == "Fileditch":
        fileditch_btn.configure(style="Selected.TButton")
    elif h == "Litterbox":
        litterbox_btn.configure(style="Selected.TButton")
    update_drop_text()

def show_litterbox_menu(event):
    menu = Menu(root, tearoff=0)
    def set_exp(time):
        global litterbox_expiration
        litterbox_expiration = time
        litterbox_btn.tooltip_text = f"Temporary upload: deletes after {litterbox_expiration}"
        litterbox_tooltip.text = litterbox_btn.tooltip_text
    menu.add_command(label="1 hour", command=lambda: set_exp("1h"))
    menu.add_command(label="12 hours", command=lambda: set_exp("12h"))
    menu.add_command(label="1 day", command=lambda: set_exp("1d"))
    menu.add_command(label="3 days", command=lambda: set_exp("3d"))
    menu.tk_popup(event.x_root, event.y_root)

# --- Simple tooltip class ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        try:
            x, y, _cx, cy = self.widget.bbox("insert")
        except Exception:
            x = y = 0
        x += self.widget.winfo_rootx() + 0
        y = self.widget.winfo_rooty() - 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#404040",
            foreground="#eee",
            relief=tk.FLAT,
            borderwidth=0,
            font=(BASE_FONT_FAMILY, 9, "italic") 
        )
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
            
def load_images():
    global video_thumbnail, file_icon
    try:
        response = requests.get(THUMBNAIL_URL)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img = img.resize((32, 32), Image.Resampling.LANCZOS) 
        video_thumbnail = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading video thumbnail: {e}")
        video_thumbnail = create_placeholder_icon("Video", "#4A86E8")

    file_icon = create_placeholder_icon("File", "#6AA84F")

def create_placeholder_icon(text, color):
    img = Image.new('RGB', (32, 32), color=color)
    d = ImageDraw.Draw(img)
    d.text((5, 8), text[0], fill="white", font=None)
    return ImageTk.PhotoImage(img)

# --- Main window ---
try:
    root = TkinterDnD.Tk()
except Exception:
    root = tk.Tk()

WINDOW_W = 640
WINDOW_H = 440
root.title("AV1 Fluent Uploader")
root.geometry(f"{WINDOW_W}x{WINDOW_H}")
root.resizable(False, False) 
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

root.configure(bg="#2d2d2d")

load_images()

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f'{width}x{height}+{x}+{y}')

center_window(root)

selected_file = tk.StringVar()
style = ttk.Style()
try:
    style.theme_use("clam")
except Exception:
    pass

style.configure("TButton",
                foreground="white",
                background="#444",
                font=BASE_FONT_TUPLE,
                padding=6)
style.map("TButton",
          background=[('active', '#555'), ('!disabled', '#444')])

style.configure("Selected.TButton",
                background="#0078D7",
                foreground="white")

style.map("Selected.TButton",
          background=[('active', '#0078D7'), ('!disabled', '#0078D7')])

style.configure("TLabel",
                foreground="white",
                background="#2d2d2d",
                font=BASE_FONT_TUPLE)

style.configure("MaxWeight.TLabel",
                foreground="#bbb",
                background="#2d2d2d",
                font=(BASE_FONT_FAMILY, 8))
                
style.configure("Treeview", 
                background="#2d2d2d", 
                foreground="white", 
                fieldbackground="#2d2d2d",
                rowheight=36) 
                
style.map('Treeview', 
          background=[('selected', '#0078D7'), 
                      ('active', '#555555'), 
                      ('!selected', '#2d2d2d')],    
          foreground=[('selected', 'white'), 
                      ('!selected', 'white')])

style.configure("Treeview.Heading", 
                font=BOLD_FONT_TUPLE,
                background="#444", 
                foreground="white",
                relief="flat")
style.map("Treeview.Heading", 
           background=[('active', '#444')]) 

style.configure("Fluent.Vertical.TScrollbar",
                troughcolor="#2d2d2d",
                bordercolor="#2d2d2d",
                background="#666666",
                arrowcolor="#2d2d2d",
                arrowsize=1,
                relief="flat",
                width=10)
style.map("Fluent.Vertical.TScrollbar",
          background=[('active', '#0078D7')])


# --- Hamburger button ---
hamburger_frame = tk.Frame(root, bg="#2d2d2d")
hamburger_frame.place(x=10, y=10)
hamburger_btn = tk.Label(hamburger_frame, text="☰", font=(BASE_FONT_FAMILY, 20), fg="white", bg="#2d2d2d", cursor="hand2")
hamburger_btn.pack()
# Drawer control variables created later
# --- Layout main UI ---
name_label = ttk.Label(root, text="File name:")
name_label.pack(pady=(10, 5)) 

# Ancho ajustado
name_entry = ttk.Entry(root, width=30, font=BASE_FONT_TUPLE)
name_entry.pack(pady=(0, 5)) 

host_label = ttk.Label(root, text="Choose the host:")
host_label.pack(pady=(5, 5)) 

host_var = tk.StringVar(value=config.get("host", "Catbox"))

host_frame = tk.Frame(root, bg="#2d2d2d")
host_frame.pack(pady=0) 

catbox_btn = ttk.Button(host_frame, text="Catbox", command=lambda: select_host("Catbox"))
catbox_btn.pack(side="left", padx=10)

fileditch_btn = ttk.Button(host_frame, text="Fileditch", command=lambda: select_host("Fileditch"))
fileditch_btn.pack(side="left", padx=10)

litterbox_btn = ttk.Button(host_frame, text="Litterbox", command=lambda: select_host("Litterbox"))
litterbox_btn.pack(side="left", padx=10)
litterbox_btn.bind("<Button-3>", show_litterbox_menu)

litterbox_btn.tooltip_text = f"Temporary upload: deletes after {litterbox_expiration}"
litterbox_tooltip = ToolTip(litterbox_btn, litterbox_btn.tooltip_text)

container = tk.Frame(root, bg="#2d2d2d")
container.pack(pady=10) 

drop_button = ttk.Button(container, text=">> Drag or browse <<", style="TButton", command=on_click_drop, width=45)
drop_button.pack(ipady=30) 
if DND_FILES is not None:
    try:
        drop_button.drop_target_register(DND_FILES)
        drop_button.dnd_bind('<<Drop>>', on_drop)
    except Exception:
        pass

# Label overlapping the button to show max file size
max_weight_label = tk.Label(container, text="", fg="#bbb", bg="#444444", font=(BASE_FONT_FAMILY, 8))
max_weight_label.place(relx=0.5, rely=0.8, anchor="center")

def on_drop_button_enter(event):
    max_weight_label.config(background="#555555")

def on_drop_button_leave(event):
    max_weight_label.config(background="#444444")

drop_button.bind("<Enter>", on_drop_button_enter)
drop_button.bind("<Leave>", on_drop_button_leave)

def update_drop_text():
    host = host_var.get()
    if host == "Catbox":
        max_weight = "200 MB"
    elif host == "Fileditch":
        max_weight = "10 GB"
    elif host == "Litterbox":
        max_weight = "1 GB"
    else:
        max_weight = "Unknown"
    max_weight_label.config(text=f"Max file size: {max_weight}")

select_host(host_var.get())

upload_button = ttk.Button(root, text="Upload", command=process_video, state="disabled")
upload_button.pack(pady=5)

# --- Progress and status ---
style.configure("Custom.Horizontal.TProgressbar",
                troughcolor="#2d2d2d",
                background="#0078D7",
                thickness=20)
progress_bar = ttk.Progressbar(root, length=400, mode='determinate', style="Custom.Horizontal.TProgressbar") 
progress_bar.pack(pady=10)

status_label = ttk.Label(root, text="")
status_label.pack(pady=5)

# --- Existing history window variables (kept for compatibility) ---
history_window = None
history_tree = None

# --- Drawer (full-screen overlay) ---
drawer = tk.Frame(root, bg="#2d2d2d", width=WINDOW_W, height=WINDOW_H)
drawer.place(x=-WINDOW_W, y=0)  # hidden off-screen initially

drawer_open = False
ANIMATION_DAMPING = 0.25 
ANIMATION_INTERVAL = 8  

animation_id = None 

def _animate_drawer(target_x):

    global animation_id, drawer_open
    
    current_x = drawer.winfo_x()
    
    distance_to_go = target_x - current_x
    step = distance_to_go * ANIMATION_DAMPING
    new_x = current_x + step
    
    stop_condition = abs(distance_to_go) < 1
    overshoot_condition = (step > 0 and new_x > target_x) or (step < 0 and new_x < target_x)
    
    if stop_condition or overshoot_condition:
        drawer.place(x=target_x, y=0)
        
        drawer_open = (target_x == 0)
        
        animation_id = None 
        return

    drawer.place(x=new_x, y=0)
    
    animation_id = root.after(ANIMATION_INTERVAL, lambda: _animate_drawer(target_x))


def open_history_drawer(event=None):

    global drawer_open, animation_id

    if animation_id is not None:
        try:
            root.after_cancel(animation_id)
        except Exception:
            pass 
        animation_id = None
        
    current_x = drawer.winfo_x()
    .
    if current_x > -WINDOW_W / 2:
        target = -WINDOW_W
    else:
        refresh_history_list()
        target = 0
        
    _animate_drawer(target)

hamburger_btn.bind("<Button-1>", open_history_drawer)

# --- Drawer content ---
drawer_title = tk.Label(drawer, text="Upload History", bg="#2d2d2d", fg="white",
                        font=TITLE_FONT_TUPLE) 
drawer_title.place(x=20, y=10)

drawer_close_btn = tk.Label(drawer, text="✕", font=(BASE_FONT_FAMILY, 14), fg="white", bg="#2d2d2d", cursor="hand2")
drawer_close_btn.place(x=WINDOW_W-30, y=8)
drawer_close_btn.bind("<Button-1>", lambda e: open_history_drawer())

history_list_frame = tk.Frame(drawer, bg="#2d2d2d")
history_list_frame.place(x=20, y=50, width=WINDOW_W-40, height=300) 

history_tree = ttk.Treeview(history_list_frame, 
                            columns=("clip_name", "host", "timestamp"), 
                            show="headings", 
                            selectmode="browse")
history_tree.pack(fill="both", expand=True, side="left")


scrollbar = ttk.Scrollbar(history_list_frame, 
                          orient="vertical", 
                          command=history_tree.yview, 
                          style="Fluent.Vertical.TScrollbar")
history_tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side="right", fill="y")

history_tree.heading("#0", text="Preview") 
history_tree.column("#0", width=40, anchor="center")

history_tree.heading("clip_name", text="File Name")
history_tree.column("clip_name", width=220)

history_tree.heading("host", text="Host")
history_tree.column("host", width=90, anchor="center")
history_tree.heading("timestamp", text="Upload Date")
history_tree.column("timestamp", width=250, anchor="center")


drawer_btn_frame = tk.Frame(drawer, bg="#2d2d2d")
drawer_btn_frame.place(x=20, y=370)

copy_btn = ttk.Button(drawer_btn_frame, text="Copy URL", command=lambda: drawer_copy_url())
copy_btn.pack(side="left", padx=5)

open_btn = ttk.Button(drawer_btn_frame, text="Open URL", command=lambda: drawer_open_url())
open_btn.pack(side="left", padx=5)

clear_btn = ttk.Button(drawer_btn_frame, text="Clear History", command=lambda: drawer_clear_history())
clear_btn.pack(side="left", padx=5)

def refresh_history_list():
    global video_thumbnail, file_icon
    for row in history_tree.get_children():
        history_tree.delete(row)

    history = load_history()
    for item in history:
        display_name = item.get("clip_name") or item.get("filename", "unknown file") 
        host = item.get("host", "Unknown Host")
        timestamp_str = item.get("timestamp", "")
        is_video = item.get("is_video", False)
        
        date_time_str = "Unknown Date"
        if timestamp_str:
            try:
                dt_utc = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                dt_local = dt_utc.astimezone()
                date_time_str = dt_local.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                date_time_str = "Invalid Date Format"

        icon_to_use = video_thumbnail if is_video and video_thumbnail else file_icon
        
        history_tree.insert("", 
                            "end", 
                            text="", 
                            image=icon_to_use, 
                            values=(display_name, host, date_time_str))

def drawer_get_selected_entry():
    sel = history_tree.selection()
    if not sel:
        notify("Error", "Select an entry first")
        return None, None
    
    item_id = sel[0]
    index = history_tree.get_children().index(item_id)
    
    history = load_history()
    if index < 0 or index >= len(history):
        return None, None
    return history[index], index

def drawer_copy_url():
    entry, _ = drawer_get_selected_entry()
    if not entry:
        notify("Error", "Select an entry first")
        return
        
    url = entry["url"]
    clip_name = entry.get("clip_name", "") 
    
    if entry.get("is_video"):
        content_to_copy = f"[{clip_name}]({url})"
        message_type = "Link (Markdown)"
    else:
        content_to_copy = url
        message_type = "URL"
        
    try:
        pyperclip.copy(content_to_copy)
    except Exception:
        pass
    notify("Copied", f"{message_type} copied to clipboard")
    
def drawer_open_url():
    entry, _ = drawer_get_selected_entry()
    if not entry:
        notify("Error", "Select an entry first")
        return
    try:
        webbrowser.open(entry["url"])
    except Exception as e:
        notify("Error", str(e))

def drawer_clear_history():
    if messagebox.askyesno("Confirm", "Clear all history?"):
        save_history([])
        refresh_history_list()

# --- Keep compatibility with old History window function ---
def open_history_window():
    messagebox.showinfo("Info", "Using new History Drawer. Click '☰' at the top-left.")

def refresh_history_view():
    pass

def copy_selected_url():
    messagebox.showinfo("Info", "Use 'Copy URL' button in the History Drawer.")

def open_selected_url():
    messagebox.showinfo("Info", "Use 'Open URL' button in the History Drawer.")

def clear_history_confirm():
    drawer_clear_history()

root.mainloop()