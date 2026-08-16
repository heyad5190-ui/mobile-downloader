[app]
title = Mo Yahia Downloader
package.name = moyahiadownloader
package.domain = org.moyahia
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,yt_dlp,beautifulsoup4,requests,urllib3,certifi,openssl

orientation = portrait
osx.kivy_version = 2.3.0
fullscreen = 0

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1