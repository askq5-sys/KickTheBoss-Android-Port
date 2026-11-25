#!/usr/bin/env python3
# ZettaBridge: add a "kicktheboss" product flavor - a standalone app with the game bundled inside.
#   library     : the normal ZettaBridge launcher (unchanged behaviour)
#   kicktheboss : applicationId com.zettabridge.kicktheboss, label/icon of the game, opens the game
#                 directly; the bundled APK is imported on first launch and re-imported only when
#                 it changes. The plugin "data" dir (saves) survives re-imports.
# Usage: python3 zb_make_ktb_app.py ~/ZettaBridge /path/to/KTB_Stage43.apk
import sys, pathlib, hashlib, zipfile, shutil
root = pathlib.Path(sys.argv[1]).expanduser()
game = pathlib.Path(sys.argv[2]).expanduser()
L = root / 'android/launcher'
APP = L / 'app'

def patch(path, old, new, count=1):
    s = path.read_text()
    if new in s:
        print('already patched:', path.relative_to(root)); return
    if s.count(old) != count:
        sys.exit('pattern found %d times (want %d) in %s: %s' % (s.count(old), count, path, old[:60]))
    path.write_text(s.replace(old, new))
    print('patched:', path.relative_to(root))

# 1. Gradle flavors
patch(APP / 'build.gradle.kts',
"""    compileOptions {""",
"""    flavorDimensions += "app"
    productFlavors {
        // The general launcher: import any APK, library screen.
        create("library") {
            dimension = "app"
        }
        // One game bundled inside (src/kicktheboss/assets/bundled/game.apk, kept out of git).
        create("kicktheboss") {
            dimension = "app"
            applicationId = "com.zettabridge.kicktheboss"
            versionName = "2.64-zb"
        }
    }
    androidResources {
        noCompress += listOf("apk")
    }
    compileOptions {""")

# 2. Task affinities follow the application id, so both apps can be installed side by side.
man = APP / 'src/main/AndroidManifest.xml'
s = man.read_text()
if 'android:taskAffinity="com.zettabridge.launcher.' in s:
    s = s.replace('android:taskAffinity="com.zettabridge.launcher.switch"', 'android:taskAffinity="${applicationId}.switch"')
    s = s.replace('android:taskAffinity="com.zettabridge.launcher.guest"', 'android:taskAffinity="${applicationId}.guest"')
    man.write_text(s); print('patched: task affinities')
else:
    print('already patched: task affinities')

# 3. PluginStore: import from any stream (the bundled asset), not only from a picked Uri.
patch(APP / 'src/main/java/com/zettabridge/launcher/PluginStore.java',
"""    static PluginRecord importApk(Context c, Uri uri) throws IOException {
        File tmp = File.createTempFile("zb-import-", ".apk", c.getCacheDir());
        try (InputStream in = c.getContentResolver().openInputStream(uri)) {
            if (in == null) throw new IOException("cannot open " + uri);
            copy(in, tmp);
        }
        PackageManager pm = c.getPackageManager();""",
"""    static PluginRecord importApk(Context c, Uri uri) throws IOException {
        InputStream in = c.getContentResolver().openInputStream(uri);
        if (in == null) throw new IOException("cannot open " + uri);
        return importStream(c, in);
    }

    /** Imports the APK read from source, which is closed here. Used for picked files and bundled games. */
    static PluginRecord importStream(Context c, InputStream source) throws IOException {
        File tmp = File.createTempFile("zb-import-", ".apk", c.getCacheDir());
        try (InputStream in = source) {
            copy(in, tmp);
        } catch (IOException e) {
            tmp.delete();
            throw e;
        }
        PackageManager pm = c.getPackageManager();""")

# 4. Flavor sources
F = APP / 'src/kicktheboss'
(F / 'java/com/zettabridge/launcher').mkdir(parents=True, exist_ok=True)
(F / 'AndroidManifest.xml').write_text("""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <application
        android:label="Kick the Boss"
        android:icon="@mipmap/ic_launcher"
        tools:replace="android:label,android:icon">
        <!-- No library screen on the home screen: the bundled game is the app. -->
        <activity
            android:name=".LibraryActivity"
            android:exported="false"
            tools:node="replace" />
        <activity
            android:name=".BundledGameActivity"
            android:exported="true"
            android:screenOrientation="sensorLandscape"
            android:theme="@android:style/Theme.Material.NoActionBar.Fullscreen">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""")
(F / 'java/com/zettabridge/launcher/BundledGameActivity.java').write_text("""package com.zettabridge.launcher;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Home-screen entry of a single-game build. The game APK ships as an asset; it is imported through
 * the normal plugin import on first launch and again only when the bundled copy changes (its
 * version file differs). Import keeps the plugin's data directory, so saves survive updates.
 */
public class BundledGameActivity extends Activity {
    private static final String ASSET_APK = "bundled/game.apk";
    private static final String ASSET_VERSION = "bundled/game.version";
    private static final String PREFS = "bundled-game";

    private TextView status;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        final String wanted;
        try {
            wanted = readAsset(ASSET_VERSION).trim();
        } catch (IOException e) {
            fail("The game is not bundled in this build: " + e.getMessage());
            return;
        }
        final SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        final String pkg = prefs.getString("package", null);
        final PluginRecord installed = pkg != null ? PluginStore.find(this, pkg) : null;
        if (installed != null && installed.isLaunchable() && wanted.equals(prefs.getString("version", null))) {
            launch(pkg);
            return;
        }
        status = new TextView(this);
        status.setTextColor(Color.WHITE);
        status.setBackgroundColor(Color.BLACK);
        status.setGravity(Gravity.CENTER);
        status.setTextSize(18);
        status.setText(installed == null ? "Preparing the game (first launch)..." : "Updating the game...");
        setContentView(status);
        new Thread(() -> {
            try {
                PluginRecord r = PluginStore.importStream(this, getAssets().open(ASSET_APK));
                prefs.edit().putString("package", r.packageName).putString("version", wanted).commit();
                runOnUiThread(() -> launch(r.packageName));
            } catch (Exception e) {
                runOnUiThread(() -> fail("Cannot prepare the game: " + e));
            }
        }, "zb-bundled-import").start();
    }

    private void launch(String packageName) {
        startActivity(PluginSwitchActivity.intent(this, packageName));
        finish();
    }

    private void fail(String message) {
        Diagnostics.report(this, message, null, false);
        TextView t = status != null ? status : new TextView(this);
        t.setText(message + "\\n\\nTap to open the ZettaBridge library.");
        t.setOnClickListener(v -> {
            startActivity(new Intent(this, LibraryActivity.class));
            finish();
        });
        if (status == null) {
            t.setGravity(Gravity.CENTER);
            setContentView(t);
        }
    }

    private String readAsset(String name) throws IOException {
        try (InputStream in = getAssets().open(name)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[256];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            return new String(out.toByteArray(), StandardCharsets.US_ASCII);
        }
    }
}
""")
print('wrote: src/kicktheboss (manifest, BundledGameActivity)')

# 5. Bundled game + version + icons (out of git)
A = F / 'assets/bundled'
A.mkdir(parents=True, exist_ok=True)
shutil.copyfile(game, A / 'game.apk')
digest = hashlib.sha256(game.read_bytes()).hexdigest()
(A / 'game.version').write_text(digest + '\n')
z = zipfile.ZipFile(game)
for src, dens in [('res/drawable/app_icon.png', 'mdpi'), ('res/drawable-hdpi/app_icon.png', 'hdpi'),
                  ('res/drawable-xhdpi/app_icon.png', 'xhdpi'), ('res/drawable-ldpi/app_icon.png', 'ldpi')]:
    if src in z.namelist():
        d = F / ('res/mipmap-' + dens); d.mkdir(parents=True, exist_ok=True)
        (d / 'ic_launcher.png').write_bytes(z.read(src))
print('bundled:', game.name, 'version', digest[:16])

gi = root / '.gitignore'
line = 'android/launcher/app/src/kicktheboss/assets/'
g = gi.read_text() if gi.exists() else ''
if line not in g:
    gi.write_text(g.rstrip('\n') + '\n# bundled game APK: copyrighted, never commit\n' + line + '\n')
    print('patched: .gitignore')
print('done')
