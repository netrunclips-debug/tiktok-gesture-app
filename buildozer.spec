[app]
title = TikTok Gesture Control
package.name = tiktokgesture
package.domain = org.tiktokgesture

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,xml

version = 0.1

# المكتبات المطلوبة - opencv-python متوفرة كـ recipe في python-for-android
requirements = python3,kivy==2.3.0,opencv,numpy,pyjnius

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

android.permissions = CAMERA,SYSTEM_ALERT_WINDOW,BIND_ACCESSIBILITY_SERVICE

# مجلد الكود الجافا الإضافي (خدمة الوصول Accessibility Service)
android.add_src = src

# ملفات موارد أندرويد إضافية (accessibility_service_config.xml)
android.add_resources = res

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a



[buildozer]
log_level = 2
warn_on_root = 1
