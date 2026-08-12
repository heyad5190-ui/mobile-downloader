[app]

title = Mo Yahia Downloader
package.name = moyahiadownloader
package.domain = org.moyahia

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.main = main.py

version = 1.0

requirements = python3,kivy,yt-dlp

orientation = portrait

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
