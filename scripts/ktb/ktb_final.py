#!/usr/bin/env python3
"""Kick the Boss 3.0.0: final tidy-up and final build.

 1. Checks that the bundled game is the finished Russian build and that game.version matches it.
 2. Shell sources: removes the last investigation trace (Stage 33 asset-open log in host_assets.cpp)
    and the "profileable" flag that was only there for profiling; deletes leftover *.stageNN.bak,
    *.tmp, *.zb-tmp and __pycache__ in the project.
 3. Puts the original (pre-localization) game and the scripts/patches of this work into ~/ktb_archive,
    and the working files on the Desktop into Desktop/ktb/архив_KTB (only files made in this work;
    nothing else in that folder is touched).
 4. Final build -> "Kick the Boss 3.0.0.apk" on the Desktop, with its size.

Usage: python3 ktb_final.py ~/ZettaBridge
"""
import sys, re, shutil, hashlib, zipfile, subprocess, pathlib, os
root = pathlib.Path(sys.argv[1]).expanduser()
home = pathlib.Path.home()
desk = pathlib.Path('/mnt/c/Users/Rgood/Desktop')
ktbdir = desk / 'ktb'
L = root / 'android/launcher'
bundled = L / 'app/src/kicktheboss/assets/bundled'
arch = home / 'ktb_archive'

def step(t): print('\n== ' + t)

# 1 ------------------------------------------------------------------------------------------------
step('1. bundled game')
game = bundled / 'game.apk'
names = zipfile.ZipFile(game).namelist()
assert 'assets/bin/Data/sharedassets0.assets.split25' in names, 'the bundled game is not the Russian build'
digest = hashlib.sha256(game.read_bytes()).hexdigest()
ver = (bundled / 'game.version').read_text().strip()
if ver != digest:
    (bundled / 'game.version').write_text(digest + '\n'); print('game.version fixed')
extra = [p.name for p in bundled.iterdir() if p.name not in ('game.apk', 'game.version')]
for n in extra:
    p = bundled / n
    arch.mkdir(exist_ok=True); shutil.move(str(p), arch / n); print('moved out of the app assets:', n)
print(f'game.apk {game.stat().st_size/1e6:.1f} MB, version {digest[:12]}, Russian build: ok')

# 2 ------------------------------------------------------------------------------------------------
step('2. shell sources')
ha = root / 'core/src/assets/host_assets.cpp'
s = ha.read_text()
m = re.search(r'\n        const bool managed = filename\.find\("Managed/"\).*?"guest-handle=" \+ std::to_string\(guest_manager\), true\);\n        \}\n', s, re.S)
if m and 'ktb33' in m.group(0):
    s = s[:m.start()] + '\n' + s[m.end():]
    ha.write_text(s); print('removed: Stage 33 asset-open trace (host_assets.cpp)')
else:
    print('Stage 33 trace: already gone' if 'ktb33' not in s else 'Stage 33 trace: pattern changed, left as is')
man = L / 'app/src/kicktheboss/AndroidManifest.xml'
s = man.read_text()
t = s.replace('        <!-- zb-opt-r2: release builds stay measurable with simpleperf. -->\n', '') \
     .replace('        <profileable android:shell="true" tools:targetApi="29" />\n', '')
if t != s: man.write_text(t); print('removed: profileable flag (only needed for profiling)')
else: print('profileable flag: already gone')
gone = 0
for p in list(root.rglob('*')):
    if any(x in ('.git', '.gradle', '.cxx', '.idea', 'build', 'third_party') for x in p.parts): continue
    if p.is_dir() and p.name == '__pycache__': shutil.rmtree(p, ignore_errors=True); gone += 1
    elif p.is_file() and (re.search(r'\.stage\d+\.bak$', p.name) or p.suffix in ('.tmp',) or p.name.endswith('.zb-tmp')):
        p.unlink(); gone += 1
print(f'leftover files removed: {gone}')
bk = root / '.ktb_backup'
if bk.is_dir():
    arch.mkdir(exist_ok=True)
    for p in bk.iterdir(): shutil.move(str(p), arch / ('KTB_game_original_' + p.name)); print('archived:', p.name)
    bk.rmdir()

# 3 ------------------------------------------------------------------------------------------------
step('3. archive')
arch.mkdir(exist_ok=True)
for pat in ('ktb_ru_patch*.zip', 'ktb_ru_apply*.py', 'zb_ktb_bundled_ui.py', 'ktb_final.py'):
    for p in home.glob(pat):
        if p.name == 'ktb_final.py': continue
        shutil.move(str(p), arch / p.name); print('~/' + p.name, '-> ~/ktb_archive')
da = ktbdir / 'архив_KTB'
mine = ['ktb_ru_patch*.zip', 'ktb_ru_apply*.py', 'ktb_ru_log*.txt', 'KTB_ru.apk', 'installed.apk',
        'KTB_RU_*.png', 'KTB_флаг_RU_превью.png', 'zb_ktb_bundled_ui.py', 'KTB_перевод_RU.xlsx', 'ktb_final.py']
moved = 0
for pat in mine:
    for p in ktbdir.glob(pat):
        da.mkdir(exist_ok=True); shutil.move(str(p), da / p.name); moved += 1
print(f'Desktop/ktb: {moved} working files -> архив_KTB (the current translation table stays)')

# 4 ------------------------------------------------------------------------------------------------
step('4. final build')
subprocess.run(['./gradlew', 'assembleKickthebossRelease', '-q'], cwd=L, check=True)
apk = L / 'app/build/outputs/apk/kicktheboss/release/app-kicktheboss-release.apk'
out = desk / 'Kick the Boss 3.0.0.apk'
shutil.copyfile(apk, out)
z = zipfile.ZipFile(apk)
inside = sorted(((i.compress_size, i.filename) for i in z.infolist()), reverse=True)[:3]
print(f'Desktop/Kick the Boss 3.0.0.apk: {out.stat().st_size/1e6:.1f} MB')
for sz, n in inside: print(f'   {sz/1e6:5.1f} MB  {n}')
step('git status (changes since the last commit)')
subprocess.run(['git', 'status', '--short'], cwd=root)
print('\ndone')
