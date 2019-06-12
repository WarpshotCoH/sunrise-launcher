# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/Users/amayo/Documents/workarea/self/sunrise-launcher'],
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
          name='Sunrise',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='Sunrise.app',
             icon='resources/icon.icns',
             bundle_identifier='com.scots.sunrise',
             info_plist={
                'NSPrincipleClass': 'NSApplication',
                'NSHighResolutionCapable': 'True',
                'NSAppleScriptEnabled': False,
                'CFBundleURLTypes': [
                    {
                        'CFBundleURLName': 'Sunrise Manifest',
                        'CFBundleURLSchemes': ['sunrise'],
                        'CFBundleURLIconFile': 'icon'
                    }
                ]
             }
            )
