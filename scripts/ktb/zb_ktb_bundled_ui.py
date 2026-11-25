#!/usr/bin/env python3
"""Kick the Boss app (kicktheboss flavour): one entry in Recents, localized "Updating the game...".

 1. The home-screen activity (BundledGameActivity) only imports/updates the bundled game and hands
    over to the game, which runs in its own task. It used to stay in Recents as a second card
    showing the "Updating the game..." screen. It is now excluded from Recents and removes its task
    when it hands over, so Recents shows only the game.
 2. "Preparing the game (first launch)..." / "Updating the game..." follow the phone language:
    English, Russian, Chinese (traditional/simplified), Japanese, Spanish, French, German, Swedish,
    Korean (the game's languages).

Note: zb_make_ktb_app.py rewrites these files; run this again after it.
Usage: python3 zb_ktb_bundled_ui.py ~/ZettaBridge
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1]).expanduser()
F = root / 'android/launcher/app/src/kicktheboss'
MAN = F / 'AndroidManifest.xml'
JAVA = F / 'java/com/zettabridge/launcher/BundledGameActivity.java'


def patch(path, pairs, marker):
    s = path.read_text(encoding='utf-8')
    if marker in s:
        print('already patched:', path.relative_to(root)); return
    for old, new in pairs:
        if s.count(old) != 1:
            sys.exit(f'{path}: anchor not found exactly once:\n{old}')
        s = s.replace(old, new)
    path.write_text(s, encoding='utf-8')
    print('patched:', path.relative_to(root))


patch(MAN, [
    ('            android:name=".BundledGameActivity"\n            android:exported="true"\n',
     '            android:name=".BundledGameActivity"\n            android:exported="true"\n'
     '            android:excludeFromRecents="true"\n'),
], 'android:excludeFromRecents="true"\n            android:screenOrientation')

patch(JAVA, [
    ('import java.nio.charset.StandardCharsets;\n',
     'import java.nio.charset.StandardCharsets;\nimport java.util.Locale;\n'),
    ('status.setText(installed == null ? "Preparing the game (first launch)..." : "Updating the game...");',
     'status.setText(progressText(installed == null));  // zb-ui: localized'),
    ('        startActivity(PluginSwitchActivity.intent(this, packageName));\n        finish();\n',
     '        startActivity(PluginSwitchActivity.intent(this, packageName));\n'
     '        finishAndRemoveTask();  // zb-ui: the game\'s own task is the only one in Recents\n'),
    ('    private String readAsset(String name) throws IOException {',
     '''    /** zb-ui: the progress line in the phone language (the game's ten languages, else English). */
    private static String progressText(boolean firstLaunch) {
        Locale l = Locale.getDefault();
        String lang = l.getLanguage();
        if ("zh".equals(lang)) {
            String script = l.getScript();
            String country = l.getCountry();
            boolean hant = "Hant".equals(script) || (script.isEmpty()
                    && ("TW".equals(country) || "HK".equals(country) || "MO".equals(country)));
            lang = hant ? "zh-Hant" : "zh-Hans";
        }
        switch (lang) {
            case "ru": return firstLaunch ? "Подготовка игры (первый запуск)..." : "Обновление игры...";
            case "zh-Hant": return firstLaunch ? "正在準備遊戲（首次啟動）..." : "正在更新遊戲...";
            case "zh-Hans": return firstLaunch ? "正在准备游戏（首次启动）..." : "正在更新游戏...";
            case "ja": return firstLaunch ? "ゲームを準備しています（初回起動）..." : "ゲームを更新しています...";
            case "es": return firstLaunch ? "Preparando el juego (primer inicio)..." : "Actualizando el juego...";
            case "fr": return firstLaunch ? "Préparation du jeu (premier lancement)..." : "Mise à jour du jeu...";
            case "de": return firstLaunch ? "Spiel wird vorbereitet (erster Start)..." : "Spiel wird aktualisiert...";
            case "sv": return firstLaunch ? "Förbereder spelet (första start)..." : "Uppdaterar spelet...";
            case "ko": return firstLaunch ? "게임 준비 중 (첫 실행)..." : "게임 업데이트 중...";
            default: return firstLaunch ? "Preparing the game (first launch)..." : "Updating the game...";
        }
    }

    private String readAsset(String name) throws IOException {'''),
], 'zb-ui')
print('done')
