import os
import re
import urllib.request
import threading
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from bs4 import BeautifulSoup
import yt_dlp

# واجهة المستخدم بأسلوب KivyMD المتوافق مع الموبايل
KV = '''
MDScreen:
    md_bg_color: 0.12, 0.13, 0.17, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "20dp"
        spacing: "15dp"

        MDLabel:
            text: "MO YAHIA DOWNLOADER PRO"
            font_style: "H5"
            bold: True
            theme_text_color: "Custom"
            text_color: 0, 0.9, 1, 1
            size_hint_y: None
            height: self.texture_size[1]
            halign: "center"

        MDLabel:
            text: "الجيل الجديد للتحميل من جميع المنصات ومواقع البث"
            font_style: "Caption"
            theme_text_color: "Custom"
            text_color: 0.54, 0.6, 0.68, 1
            size_hint_y: None
            height: self.texture_size[1]
            halign: "center"

        MDTextField:
            id: url_input
            hint_text: "ضع رابط الفيديو أو الصفحة هنا..."
            mode: "rectangle"
            text_color_normal: 1, 1, 1, 1
            text_color_focus: 0, 0.9, 1, 1
            hint_text_color_normal: 0.54, 0.6, 0.68, 1
            line_color_focus: 0, 0.9, 1, 1

        MDBoxLayout:
            orientation: 'horizontal'
            spacing: "10dp"
            size_hint_y: None
            height: "50dp"

            MDRaisedButton:
                id: btn_video
                text: "فيديو MP4 🎬"
                md_bg_color: (0.12, 0.41, 0.64, 1) if app.format_choice == "video" else (0.18, 0.2, 0.26, 1)
                on_release: app.set_format("video")

            MDRaisedButton:
                id: btn_audio
                text: "صوت MP3 🎵"
                md_bg_color: (0.12, 0.41, 0.64, 1) if app.format_choice == "audio" else (0.18, 0.2, 0.26, 1)
                on_release: app.set_format("audio")

        MDDropDownItem:
            id: quality_drop
            text: app.quality_choice
            on_release: app.open_quality_menu()
            size_hint_x: 1

        MDLabel:
            id: status_label
            text: "جاهز لبدء التحميل"
            font_style: "Subtitle2"
            theme_text_color: "Custom"
            text_color: 0, 0.9, 1, 1
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]

        MDProgressBar:
            id: progress_bar
            value: 0
            color: 0, 0.9, 1, 1

        MDBoxLayout:
            orientation: 'horizontal'
            spacing: "10dp"
            size_hint_y: None
            height: "50dp"

            MDRaisedButton:
                id: download_btn
                text: "بدء التحميل الآن 🚀"
                md_bg_color: 0, 0.9, 1, 1
                text_color: 0, 0, 0, 1
                on_release: app.toggle_download()
                elevation: 2

            MDRaisedButton:
                id: pause_btn
                text: "إيقاف مؤقت ⏸️"
                md_bg_color: 0.17, 0.19, 0.24, 1
                disabled: True
                on_release: app.toggle_pause()
'''

class MoYahiaDownloaderApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.format_choice = "video"
        self.quality_choice = "أعلى جودة متاحة (Best)"
        self.is_downloading = False
        self.is_paused = False
        self.dialog = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.request_android_permissions()
        return Builder.load_string(KV)

    def request_android_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])

    def get_download_path(self):
        if platform == 'android':
            from android.storage import primary_external_storage_path
            return os.path.join(primary_external_storage_path(), 'Download')
        return os.path.expanduser("~/Downloads")

    def set_format(self, fmt):
        self.format_choice = fmt
        self.root.ids.btn_video.md_bg_color = (0.12, 0.41, 0.64, 1) if fmt == "video" else (0.18, 0.2, 0.26, 1)
        self.root.ids.btn_audio.md_bg_color = (0.12, 0.41, 0.64, 1) if fmt == "audio" else (0.18, 0.2, 0.26, 1)
        self.root.ids.quality_drop.disabled = (fmt == "audio")

    def open_quality_menu(self):
        qualities = ["أعلى جودة متاحة (Best)", "1080p", "720p", "480p", "360p"]
        # يمكن دمج القائمة المنسدلة للخيارات بسهولة
        pass

    def update_status(self, text, progress=None, color=None):
        def _update(dt):
            self.root.ids.status_label.text = text
            if progress is not None:
                self.root.ids.progress_bar.value = progress
        Clock.schedule_once(_update)

    def toggle_pause(self):
        if not self.is_downloading:
            return
        self.is_paused = not self.is_paused
        btn = self.root.ids.pause_btn
        if self.is_paused:
            btn.text = "استئناف ▶️"
            self.update_status("تم إيقاف التحميل مؤقتاً ⏸️")
        else:
            btn.text = "إيقاف مؤقت ⏸️"
            self.update_status("جاري استئناف التحميل...")

    def toggle_download(self):
        if not self.is_downloading:
            url = self.root.ids.url_input.text.strip()
            if not url:
                self.show_alert("تنبيه", "يرجى إدخال رابط أولاً.")
                return
            self.is_downloading = True
            self.is_paused = False
            self.root.ids.download_btn.text = "إلغاء ⏹️"
            self.root.ids.download_btn.md_bg_color = (1, 0.23, 0.19, 1)
            self.root.ids.pause_btn.disabled = False
            
            threading.Thread(target=self.run_downloader, args=(url,), daemon=True).start()
        else:
            self.is_downloading = False
            self.reset_ui("تم إلغاء التحميل.")

    def reset_ui(self, msg=""):
        def _reset(dt):
            self.is_downloading = False
            self.is_paused = False
            self.root.ids.download_btn.text = "بدء التحميل الآن 🚀"
            self.root.ids.download_btn.md_bg_color = (0, 0.9, 1, 1)
            self.root.ids.pause_btn.disabled = True
            self.root.ids.pause_btn.text = "إيقاف مؤقت ⏸️"
            if msg:
                self.root.ids.status_label.text = msg
        Clock.schedule_once(_reset)

    def progress_callback(self, d):
        while self.is_paused:
            pass
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                pct = (downloaded / total) * 100
                speed = d.get('_speed_str', 'N/A')
                self.update_status(f"جاري التحميل... {int(pct)}% | السرعة: {speed}", progress=pct)
        elif d['status'] == 'finished':
            self.update_status("جاري معالجة واستخراج الملف النهائي...", progress=100)

    def scan_page_for_embeds(self, url):
        urls = [url]
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req, timeout=7).read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src') or iframe.get('data-src')
                if src:
                    if src.startswith('//'): src = 'https:' + src
                    if src.startswith('http'): urls.append(src)
            matches = re.findall(r'(https?://[^\s\'"]+\.(?:m3u8|mp4)[^\s\'"]*)', html)
            for m in matches:
                if m not in urls: urls.append(m)
        except Exception:
            pass
        return urls

    def run_downloader(self, raw_url):
        self.update_status("جاري فحص واستخراج الفيديو...")
        target_dir = self.get_download_path()
        os.makedirs(target_dir, exist_ok=True)
        
        user_agent = 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36'
        base_opts = {
            'outtmpl': os.path.join(target_dir, '%(title).80s [%(id)s].%(ext)s'),
            'progress_hooks': [self.progress_callback],
            'quiet': True,
            'nocheckcertificate': True,
            'user_agent': user_agent,
            'referer': raw_url,
        }

        if self.format_choice == "audio":
            base_opts.update({'format': 'bestaudio/best'})
        else:
            base_opts.update({'format': 'bestvideo+bestaudio/best'})

        candidate_urls = self.scan_page_for_embeds(raw_url)
        success = False
        last_error = ""

        for test_url in candidate_urls:
            if not self.is_downloading: return
            try:
                with yt_dlp.YoutubeDL(base_opts) as ydl:
                    ydl.download([test_url])
                success = True
                break
            except Exception as e:
                last_error = str(e)

        if success and self.is_downloading:
            self.reset_ui("تم التحميل والحفظ بنجاح! ✅")
        elif self.is_downloading:
            self.reset_ui(f"خطأ: {last_error[:50]}...")

    def show_alert(self, title, message):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=message,
                buttons=[MDFlatButton(text="حسناً", on_release=lambda x: self.dialog.dismiss())]
            )
        self.dialog.text = message
        self.dialog.open()

if __name__ == "__main__":
    MoYahiaDownloaderApp().run()