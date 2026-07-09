package org.tiktokgesture.app;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Path;
import android.os.Build;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;

/**
 * خدمة وصول (Accessibility Service) تستقبل أوامر من تطبيق بايثون (Kivy)
 * عبر Broadcast وتحوّلها إلى إيماءات سحب/لمس فعلية على الشاشة
 * (تعمل فوق أي تطبيق مفتوح حاليًا، بما فيه TikTok).
 *
 * يجب على المستخدم تفعيل هذه الخدمة يدويًا من:
 * الإعدادات -> إمكانية الوصول (Accessibility) -> TikTok Gesture Control -> تفعيل
 */
public class GestureAccessibilityService extends AccessibilityService {

    private static final String TAG = "GestureA11yService";
    public static final String ACTION_GESTURE = "org.tiktokgesture.app.ACTION_GESTURE";

    private BroadcastReceiver receiver;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        Log.i(TAG, "تم الاتصال بخدمة الوصول");

        receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                String command = intent.getStringExtra("command");
                if (command == null) return;

                switch (command) {
                    case "SWIPE_DOWN":
                        performSwipe(true);
                        break;
                    case "SWIPE_UP":
                        performSwipe(false);
                        break;
                    case "LIKE":
                        performDoubleTapLike();
                        break;
                }
            }
        };
        registerReceiver(receiver, new IntentFilter(ACTION_GESTURE));
    }

    /**
     * ينفذ سحبة عمودية على الشاشة تحاكي تمرير Reel التالي/السابق.
     * goDown = true  -> سحب من الأسفل للأعلى (ينتقل لفيديو تالي، مثل سلوك TikTok)
     * goDown = false -> سحب من الأعلى للأسفل (يرجع لفيديو سابق)
     */
    private void performSwipe(boolean goDown) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return;

        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        int screenHeight = getResources().getDisplayMetrics().heightPixels;
        int centerX = screenWidth / 2;

        float startY = goDown ? screenHeight * 0.75f : screenHeight * 0.25f;
        float endY = goDown ? screenHeight * 0.25f : screenHeight * 0.75f;

        Path path = new Path();
        path.moveTo(centerX, startY);
        path.lineTo(centerX, endY);

        GestureDescription.StrokeDescription stroke =
                new GestureDescription.StrokeDescription(path, 0, 250);

        GestureDescription gesture = new GestureDescription.Builder()
                .addStroke(stroke)
                .build();

        dispatchGesture(gesture, null, null);
    }

    /** ينفذ ضغطتين متتاليتين سريعتين في وسط الشاشة (لايك على TikTok) */
    private void performDoubleTapLike() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return;

        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        int screenHeight = getResources().getDisplayMetrics().heightPixels;

        Path path = new Path();
        path.moveTo(screenWidth / 2f, screenHeight / 2f);

        GestureDescription.StrokeDescription tap1 =
                new GestureDescription.StrokeDescription(path, 0, 50);
        dispatchGesture(new GestureDescription.Builder().addStroke(tap1).build(), null, null);

        GestureDescription.StrokeDescription tap2 =
                new GestureDescription.StrokeDescription(path, 120, 50);
        dispatchGesture(new GestureDescription.Builder().addStroke(tap2).build(), null, null);
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // لسنا بحاجة لمعالجة أحداث الوصول هنا، فقط نستخدم الخدمة لإرسال الإيماءات
    }

    @Override
    public void onInterrupt() {
        Log.w(TAG, "تم مقاطعة خدمة الوصول");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (receiver != null) {
            unregisterReceiver(receiver);
        }
    }
}
