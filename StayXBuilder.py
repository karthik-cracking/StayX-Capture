import sys
import os
import re
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QProgressBar, QGraphicsDropShadowEffect, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

# ═══════════════════════════════════════════════════════════════════════
#  PALETTE & STYLES
# ═══════════════════════════════════════════════════════════════════════
class Palette:
    BG1 = "#0F0F12"
    BG2 = "#1C1C24"
    TEXT = "#F0F0F5"
    TEXT2 = "#9B9BB0"
    ACCENT = "#8B5CF6"
    ACCENT_GRAD1 = "#4F46E5"
    ACCENT_GRAD2 = "#8B5CF6"
    INPUT_BG = "#121216"
    SUCCESS = "#10B981"
    DANGER = "#F43F5E"
    CONSOLE_BG = "#08080A"

STYLESHEET = f"""
QMainWindow {{
    background-color: {Palette.BG1};
}}
QWidget#central {{
    background-color: {Palette.BG1};
}}
QLabel {{
    color: {Palette.TEXT};
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}
QLabel#title {{
    font-size: 20px;
    font-weight: bold;
    color: #FFFFFF;
}}
QLabel#subtitle {{
    font-size: 12px;
    color: {Palette.TEXT2};
}}
QLabel#field_label {{
    font-size: 11px;
    font-weight: 600;
    color: {Palette.TEXT2};
    text-transform: uppercase;
}}
QLineEdit {{
    background-color: {Palette.INPUT_BG};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    color: {Palette.TEXT};
    padding: 8px 12px;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1px solid {Palette.ACCENT};
}}
QPushButton#btn_primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Palette.ACCENT_GRAD1}, stop:1 {Palette.ACCENT_GRAD2});
    border: none;
    border-radius: 8px;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 16px;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}
QPushButton#btn_primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5C52F8, stop:1 #9A6CFA);
}}
QPushButton#btn_primary:disabled {{
    background: #252530;
    color: #555565;
}}
QPushButton#btn_secondary {{
    background-color: {Palette.BG2};
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    color: {Palette.TEXT};
    font-size: 12px;
    padding: 8px 12px;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}
QPushButton#btn_secondary:hover {{
    background-color: #2A2A36;
    border: 1px solid rgba(255, 255, 255, 0.12);
}}
QTextEdit#console {{
    background-color: {Palette.CONSOLE_BG};
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 8px;
    color: #A3E635;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    padding: 10px;
}}
QProgressBar {{
    background-color: {Palette.INPUT_BG};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Palette.ACCENT_GRAD1}, stop:1 {Palette.ACCENT_GRAD2});
    border-radius: 4px;
}}
QCheckBox {{
    color: {Palette.TEXT2};
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 12px;
}}
"""

# ═══════════════════════════════════════════════════════════════════════
#  BUILD PROCESS BACKGROUND THREAD
# ═══════════════════════════════════════════════════════════════════════
class BuildThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        app_name = self.params['app_name']
        version = self.params['version']
        company = self.params['company']
        copyright_str = self.params['copyright']
        icon_path = self.params['icon_path']
        console_mode = self.params['console_mode']

        work_dir = Path(os.getcwd())
        dist_dir = work_dir / "dist"
        temp_version_file = work_dir / "temp_version_info.txt"
        temp_spec_file = work_dir / "temp_build.spec"

        try:
            # 1. Clean previous build folders to prevent conflicts
            self.log_signal.emit("[BUILD] Cleaning previous compilation outputs...")
            subprocess.run("pyinstaller --clean --noconfirm -h >nul 2>&1", shell=True) # run clean flag

            # 2. Parse version string into tuple
            parts = [int(x) for x in re.findall(r'\d+', version)]
            while len(parts) < 4:
                parts.append(0)
            version_tuple = tuple(parts[:4])

            # 3. Create Windows Version Info resource file
            self.log_signal.emit(f"[BUILD] Generating Windows file resource metadata (v{version})...")
            version_content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', {repr(company)}),
        StringStruct('FileDescription', {repr(app_name)}),
        StringStruct('FileVersion', {repr(version)}),
        StringStruct('InternalName', {repr(app_name)}),
        StringStruct('LegalCopyright', {repr(copyright_str)}),
        StringStruct('OriginalFilename', {repr(f"{app_name}.exe")}),
        StringStruct('ProductName', {repr(app_name)}),
        StringStruct('ProductVersion', {repr(version)})])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
            temp_version_file.write_text(version_content, encoding='utf-8')

            # 4. Generate dynamic PyInstaller spec template
            self.log_signal.emit("[BUILD] Writing temporary PyInstaller spec blueprint...")
            icon_arg = repr(str(icon_path)) if icon_path else "None"
            
            spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('PyQt5')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['Capture.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name={repr(app_name)},
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console_mode},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_arg},
    version={repr(str(temp_version_file))}
)
"""
            temp_spec_file.write_text(spec_content, encoding='utf-8')

            # 5. Run PyInstaller
            self.log_signal.emit(f"[BUILD] Starting PyInstaller compilation thread for {app_name}.exe...")
            cmd = f'pyinstaller --noconfirm "{temp_spec_file}"'
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log_signal.emit(line.strip())

            rc = process.poll()

            # Clean temporary build configuration scripts
            if temp_version_file.exists():
                temp_version_file.unlink()
            if temp_spec_file.exists():
                temp_spec_file.unlink()

            if rc == 0:
                self.log_signal.emit("\n[SUCCESS] Custom application packaged successfully!")
                self.finished_signal.emit(True, str(dist_dir))
            else:
                self.log_signal.emit(f"\n[ERROR] Compilation failed with return code {rc}")
                self.finished_signal.emit(False, "")

        except Exception as e:
            self.log_signal.emit(f"\n[EXCEPTION] Build process encountered an error: {e}")
            self.finished_signal.emit(False, "")


# ═══════════════════════════════════════════════════════════════════════
#  MAIN BUILDER WINDOW
# ═══════════════════════════════════════════════════════════════════════
class BuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StayX Capture - Custom App Builder")
        self.setFixedSize(540, 680)
        self.setStyleSheet(STYLESHEET)

        # Main Widget & Glassmorphic Container
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title_lbl = QLabel("StayX App Compiler")
        title_lbl.setObjectName("title")
        subtitle_lbl = QLabel("Build and brand your custom screenshot capture executable")
        subtitle_lbl.setObjectName("subtitle")
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)
        main_layout.addLayout(header_layout)

        # Fields Section (Card Box)
        fields_card = QFrame()
        fields_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Palette.BG2};
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }}
        """)
        fields_layout = QVBoxLayout(fields_card)
        fields_layout.setContentsMargins(16, 16, 16, 16)
        fields_layout.setSpacing(12)

        # App Name Input
        name_lbl = QLabel("Executable Name")
        name_lbl.setObjectName("field_label")
        self.name_input = QLineEdit("StayXCapture")
        self.name_input.setPlaceholderText("e.g. MyCapture")
        fields_layout.addWidget(name_lbl)
        fields_layout.addWidget(self.name_input)

        # App Version Input
        ver_lbl = QLabel("Product Version")
        ver_lbl.setObjectName("field_label")
        self.ver_input = QLineEdit("1.0.0.0")
        self.ver_input.setPlaceholderText("e.g. 1.0.0.0")
        fields_layout.addWidget(ver_lbl)
        fields_layout.addWidget(self.ver_input)

        # Company / Publisher Input
        comp_lbl = QLabel("Company / Author")
        comp_lbl.setObjectName("field_label")
        self.comp_input = QLineEdit("StayX")
        self.comp_input.setPlaceholderText("e.g. StayX Studio")
        fields_layout.addWidget(comp_lbl)
        fields_layout.addWidget(self.comp_input)

        # Legal Copyright Input
        copy_lbl = QLabel("Legal Copyright")
        copy_lbl.setObjectName("field_label")
        self.copy_input = QLineEdit("Copyright (c) 2026 StayX")
        self.copy_input.setPlaceholderText("e.g. Copyright (c) 2026 Company")
        fields_layout.addWidget(copy_lbl)
        fields_layout.addWidget(self.copy_input)

        # Icon Path Input
        icon_lbl = QLabel("Application Icon (.ico)")
        icon_lbl.setObjectName("field_label")
        fields_layout.addWidget(icon_lbl)
        
        icon_path_layout = QHBoxLayout()
        icon_path_layout.setSpacing(8)
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("Leave empty to use default icon")
        
        # Auto fill default icon path if present
        default_icon_path = os.path.abspath(os.path.join("assets", "screenshot_icon.ico"))
        if os.path.exists(default_icon_path):
            self.icon_input.setText(default_icon_path)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("btn_secondary")
        browse_btn.clicked.connect(self._browse_icon)
        icon_path_layout.addWidget(self.icon_input)
        icon_path_layout.addWidget(browse_btn)
        fields_layout.addLayout(icon_path_layout)

        # Checkboxes
        check_layout = QHBoxLayout()
        self.console_check = QCheckBox("Enable Console Output (Debug)")
        check_layout.addWidget(self.console_check)
        fields_layout.addLayout(check_layout)

        main_layout.addWidget(fields_card)

        # Action Button
        self.build_btn = QPushButton("Compile Executable")
        self.build_btn.setObjectName("btn_primary")
        self.build_btn.clicked.connect(self._start_build)
        main_layout.addWidget(self.build_btn)

        # Console Progress Logger
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        self.console = QTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Compilation logs will appear here...")
        main_layout.addWidget(self.console)

        # Subtle Shadow Effect for card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 8)
        fields_card.setGraphicsEffect(shadow)

        self.build_thread = None

    def _browse_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon File", "", "Icon Files (*.ico)"
        )
        if file_path:
            self.icon_input.setText(file_path)

    def _start_build(self):
        app_name = self.name_input.text().strip()
        version = self.ver_input.text().strip()
        company = self.comp_input.text().strip()
        copyright_str = self.copy_input.text().strip()
        icon_path = self.icon_input.text().strip()
        console_mode = self.console_check.isChecked()

        if not app_name:
            self.console.append("[ERROR] Executable Name cannot be empty.")
            return

        # Sanitize app name
        app_name = re.sub(r'[\\/*?:"<>| ]', '', app_name)
        if not app_name:
            app_name = "StayXCapture"
        self.name_input.setText(app_name)

        # Clean Console and Prepare UI
        self.console.clear()
        self.console.append("[INIT] Starting build setup...")
        self.build_btn.setEnabled(False)
        self.build_btn.setText("Compiling App...")
        self.progress_bar.show()
        self.progress_bar.setMaximum(0) # Busy indicator mode

        # Collect parameters
        params = {
            'app_name': app_name,
            'version': version if version else "1.0.0.0",
            'company': company if company else "StayX",
            'copyright': copyright_str if copyright_str else "Copyright (c) 2026 StayX",
            'icon_path': icon_path if icon_path else None,
            'console_mode': console_mode
        }

        # Start background building thread
        self.build_thread = BuildThread(params)
        self.build_thread.log_signal.connect(self._log_output)
        self.build_thread.finished_signal.connect(self._build_finished)
        self.build_thread.start()

    def _log_output(self, text):
        self.console.append(text)
        # Auto scroll to bottom
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _build_finished(self, success, output_dir):
        self.build_btn.setEnabled(True)
        self.build_btn.setText("Compile Executable")
        self.progress_bar.hide()

        if success:
            self.console.append("\n🎉 SUCCESS: Your application has been compiled successfully!")
            self.console.append(f"Output saved in: {output_dir}")
            # Open output folder in explorer
            if os.path.exists(output_dir):
                os.startfile(output_dir)
        else:
            self.console.append("\n❌ ERROR: Build failed. Please inspect the log details above.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BuilderWindow()
    window.show()
    sys.exit(app.exec_())
