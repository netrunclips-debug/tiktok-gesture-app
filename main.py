# -*- coding: utf-8 -*-
"""
تطبيق التحكم بالإيماءات (Wink / Smile / Mouth Open)
================================================================
- غمزة العين اليمنى  -> سكرول لأسفل (Reel التالي)
- غمزة العين اليسرى  -> سكرول لأعلى (Reel السابق)
- فتح الفم           -> لايك (ضغطة مزدوجة على الشاشة)
- ابتسامة طويلة      -> لايك (نفس فعل اللايك)

ملاحظة مهمة:
هذا الملف يتكفل فقط بجزء "الرؤية الحاسوبية" (كشف الإيماءات عبر الكاميرا).
تنفيذ السحب الفعلي داخل تطبيق TikTok يتم عبر AccessibilityService
(انظر ملف service/GestureAccessibilityService.java وREADME).
"""

import time
import cv2
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.graphics.texture import Texture
from kivy.utils import platform

# ---------------------------------------------------------------
# محاولة الجسر مع أندرويد (pyjnius) لإرسال أوامر إلى AccessibilityService
# ---------------------------------------------------------------
ANDROID = platform == "android"
if ANDROID:
    from jnius import autoclass, cast
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")


def send_gesture_command(command: str):
    """
    يرسل أمر (SWIPE_UP / SWIPE_DOWN / LIKE) إلى GestureAccessibilityService
    عبر Broadcast Intent يستقبله الـ Service على جانب Java/Kotlin.
    """
    if not ANDROID:
        print(f"[محاكاة - غير أندرويد] سيتم تنفيذ: {command}")
        return
    try:
        activity = PythonActivity.mActivity
        intent = Intent("org.tiktokgesture.app.ACTION_GESTURE")
        intent.putExtra("command", command)
        activity.sendBroadcast(intent)
    except Exception as e:
        print("خطأ في إرسال الأمر إلى الخدمة:", e)


# ---------------------------------------------------------------
# كاشفات OpenCV (Haar Cascades) - مضمّنة افتراضيًا مع مكتبة cv2
# ---------------------------------------------------------------
FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
EYE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)
SMILE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_smile.xml"
)


class GestureDetector:
    """
    منطق كشف الإيماءات مع مهلات زمنية (debounce) لمنع تكرار نفس
    الأمر عشرات المرات في الثانية.
    """

    def __init__(self):
        self.last_action_time = 0
        self.cooldown = 1.2  # ثانية بين كل أمر وآخر
        self.mouth_open_start = None
        self.smile_start = None

    def _cooldown_ok(self):
        return (time.time() - self.last_action_time) > self.cooldown

    def process(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5, minSize=(120, 120))

        status_text = "لا يوجد وجه"
        if len(faces) == 0:
            return status_text

        # نأخذ أكبر وجه مكتشف
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        face_gray = gray[y:y + h, x:x + w]

        # -------- تقسيم الوجه لنصفين لكشف الغمز (يمين/يسار) --------
        half_w = w // 2
        left_half = face_gray[0:int(h * 0.6), 0:half_w]     # يسار الصورة = عين المستخدم اليمنى (مرآة)
        right_half = face_gray[0:int(h * 0.6), half_w:w]    # يمين الصورة = عين المستخدم اليسرى (مرآة)

        eyes_left = EYE_CASCADE.detectMultiScale(left_half, 1.1, 6, minSize=(20, 20))
        eyes_right = EYE_CASCADE.detectMultiScale(right_half, 1.1, 6, minSize=(20, 20))

        left_open = len(eyes_left) > 0
        right_open = len(eyes_right) > 0

        # -------- كشف الفم (الجزء السفلي من الوجه) --------
        mouth_region = face_gray[int(h * 0.55):h, 0:w]
        smiles = SMILE_CASCADE.detectMultiScale(
            mouth_region, scale_factor := 1.7, min_neighbors := 22, minSize=(int(w * 0.3), int(h * 0.15))
        )
        mouth_detected = len(smiles) > 0

        # فتح الفم نقيسه بنسبة العرض/الارتفاع التقريبية لأكبر منطقة مكتشفة
        mouth_wide_open = False
        if mouth_detected:
            (mx, my, mw, mh) = max(smiles, key=lambda s: s[2] * s[3])
            aspect = mh / float(mw)
            mouth_wide_open = aspect > 0.45  # فم مفتوح عموديًا أكثر من ابتسامة عادية

        now = time.time()

        # ---------------- منطق اتخاذ القرار ----------------
        if left_open and not right_open and self._cooldown_ok():
            status_text = "غمزة يسرى -> سكرول لأعلى"
            send_gesture_command("SWIPE_UP")
            self.last_action_time = now

        elif right_open and not left_open and self._cooldown_ok():
            status_text = "غمزة يمنى -> سكرول لأسفل"
            send_gesture_command("SWIPE_DOWN")
            self.last_action_time = now

        elif mouth_wide_open:
            if self.mouth_open_start is None:
                self.mouth_open_start = now
            elif self._cooldown_ok():
                status_text = "فم مفتوح -> لايك"
                send_gesture_command("LIKE")
                self.last_action_time = now
                self.mouth_open_start = None
        else:
            self.mouth_open_start = None

        if mouth_detected and not mouth_wide_open:
            if self.smile_start is None:
                self.smile_start = now
            elif now - self.smile_start > 1.0 and self._cooldown_ok():
                status_text = "ابتسامة طويلة -> لايك"
                send_gesture_command("LIKE")
                self.last_action_time = now
                self.smile_start = None
        else:
            self.smile_start = None

        if status_text == "لا يوجد وجه" and len(faces) > 0:
            status_text = "وجه مكتشف - بانتظار إيماءة"

        return status_text


class GestureRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.status_label = Label(
            text="جارٍ تشغيل الكاميرا...",
            size_hint=(1, 0.12),
            font_size="20sp",
        )
        self.add_widget(self.status_label)

        self.camera = Camera(play=True, resolution=(640, 480), index=0)
        self.add_widget(self.camera)

        self.detector = GestureDetector()
        Clock.schedule_interval(self.update, 1.0 / 12.0)  # 12 إطار/ثانية كافٍ لكشف الإيماءات

    def update(self, dt):
        if not self.camera.texture:
            return
        texture = self.camera.texture
        size = texture.size
        pixels = texture.pixels

        frame = np.frombuffer(pixels, dtype=np.uint8).reshape(size[1], size[0], 4)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        frame_bgr = cv2.flip(frame_bgr, 0)  # تصحيح اتجاه الكاميرا الأمامية

        status = self.detector.process(frame_bgr)
        self.status_label.text = status


class TikTokGestureApp(App):
    def build(self):
        self.title = "تحكم TikTok بالإيماءات"
        return GestureRoot()


if __name__ == "__main__":
    TikTokGestureApp().run()
