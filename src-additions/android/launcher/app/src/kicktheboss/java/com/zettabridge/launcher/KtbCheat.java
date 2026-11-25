package com.zettabridge.launcher;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.SystemClock;
import android.util.Log;
import android.view.KeyEvent;
import android.view.Window;
import android.widget.Toast;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

/**
 * Kick the Boss secret: volume down, down, up, up (within 4 s) unlocks the purchases that were
 * made for real money in the original game. Google's old billing service the game used is gone,
 * so com.prime31.IABPlugin (our stand-in) then answers a purchase by granting it, which runs the
 * game's own reward code: alert, coin animation and the purchase sound. Session only.
 *
 * Key presses are seen through a Window.Callback wrapper; the system volume broadcast is a
 * fallback for windows whose keys do not reach it. Neither consumes the key: volume still changes.
 */
public final class KtbCheat {
    private static final String TAG = "zb-ktb";
    private static final long WINDOW_MS = 4000;
    private static final int[] CODE = {-1, -1, +1, +1};

    private static volatile boolean unlocked;
    private static volatile ClassLoader gameLoader;
    private static volatile Activity current;
    private static final int[] recent = new int[4];
    private static final long[] recentAt = new long[4];
    private static int count;
    private static long lastKeyAt;
    private static boolean receiverRegistered;

    private KtbCheat() {}

    public static boolean unlocked() {
        return unlocked;
    }

    /** Called (by reflection) from GuestInstrumentation after every plugin activity's onCreate. */
    public static void attach(Activity activity) {
        if (!activity.getClass().getName().startsWith("com.unity3d.player.")) return;
        current = activity;
        gameLoader = activity.getClassLoader();
        wrapWindow(activity);
        registerVolumeReceiver(activity.getApplicationContext());
    }

    private static void wrapWindow(Activity activity) {
        Window window = activity.getWindow();
        if (window == null) return;
        final Window.Callback base = window.getCallback();
        if (base == null || Proxy.isProxyClass(base.getClass())) return;
        Window.Callback wrapped = (Window.Callback) Proxy.newProxyInstance(Window.Callback.class.getClassLoader(),
                new Class<?>[] {Window.Callback.class}, (proxy, method, args) -> {
                    if ("dispatchKeyEvent".equals(method.getName()) && args != null && args[0] instanceof KeyEvent) {
                        onKeyEvent((KeyEvent) args[0]);
                    }
                    try {
                        return method.invoke(base, args);
                    } catch (InvocationTargetException e) {
                        throw e.getCause();
                    }
                });
        window.setCallback(wrapped);
    }

    private static void onKeyEvent(KeyEvent event) {
        if (event.getAction() != KeyEvent.ACTION_DOWN || event.getRepeatCount() != 0) return;
        int code = event.getKeyCode();
        if (code == KeyEvent.KEYCODE_VOLUME_DOWN) {
            lastKeyAt = SystemClock.uptimeMillis();
            step(-1);
        } else if (code == KeyEvent.KEYCODE_VOLUME_UP) {
            lastKeyAt = SystemClock.uptimeMillis();
            step(+1);
        }
    }

    private static void registerVolumeReceiver(Context context) {
        if (receiverRegistered) return;
        receiverRegistered = true;
        BroadcastReceiver receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context c, Intent intent) {
                // Key events already counted: the broadcast is only a fallback.
                if (SystemClock.uptimeMillis() - lastKeyAt < 600) return;
                int now = intent.getIntExtra("android.media.EXTRA_VOLUME_STREAM_VALUE", -1);
                int before = intent.getIntExtra("android.media.EXTRA_PREV_VOLUME_STREAM_VALUE", -1);
                if (now < 0 || before < 0 || now == before) return;
                step(now > before ? +1 : -1);
            }
        };
        IntentFilter filter = new IntentFilter("android.media.VOLUME_CHANGED_ACTION");
        try {
            if (Build.VERSION.SDK_INT >= 33) {
                context.registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED);
            } else {
                context.registerReceiver(receiver, filter);
            }
        } catch (RuntimeException e) {
            Log.w(TAG, "volume receiver not registered", e);
        }
    }

    private static synchronized void step(int direction) {
        long t = SystemClock.uptimeMillis();
        System.arraycopy(recent, 1, recent, 0, 3);
        System.arraycopy(recentAt, 1, recentAt, 0, 3);
        recent[3] = direction;
        recentAt[3] = t;
        if (count < 4) count++;
        if (count < 4 || t - recentAt[0] > WINDOW_MS) return;
        for (int i = 0; i < 4; i++) if (recent[i] != CODE[i]) return;
        count = 0;
        toggle();
    }

    private static void toggle() {
        unlocked = !unlocked;
        Log.i(TAG, "real-money purchases " + (unlocked ? "unlocked" : "locked"));
        if (unlocked) sendToGame("billingSupported", "1");
        final Activity activity = current;
        if (activity != null) {
            activity.runOnUiThread(() -> Toast.makeText(activity,
                    unlocked ? "Покупки разблокированы" : "Покупки снова заблокированы", Toast.LENGTH_SHORT).show());
        }
    }

    /** UnityPlayer.UnitySendMessage(object, method, argument) through the game's class loader. */
    public static void sendToGame(String method, String argument) {
        try {
            ClassLoader loader = gameLoader;
            if (loader == null) return;
            Class<?> player = Class.forName("com.unity3d.player.UnityPlayer", true, loader);
            Method send = player.getMethod("UnitySendMessage", String.class, String.class, String.class);
            send.invoke(null, "IABAndroidManager", method, argument);
        } catch (Throwable t) {
            Log.w(TAG, "UnitySendMessage " + method + " failed", t);
        }
    }
}
