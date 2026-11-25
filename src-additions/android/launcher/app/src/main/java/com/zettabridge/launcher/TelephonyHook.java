package com.zettabridge.launcher;

import android.content.Context;
import android.os.IBinder;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.util.Log;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

/**
 * Telephony identifier virtualization for the :guest process. Android 10+ throws SecurityException
 * when a normal app asks for the IMEI, subscriber id or SIM serial; games written before that
 * (World War Z logs getDeviceId() at start-up) die on it. The "phone" and "iphonesubinfo" binder
 * interfaces are wrapped so that an identifier call the system refuses answers a stable fake id.
 */
final class TelephonyHook implements InvocationHandler {
    private static final String TAG = "zb-launcher";

    private final Object real;
    private final String fakeId;

    private TelephonyHook(Object real, String fakeId) {
        this.real = real;
        this.fakeId = fakeId;
    }

    static void install(Context host) {
        String fake = fakeId(host);
        int hooked = 0;
        hooked += hook("phone", "com.android.internal.telephony.ITelephony", fake);
        hooked += hook("iphonesubinfo", "com.android.internal.telephony.IPhoneSubInfo", fake);
        Log.i(TAG, "telephony identifiers virtualized: " + hooked + " service(s)");
        try {
            TelephonyManager tm = (TelephonyManager) host.getSystemService(Context.TELEPHONY_SERVICE);
            Object id = Reflect.method(TelephonyManager.class, "getDeviceId").invoke(tm);
            Log.i(TAG, "telephony self-test: getDeviceId ok (" + (id != null ? "id" : "null") + ")");
        } catch (InvocationTargetException e) {
            Log.w(TAG, "telephony self-test: getDeviceId still fails: " + e.getCause());
        } catch (ReflectiveOperationException | RuntimeException e) {
            Log.w(TAG, "telephony self-test unavailable: " + e);
        }
    }

    private static int hook(String service, String iface, String fake) {
        try {
            Class<?> sm = Class.forName("android.os.ServiceManager");
            IBinder binder = (IBinder) Reflect.method(sm, "getService", String.class).invoke(null, service);
            if (binder == null) return 0;
            if (Proxy.isProxyClass(binder.getClass())) return 1;
            Class<?> itf = Class.forName(iface);
            Class<?> stub = Class.forName(iface + "$Stub");
            Object realItf = Reflect.method(stub, "asInterface", IBinder.class).invoke(null, binder);
            if (realItf == null) return 0;
            final Object hooked = Proxy.newProxyInstance(itf.getClassLoader(), new Class<?>[] {itf},
                    new TelephonyHook(realItf, fake));
            final IBinder realBinder = binder;
            IBinder wrapped = (IBinder) Proxy.newProxyInstance(IBinder.class.getClassLoader(),
                    new Class<?>[] {IBinder.class}, (p, m, a) -> {
                        if ("queryLocalInterface".equals(m.getName()) && a != null && iface.equals(a[0])) {
                            return hooked;
                        }
                        try {
                            return m.invoke(realBinder, a);
                        } catch (InvocationTargetException e) {
                            throw e.getCause();
                        }
                    });
            @SuppressWarnings("unchecked")
            Map<String, IBinder> cache = (Map<String, IBinder>) Reflect.field(sm, "sCache").get(null);
            cache.put(service, wrapped);
            // TelephonyManager keeps its own static copies of the interfaces on recent releases.
            for (Field f : TelephonyManager.class.getDeclaredFields()) {
                if (Modifier.isStatic(f.getModifiers()) && f.getType() == itf) {
                    f.setAccessible(true);
                    f.set(null, hooked);
                }
            }
            return 1;
        } catch (ReflectiveOperationException | RuntimeException e) {
            Log.w(TAG, "cannot virtualize telephony service " + service + ": " + e);
            return 0;
        }
    }

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        try {
            return method.invoke(real, args);
        } catch (InvocationTargetException e) {
            Throwable cause = e.getCause();
            if (cause instanceof SecurityException && method.getReturnType() == String.class
                    && isIdentifier(method.getName())) {
                return fakeId;
            }
            throw cause;
        }
    }

    private static boolean isIdentifier(String name) {
        return name.contains("DeviceId") || name.contains("Imei") || name.contains("Meid")
                || name.contains("SubscriberId") || name.contains("IccSerial") || name.contains("SimSerial");
    }

    /** 15 digits (IMEI-sized), stable for this device and app. */
    private static String fakeId(Context c) {
        String seed = null;
        try {
            seed = Settings.Secure.getString(c.getContentResolver(), Settings.Secure.ANDROID_ID);
        } catch (RuntimeException ignored) {
            // fall back to a fixed seed
        }
        if (seed == null) seed = "zettabridge";
        UUID u = UUID.nameUUIDFromBytes(("zb-imei:" + seed).getBytes(StandardCharsets.UTF_8));
        long v = (u.getMostSignificantBits() ^ u.getLeastSignificantBits()) & Long.MAX_VALUE;
        return String.format(Locale.US, "%015d", v % 1_000_000_000_000_000L);
    }
}
