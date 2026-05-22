# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FFTESC Tool v1.01
Build: pyinstaller fftesc_tool.spec
Output: dist/FFTESC_Tool (single executable)
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Data files to bundle ──────────────────────────────────────────────────────
# SVG logos (project root)
svg_files = [
    ('fftesc_logo.svg', '.'),
    ('fftesc_logo_on.svg', '.'),
    ('fftesc_title.svg', '.'),
    ('fftesc_title_on.svg', '.'),
]

# i18n JSON files
i18n_files = [
    (os.path.join('gui', 'i18n', f'{lang}.json'), os.path.join('gui', 'i18n'))
    for lang in ('fr', 'en', 'de', 'es', 'pl', 'it')
]

# docs
doc_files = [
    (os.path.join('docs', 'param_descriptions.json'), os.path.join('docs')),
]

# logo_cache (empty dir, but we need the folder structure)
# Not bundled — created at runtime in ~/.fftesc/logo_cache when frozen

# Build datas list
datas = []
for src, dst in svg_files + i18n_files + doc_files:
    if os.path.exists(src):
        datas.append((src, dst))

# Collect CustomTkinter data files (themes, fonts)
ctk_datas = collect_data_files('customtkinter', include_py_files=False)
datas.extend(ctk_datas)

# Collect matplotlib data files
mpl_datas = collect_data_files('matplotlib', include_py_files=False)
datas.extend(mpl_datas)

# Collect cairosvg data files
cairo_datas = collect_data_files('cairosvg', include_py_files=False)
datas.extend(cairo_datas)

# ── Hidden imports ────────────────────────────────────────────────────────────
hiddenimports = [
    'ftesc',
    'ftesc.data',
    'ftesc.protocol',
    'ftesc.transport',
    'ftesc.config_protocol',
    'ftesc.profiles',
    'ftesc.logger',
    'ftesc.simulator',
    'ftesc.wizard_engine',
    'ftesc.wizard_data',
    'ftesc.resources',
    'gui',
    'gui.app',
    'gui.logo',
    'gui.app_icons',
    'gui.tooltip',
    'gui.descriptions',
    'gui.i18n',
    'gui.wizard_data',
    'gui.styles',
    'gui.styles.colors',
    'gui.widgets',
    'gui.widgets.chart_card',
    'gui.widgets.value_card',
    'gui.widgets.fault_indicator',
    'gui.widgets.motor_selector',
    'gui.widgets.helpers',
    'gui.panels',
    'gui.panels.connection',
    'gui.panels.control',
    'gui.panels.realtime',
    'gui.panels.config_panel',
    'gui.panels.profile',
    'gui.panels.status',
    'gui.panels.wizard_panel',
    'gui.panels.recovery',
    'gui.panels.config_tabs',
    'gui.panels.config_tabs.motors',
    'gui.panels.config_tabs.limits',
    'gui.panels.config_tabs.dual',
    'gui.panels.config_tabs.inputs',
    'gui.panels.config_tabs.battery',
    'gui.panels.config_tabs.comms',
    'gui.panels.config_tabs.advanced',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    'cairosvg',
    'cairocffi',
    'customtkinter',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'numpy',
    'serial',
    'serial.tools.list_ports',
]

a = Analysis(
    ['ftesc_tool.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'matplotlib.tests',
        'PIL.tests',
        'customtkinter.test',
        'IPython',
        'jupyter',
        'notebook',
        'spyder',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FFTESC_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
