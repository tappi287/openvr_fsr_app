# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import get_package_paths

block_cipher = None
excluded_modules = list()

# ----- define app name
APP_NAME = 'openvr_fsr_app'

# ----- locate eel.js
eel_js = get_package_paths('eel')[-1] + '\\eel.js'

# ----- App Icon
icon_file = './src/assets/app_icon.ico'

# ---- other excludes
excluded_modules += ['_ssl', 'cryptography']


a = Analysis(['openvr_fsr_app.py'],
             pathex=['C:\\py\\openvr_fsr_app'],
             binaries=[],
             datas=[(eel_js, 'eel'),
                    ('web', 'web'),
                    ('license.txt', '.'),
                    ('build/version.txt', '.'),
                    ('data', 'data'), ],
             hiddenimports=['bottle_websocket'],
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=excluded_modules,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name=APP_NAME,
          icon=icon_file,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=['vcruntime140.dll', 'python38.dll', 'python.dll'],
               name=APP_NAME)