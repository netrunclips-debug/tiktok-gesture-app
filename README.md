# تطبيق التحكم بـ TikTok عبر الإيماءات (Wink / Smile / Mouth Open)

## ⚠️ اقرأ هذا أولًا

هذا المشروع **كود مصدري كامل** تبنيه أنت بنفسك على جهازك (لابتوب/PC فيه
إنترنت). لا يمكن تسليمه كملف APK جاهز من هذه المحادثة لأن البناء يحتاج
Android SDK/NDK حقيقي واتصال إنترنت لتحميل عشرات الميجابايت من الأدوات،
وهذا غير متاح في بيئة تنفيذ الكود هنا.

**تنبيه استخدام:** التحكم الآلي بالسحب/اللايك داخل TikTok قد يخالف شروط
استخدام التطبيق، وقد يُعرّض حسابك للتقييد إذا استُخدم بكثافة أو بشكل آلي
واضح. استخدمه على مسؤوليتك الخاصة، ويُفضّل تجربته أولًا في وضع اختباري.

---

## بنية المشروع

```
tiktok_gesture_app/
├── main.py                          # تطبيق Kivy: كشف الإيماءات عبر الكاميرا
├── buildozer.spec                   # إعدادات البناء لأندرويد
├── src/org/tiktokgesture/app/
│   └── GestureAccessibilityService.java   # خدمة تنفّذ السحب الفعلي في TikTok
├── res/xml/
│   └── accessibility_service_config.xml   # تعريف خدمة الوصول لأندرويد
└── README.md                        # هذا الملف
```

---

## المرحلة 1: تجهيز بيئة البناء (على جهازك، وليس هنا)

يلزمك جهاز Linux أو WSL على ويندوز (Buildozer لا يعمل على ويندوز مباشرة):

```bash
sudo apt update
sudo apt install -y python3-pip build-essential git python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
    zlib1g-dev openjdk-17-jdk unzip

pip3 install --user buildozer cython==0.29.36
```

انسخ مجلد المشروع `tiktok_gesture_app` إلى جهازك، وادخل إليه:

```bash
cd tiktok_gesture_app
```

## المرحلة 2: أول بناء تجريبي (بدون خدمة Accessibility بعد)

```bash
buildozer android debug
```

أول مرة سيحمّل Buildozer تلقائيًا Android SDK وNDK (قد يأخذ 20-40 دقيقة
حسب سرعة الإنترنت). عند الانتهاء ستجد الملف هنا:

```
bin/tiktokgesture-0.1-arm64-v8a-debug.apk
```

ثبّته على جهازك وجرّب أن الكاميرا تعمل وتظهر رسائل كشف الإيماءات
("غمزة يمنى -> سكرول لأسفل" ... إلخ) في شريط الحالة أعلى الشاشة —
هذا يؤكد أن جزء الرؤية الحاسوبية يعمل، حتى قبل ربطه بـ TikTok فعليًا.

## المرحلة 3: دمج خدمة Accessibility (الجزء الذي ينفذ السحب الفعلي)

Buildozer يضيف تلقائيًا كود Java من مجلد `src/` بفضل السطر:
```
android.add_src = src
```
لكن **تعريف الخدمة داخل AndroidManifest.xml لازم نضيفه يدويًا**، لأن
buildozer لا يوفر خيارًا مباشرًا لإضافة وسم `<service>` كامل.

### الخطوات:

1. بعد أول `buildozer android debug` ناجح، افتح ملف المانفست الناتج:
```
.buildozer/android/platform/build-<arch>/dists/tiktokgesture/src/main/AndroidManifest.xml
```

2. أضف داخل وسم `<application>` هذا المقطع:
```xml
<service
    android:name="org.tiktokgesture.app.GestureAccessibilityService"
    android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
    android:exported="true">
    <intent-filter>
        <action android:name="android.accessibilityservice.AccessibilityService" />
    </intent-filter>
    <meta-data
        android:name="android.accessibilityservice"
        android:resource="@xml/accessibility_service_config" />
</service>
```

3. انسخ `res/xml/accessibility_service_config.xml` إلى:
```
.buildozer/android/platform/build-<arch>/dists/tiktokgesture/src/main/res/xml/
```

4. أضف سلسلة النص المطلوبة في:
```
.../src/main/res/values/strings.xml
```
```xml
<string name="accessibility_service_description">
    يسمح هذا التطبيق بالتحكم في التمرير والإعجاب عبر إيماءات الوجه.
</string>
```

5. أعد البناء:
```bash
buildozer android debug
```

> ملاحظة: `buildozer android clean` قد يمسح هذه التعديلات اليدوية لأنها
> تُعاد توليدها من القوالب الأصلية. إذا أردت حلاً دائمًا وأكثر احترافية،
> الخيار الأفضل هو فتح المشروع المُولَّد داخل Android Studio مباشرة
> والاستمرار في البناء من هناك بدل Buildozer، أو تحويل المشروع بالكامل
> إلى Kotlin أصلي (بإمكاني كتابته لك إذا رغبت لاحقًا).

## المرحلة 4: تفعيل الخدمة على الجهاز

بعد تثبيت الـ APK المُحدَّث:

1. **الإعدادات ⚙️ -> إمكانية الوصول (Accessibility)**
2. ابحث عن **"TikTok Gesture Control"**
3. فعّلها ووافق على الصلاحيات

## المرحلة 5: الاستخدام

1. افتح تطبيق TikTok وابدأ بمشاهدة الـ Reels
2. افتح تطبيقنا في الخلفية (أو صغّره فوق TikTok إن أمكن باستخدام
   نافذة عائمة — هذا تحسين مستقبلي)
3. الإيماءات:
   - 👁️ غمزة العين اليمنى → سكرول لأسفل (الفيديو التالي)
   - 👁️ غمزة العين اليسرى → سكرول لأعلى (الفيديو السابق)
   - 👄 فتح الفم بشكل واضح → لايك
   - 😊 ابتسامة مستمرة لثانية → لايك

---

## قيود معروفة وتحسينات مستقبلية

- **الدقة**: نستخدم Haar Cascades (مدمجة مع OpenCV) وهي بسيطة وسريعة لكن
  أقل دقة من حلول حديثة مثل **MediaPipe Face Mesh**. إذا أردت دقة أعلى
  لاحقًا، الخيار الأفضل تطبيق Kotlin أصلي مع MediaPipe (أدق بكثير في
  تمييز الغمزة عن الرمش الطبيعي، وفتح الفم عن الابتسامة).
- **العمل في الخلفية فوق TikTok**: النسخة الحالية تتطلب أن يكون تطبيقنا
  ظاهرًا (الكاميرا تعمل من خلاله). لتشغيله كطبقة عائمة صغيرة فوق TikTok
  نحتاج `SYSTEM_ALERT_WINDOW` + Foreground Service — يمكن إضافته لاحقًا.
- **البطارية/الحرارة**: تشغيل كاميرا مستمر + معالجة صور كل ثانية يستهلك
  بطارية بشكل ملحوظ.

---

## هل تريد التالي؟

أقدر أساعدك بأي من:
1. تطوير النافذة العائمة فوق TikTok (Foreground Service + عرض الكاميرا كدائرة صغيرة)
2. الترقية لـ MediaPipe لدقة أعلى
3. تحويل كامل المشروع لـ Kotlin أصلي لثبات أكبر
