import sys
import os
import json
import re
import urllib.request
import multiprocessing
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from bs4 import BeautifulSoup

# إخفاء تحذيرات وسجلات التحميل الخاصة بـ imageio_ffmpeg
FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass

import yt_dlp

# ضبط الطابع العصري المظلم
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

CONFIG_FILE = "config.json"


class MoYahiaDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mo Yahia Downloader Pro - Universal Bypass Edition")
        self.geometry("680x620")
        self.resizable(False, False)

        # إدارة حالة التحميل والإيقاف
        self.is_downloading = False
        self.is_paused = False
        self.download_thread = None

        self.download_path = ctk.StringVar(value=self.get_initial_download_path())
        self.format_choice = ctk.StringVar(value="video")
        self.quality_choice = ctk.StringVar(value="أعلى جودة متاحة (Best)")

        self.build_ui()
        self.enable_paste_features()

    def get_initial_download_path(self):
        config = self.load_config()
        saved_path = config.get("download_path")
        if saved_path and os.path.exists(saved_path):
            return saved_path
        default_dir = os.path.expanduser("~/Downloads")
        return default_dir if os.path.exists(default_dir) else os.getcwd()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        config_data = {"download_path": self.download_path.get()}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def build_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(20, 10), fill="x", padx=30)

        title = ctk.CTkLabel(
            header_frame, 
            text="MO YAHIA DOWNLOADER PRO", 
            font=("Segoe UI", 24, "bold"),
            text_color="#00E6FF"
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame, 
            text="الجيل الجديد للتحميل من جميع المنصات ومواقع البث المباشر (Lulustream, Dood, Streamtape...)", 
            font=("Segoe UI", 11),
            text_color="#8A99AD"
        )
        subtitle.pack(anchor="w")

        card_entry = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E222D")
        card_entry.pack(pady=10, padx=30, fill="x")

        self.url_entry = ctk.CTkEntry(
            card_entry, 
            placeholder_text="ضع رابط الفيديو أو الصفحة (YouTube, TikTok, Lulustream...)...", 
            height=45,
            border_width=0,
            fg_color="transparent",
            text_color="#FFFFFF",
            font=("Segoe UI", 13)
        )
        self.url_entry.pack(padx=15, pady=5, fill="x")

        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(pady=10, padx=30, fill="x")

        self.format_menu = ctk.CTkSegmentedButton(
            options_frame,
            values=["فيديو MP4 🎬", "صوت MP3 🎵"],
            command=self.on_format_change,
            selected_color="#1F6AA5",
            unselected_color="#1E222D"
        )
        self.format_menu.set("فيديو MP4 🎬")
        self.format_menu.pack(side="left", padx=(0, 15))

        self.quality_dropdown = ctk.CTkOptionMenu(
            options_frame,
            values=["أعلى جودة متاحة (Best)", "1080p", "720p", "480p", "360p"],
            variable=self.quality_choice,
            fg_color="#1E222D",
            button_color="#2B303C",
            dropdown_fg_color="#1E222D"
        )
        self.quality_dropdown.pack(side="right")

        path_card = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E222D")
        path_card.pack(pady=10, padx=30, fill="x")

        self.path_label = ctk.CTkLabel(
            path_card, 
            textvariable=self.download_path, 
            anchor="w",
            text_color="#A0AAB8",
            font=("Segoe UI", 11)
        )
        self.path_label.pack(side="left", padx=15, fill="x", expand=True)

        browse_btn = ctk.CTkButton(
            path_card, 
            text="تغيير المجلد", 
            width=100, 
            height=32,
            fg_color="#2B303C",
            hover_color="#3A4151",
            command=self.select_folder
        )
        browse_btn.pack(side="right", padx=5, pady=5)

        status_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E222D")
        status_card.pack(pady=15, padx=30, fill="x")

        self.status_label = ctk.CTkLabel(
            status_card, 
            text="جاهز لبدء التحميل", 
            font=("Segoe UI", 12),
            text_color="#00E6FF"
        )
        self.status_label.pack(pady=(12, 5))

        self.progress_bar = ctk.CTkProgressBar(status_card, height=10, progress_color="#00E6FF")
        self.progress_bar.pack(pady=(5, 15), padx=20, fill="x")
        self.progress_bar.set(0)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.download_btn = ctk.CTkButton(
            btn_frame, 
            text="بدء التحميل الآن 🚀", 
            width=200, 
            height=48,
            font=("Segoe UI", 14, "bold"),
            fg_color="#00E6FF",
            text_color="#000000",
            hover_color="#00B3C7",
            command=self.toggle_download
        )
        self.download_btn.pack(side="left", padx=10)

        self.pause_btn = ctk.CTkButton(
            btn_frame, 
            text="إيقاف مؤقت ⏸️", 
            width=140, 
            height=48,
            font=("Segoe UI", 13, "bold"),
            fg_color="#2B303C",
            text_color="#FFFFFF",
            hover_color="#3A4151",
            state="disabled",
            command=self.toggle_pause
        )
        self.pause_btn.pack(side="left", padx=10)

    def on_format_change(self, value):
        if "MP3" in value:
            self.format_choice.set("audio")
            self.quality_dropdown.configure(state="disabled")
        else:
            self.format_choice.set("video")
            self.quality_dropdown.configure(state="normal")

    def enable_paste_features(self):
        self.url_entry.bind("<Key>", self.handle_universal_paste)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="لصق (Paste)", command=self.paste_from_clipboard)
        self.context_menu.add_command(label="مسح (Clear)", command=lambda: self.url_entry.delete(0, tk.END))
        self.url_entry.bind("<Button-3>", lambda e: self.context_menu.tk_popup(e.x_root, e.y_root))

    def handle_universal_paste(self, event):
        if (event.state & 0x4) and (event.keysym.lower() == 'v' or event.keycode == 86):
            self.paste_from_clipboard()
            return "break"

    def paste_from_clipboard(self):
        try:
            clipboard_content = self.clipboard_get().strip()
            if clipboard_content:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(tk.INSERT, clipboard_content)
        except Exception:
            pass

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path.set(folder)
            self.save_config()

    def progress_callback(self, d):
        if self.is_paused:
            while self.is_paused:
                pass

        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                percentage = downloaded / total
                self.progress_bar.set(percentage)
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                self.status_label.configure(
                    text=f"جاري التحميل... {int(percentage * 100)}% | السرعة: {speed} | المتبقي: {eta}",
                    text_color="#00E6FF"
                )
        elif d['status'] == 'finished':
            self.progress_bar.set(1.0)
            self.status_label.configure(text="جاري معالجة وتجميع الملف الحقيقي...", text_color="#00FF88")

    def toggle_pause(self):
        if not self.is_downloading:
            return

        if not self.is_paused:
            self.is_paused = True
            self.pause_btn.configure(text="استئناف ▶️", fg_color="#007ACC")
            self.status_label.configure(text="تم إيقاف التحميل مؤقتاً ⏸️", text_color="#FFCC00")
        else:
            self.is_paused = False
            self.pause_btn.configure(text="إيقاف مؤقت ⏸️", fg_color="#2B303C")
            self.status_label.configure(text="جاري استئناف التحميل...", text_color="#00E6FF")

    def toggle_download(self):
        if not self.is_downloading:
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showwarning("تنبيه", "يرجى إدخال رابط أولاً.")
                return

            self.is_downloading = True
            self.is_paused = False
            self.download_btn.configure(text="إلغاء ⏹️", fg_color="#FF3B30", hover_color="#C72C23")
            self.pause_btn.configure(state="normal")
            self.progress_bar.set(0)

            self.download_thread = threading.Thread(target=self.run_downloader, args=(url,))
            self.download_thread.daemon = True
            self.download_thread.start()
        else:
            self.is_downloading = False
            self.is_paused = False
            self.reset_ui_state("تم إلغاء التحميل.")

    def reset_ui_state(self, message=""):
        self.is_downloading = False
        self.is_paused = False
        self.download_btn.configure(text="بدء التحميل الآن 🚀", fg_color="#00E6FF", text_color="#000000", hover_color="#00B3C7")
        self.pause_btn.configure(text="إيقاف مؤقت ⏸️", state="disabled", fg_color="#2B303C")
        if message:
            self.status_label.configure(text=message, text_color="#FFFFFF")

    def scan_page_for_embeds(self, url):
        urls_to_try = [url]
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=7).read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')

            for iframe in soup.find_all('iframe'):
                src = iframe.get('src') or iframe.get('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    if src.startswith('http'):
                        urls_to_try.append(src)

            matches = re.findall(r'(https?://[^\s\'"]+\.(?:m3u8|mp4)[^\s\'"]*)', html)
            for m in matches:
                if m not in urls_to_try:
                    urls_to_try.append(m)

        except Exception:
            pass
        return urls_to_try

    def run_downloader(self, raw_url):
        self.status_label.configure(text="جاري فحص واستخراج مشغل الفيديو...", text_color="#00E6FF")
        target_dir = self.download_path.get()
        is_audio_only = self.format_choice.get() == "audio"

        output_template = os.path.join(target_dir, '%(title).80s [%(height)sp] [%(id)s].%(ext)s')
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        
        base_opts = {
            'outtmpl': output_template,
            'overwrites': False,
            'nooverwrites': False,
            'progress_hooks': [self.progress_callback],
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'legacyserverconnect': True,
            'geo_bypass': True,
            'continuedl': False,
            'user_agent': user_agent,
            'referer': raw_url,
            'http_headers': {
                'User-Agent': user_agent,
                'Referer': raw_url,
                'Origin': raw_url.split('/')[0] + '//' + raw_url.split('/')[2] if '://' in raw_url else raw_url,
                'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            },
            'concurrent_fragment_downloads': 5,
        }

        if FFMPEG_PATH:
            base_opts['ffmpeg_location'] = FFMPEG_PATH

        if is_audio_only:
            base_opts.update({
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(target_dir, '%(title).80s [Audio] [%(id)s].%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            quality_selected = self.quality_choice.get()
            if quality_selected == "1080p":
                format_spec = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
            elif quality_selected == "720p":
                format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            elif quality_selected == "480p":
                format_spec = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
            elif quality_selected == "360p":
                format_spec = "bestvideo[height<=360]+bestaudio/best[height<=360]/best"
            else:
                format_spec = "bestvideo+bestaudio/best"

            base_opts.update({
                'format': format_spec,
                'merge_output_format': 'mp4',
            })

        candidate_urls = self.scan_page_for_embeds(raw_url)

        success = False
        last_error = ""

        for test_url in candidate_urls:
            if not self.is_downloading:
                return

            methods = [
                {},
                {'cookiesfrombrowser': ('chrome',)},
                {'cookiesfrombrowser': ('edge',)},
            ]

            for method in methods:
                if not self.is_downloading:
                    return
                opts = base_opts.copy()
                opts.update(method)
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([test_url])
                    success = True
                    break
                except Exception as e:
                    last_error = str(e)
                    continue

            if success:
                break

        if success and self.is_downloading:
            self.reset_ui_state("تم التحميل والحفظ بنجاح! ✅")
            messagebox.showinfo("نجاح", "تم تحميل وتصدير الملف بنجاح.")
        elif self.is_downloading:
            self.reset_ui_state("حدث خطأ أثناء التحميل ❌")
            messagebox.showerror("خطأ", f"تعذر التحميل:\n{last_error}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = MoYahiaDownloader()
    app.mainloop()