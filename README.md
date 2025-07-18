# AV1 Fluent Uploader

**AV1 Fluent Uploader** is a lightweight and user-friendly desktop application built with Python and Tkinter that allows you to quickly upload video files and other types of files to popular hosting services like **Catbox**, **Fileditch**, and **Litterbox**.

## Features

- Drag and drop or browse files to upload  
- Support for multiple file hosts (Catbox, Fileditch, Litterbox)  
- Progress bar showing upload progress, speed, and estimated time remaining  
- Automatic clipboard copy of generated Markdown link after upload  
- Temporary upload expiration setting for Litterbox with easy right-click menu  
- Built-in AV1 video link builder via [Autocompressor](https://autocompressor.net/av1) for seamless embedding  
- Upload videos bypassing Discord's file size limits by hosting externally  
- Desktop notifications on upload success or failure  
- Simple and modern UI with dark theme  

## Technologies

- Python
- Tkinter + tkinterdnd2 for GUI and drag-and-drop support  
- Requests + requests-toolbelt for HTTP multipart uploads  
- Plyer for cross-platform desktop notifications  
- BeautifulSoup for HTML parsing (Fileditch direct video link extraction)  

## Usage

1. Choose a host from the options (Catbox, Fileditch, Litterbox).  
2. Drag and drop a file or browse your computer to select a file.  
3. (For videos) Enter a name for your clip.  
4. Click Upload and wait for the progress bar to complete.  
5. The Markdown link with an embedded AV1 video player will be copied to your clipboard automatically — ideal for sharing videos larger than Discord's upload limits.  

## Note

Discord may cache files from temporary hosts for much longer than the files are actually available on the host. Because of this, I recommend using temporary file hosting services to reduce the load on permanent hosts. This helps prevent rate-limiting or bans, and ultimately helps the application remain functional for a longer time.

## Installation

Make sure you have Python 3 installed, then install dependencies with:

```bash
pip install -r requirements.txt
