# -*- mode: python ; coding: utf-8 -*-

package_version = "0.3.2"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('project_template', 'project_template')],
    hiddenimports=['cookiecutter', 'cookiecutter.main', 'cookiecutter.extensions', 'prompt_toolkit', 'slugify'],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='fetcher',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )

