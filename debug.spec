# -*- mode: python -*-

import json
import os

config = json.loads(open("config.json", "r").read())
dir_path = os.path.dirname(os.path.realpath('.'))

block_cipher = None


a = Analysis(['main.py'],
             pathex=[dir_path],
             binaries=[],
             datas=[('resources/', 'resources'), ('twine/', 'twine'), ('ui/', 'ui'), ('themes/', 'themes'), ('widgets/', 'widgets'), ('config.json', '.')],
             hiddenimports=['PySide2.QtXml', 'PySide2.QtPrintSupport', 'PySide2.QtUiTools'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name=config['name'],
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name=config['exec'] + '.app',
             icon='resources/icon.icns',
             bundle_identifier='com.scots.sunrise',
             info_plist={
                'NSPrincipleClass': 'NSApplication',
                'NSHighResolutionCapable': 'True',
                'NSAppleScriptEnabled': False,
                'CFBundleURLTypes': [
                    {
                        'CFBundleURLName': config['name'] + ' Manifest',
                        'CFBundleURLSchemes': [config['protocol']],
                        'CFBundleURLIconFile': 'icon'
                    }
                ]
             }
            )
