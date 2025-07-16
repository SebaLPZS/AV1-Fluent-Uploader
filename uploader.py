import tkinter as tk
from tkinter import ttk, filedialog, Menu
from tkinterdnd2 import TkinterDnD, DND_FILES
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

CONFIG_FILE = "config.json"
THUMBNAIL_URL = "https://autocompressor.net/usercontent/images/07c5cc292dc72de9.jpg"
litterbox_expiration = "1h"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {"host": "Catbox"}

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def notify(title, message):
    notification.notify(title=title, message=message[:255], timeout=5)

def upload_to_catbox(file_path, progress_callback):
    def create_callback(encoder):
        total_size = encoder.len
        start_time = time.time()
        def callback(monitor):
            uploaded = monitor.bytes_read
            elapsed = time.time() - start_time
            speed = uploaded / elapsed if elapsed > 0 else 0
            eta = (total_size - uploaded) / speed if speed > 0 else 0
            progress_callback(uploaded, total_size, speed, eta)
        return callback

    mime_type = 'video/mp4' if file_path.lower().endswith(".mp4") else 'application/octet-stream'

    with open(file_path, 'rb') as f:
        encoder = MultipartEncoder({
            'reqtype': 'fileupload',
            'fileToUpload': (os.path.basename(file_path), f, mime_type)
        })
        monitor = MultipartEncoderMonitor(encoder, create_callback(encoder))
        response = requests.post('https://catbox.moe/user/api.php', data=monitor, headers={'Content-Type': monitor.content_type})
        if response.status_code == 200:
            return response.text.strip()
        else:
            raise Exception(f"Error uploading to Catbox (status {response.status_code})")

def upload_to_fileditch(file_path, progress_callback):
    def create_callback(encoder):
        total_size = encoder.len
        start_time = time.time()
        def callback(monitor):
            uploaded = monitor.bytes_read
            elapsed = time.time() - start_time
            speed = uploaded / elapsed if elapsed > 0 else 0
            eta = (total_size - uploaded) / speed if speed > 0 else 0
            progress_callback(uploaded, total_size, speed, eta)
        return callback

    mime_type = 'video/mp4' if file_path.lower().endswith(".mp4") else 'application/octet-stream'

    with open(file_path, 'rb') as f:
        encoder = MultipartEncoder(fields={
            'files[]': (os.path.basename(file_path), f, mime_type)
        })
        monitor = MultipartEncoderMonitor(encoder, create_callback(encoder))
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
    def create_callback(encoder):
        total_size = encoder.len
        start_time = time.time()
        def callback(monitor):
            uploaded = monitor.bytes_read
            elapsed = time.time() - start_time
            speed = uploaded / elapsed if elapsed > 0 else 0
            eta = (total_size - uploaded) / speed if speed > 0 else 0
            progress_callback(uploaded, total_size, speed, eta)
        return callback

    mime_type = 'video/mp4' if file_path.lower().endswith(".mp4") else 'application/octet-stream'

    with open(file_path, 'rb') as f:
        encoder = MultipartEncoder(fields={
            'reqtype': 'fileupload',
            'time': litterbox_expiration,
            'fileToUpload': (os.path.basename(file_path), f, mime_type)
        })
        monitor = MultipartEncoderMonitor(encoder, create_callback(encoder))
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

            if is_video:
                av1_link = build_av1_link(file_url)
                markdown = f"[{name}]({av1_link})"
            else:
                markdown = file_url

            pyperclip.copy(markdown)
            status_label.config(text="Done! Copied to clipboard.")
            notify("File uploaded", "Link copied to clipboard")
        except Exception as e:
            status_label.config(text="Error")
            notify("Error", str(e))

    Thread(target=thread_func).start()

def on_file_selected(path):
    selected_file.set(path)
    drop_button.config(text=os.path.basename(path))
    upload_button.config(state="normal")
    if not path.lower().endswith(".mp4"):
        name_entry.delete(0, tk.END)
        name_entry.insert(0, "This file does not need a name")
        name_entry.config(state="disabled", foreground="#777", background="#2d2d2d")
    else:
        name_entry.config(state="normal", foreground="black", background="white")
        name_entry.delete(0, tk.END)

def on_drop(event):
    path = root.tk.splitlist(event.data)[0]
    on_file_selected(path)

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
        # Update visible tooltip
        litterbox_tooltip.text = litterbox_btn.tooltip_text
    menu.add_command(label="1 hour", command=lambda: set_exp("1h"))
    menu.add_command(label="12 hours", command=lambda: set_exp("12h"))
    menu.add_command(label="1 day", command=lambda: set_exp("1d"))
    menu.add_command(label="3 days", command=lambda: set_exp("3d"))
    menu.tk_popup(event.x_root, event.y_root)

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
        x, y, _cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 0
        y = self.widget.winfo_rooty() - 25  # Show above the widget
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
            font=("Segoe UI", 9, "italic")
        )
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

root = TkinterDnD.Tk()
root.title("AV1 Fluent Uploader")
root.geometry("603x487")
root.configure(bg="#2d2d2d")

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
style.theme_use("clam")

style.configure("TButton",
                foreground="white",
                background="#444",
                font=("Segoe UI", 10),
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
                font=("Segoe UI", 10))

style.configure("MaxWeight.TLabel",
                foreground="#bbb",
                background="#2d2d2d",
                font=("Segoe UI", 8))

name_label = ttk.Label(root, text="File name:")
name_label.pack(pady=(20, 5))

name_entry = ttk.Entry(root, width=40, font=("Segoe UI", 10))
name_entry.pack(pady=(0, 10))

host_label = ttk.Label(root, text="Choose the host:")
host_label.pack(pady=(10, 5))

host_var = tk.StringVar(value=config.get("host", "Catbox"))

host_frame = tk.Frame(root, bg="#2d2d2d")
host_frame.pack(pady=2)

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
container.pack(pady=15)

drop_button = ttk.Button(container, text=">> Drag or browse <<", style="TButton", command=on_click_drop, width=45)
drop_button.pack(ipady=40)
drop_button.drop_target_register(DND_FILES)
drop_button.dnd_bind('<<Drop>>', on_drop)

# Label overlapping the button to show max file size
max_weight_label = tk.Label(container, text="", fg="#bbb", bg="#444444", font=("Segoe UI", 8))
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

style.configure("Custom.Horizontal.TProgressbar",
                troughcolor="#2d2d2d",
                background="#0078D7",
                thickness=20)
progress_bar = ttk.Progressbar(root, length=400, mode='determinate', style="Custom.Horizontal.TProgressbar")
progress_bar.pack(pady=10)

status_label = ttk.Label(root, text="")
status_label.pack(pady=5)

root.mainloop()

##    Created by sebalz1