# AV1 Fluent Uploader

**AV1 Fluent Uploader** is a lightweight desktop application built with Python and Tkinter, designed to simplify uploading videos **larger than Discord's limits**. It provides direct hosting to services like **Catbox**, **Fileditch**, and **Litterbox**, and automatically generates an embeddable AV1 player link.

## Features

- Drag and drop or browse files to upload.
- Support for multiple file hosts (**Catbox**, **Fileditch**, **Litterbox**).
- **Real-Time Speed Display:** The progress bar shows **instantaneous upload speed** (MB/s), progress, and estimated time remaining (ETA).
- **Integrated History Drawer:** Quick-access panel for reviewing past uploads, copying links, and opening the hosted file.
- Automatic clipboard copy of generated Markdown link after upload.
- Temporary upload expiration setting for Litterbox with an easy right-click menu.
- Built-in AV1 video link builder via [Autocompressor](https://autocompressor.net/av1) for seamless embedding.
- Upload videos bypassing Discord's file size limits by hosting externally.
- Desktop notifications on upload success or failure.
- Simple and modern UI with a dark theme and **consistent font family** (`Segoe UI`) across all elements.

## Technologies

- Python
- Tkinter + tkinterdnd2 for GUI and drag-and-drop support.
- Requests + requests-toolbelt for HTTP multipart uploads.
- **Pillow (PIL)** for generating icons and managing the history list thumbnails.
- Plyer for cross-platform desktop notifications.
- BeautifulSoup for HTML parsing (Fileditch direct video link extraction).

## Usage

1. Choose a host from the options (Catbox, Fileditch, Litterbox).
2. Drag and drop a file or browse your computer to select a file.
3. (For videos) Enter a descriptive name for your clip.
4. Click Upload and monitor the **real-time speed** and progress bar.
5. The **Markdown link** with an embedded AV1 video player will be automatically copied to your clipboard, ready for sharing videos larger than Discord's upload limits.

---

## Note

Discord may cache files from temporary hosts for much longer than the files are actually available on the host. Because of this, I recommend using temporary file hosting services to reduce the load on permanent hosts. This helps prevent rate-limiting or bans, and ultimately helps the application remain functional for a longer time.

---

## Installation

Make sure you have Python 3 installed. You can install all dependencies with:


```bash
pip install -r requirements.txt
