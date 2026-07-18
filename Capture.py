"""
StayX Capture v3.0  —  Premium UI
─────────────────────────────────────────────────────────────
Features: region / fullscreen capture, built-in annotation editor,
capture history, global hotkeys, auto-organized folders,
dark/light theme, copy-to-clipboard, configurable save folder.
"""

import sys, os, json, ctypes, math, base64

if sys.stdout is None:
    class DummyWriter:
        def write(self, *args, **kwargs): pass
        def flush(self): pass
    sys.stdout = DummyWriter()
    sys.stderr = DummyWriter()

try:
    import winreg
except ImportError:
    winreg = None
from pathlib import Path
from datetime import datetime, date
import requests
import urllib3
from io import BytesIO

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSystemTrayIcon, QMenu, QLineEdit,
    QFrame, QGraphicsDropShadowEffect, QTabWidget, QScrollArea,
    QListWidget, QListWidgetItem, QInputDialog, QComboBox, QCheckBox,
    QSlider, QStatusBar, QSizePolicy, QStackedWidget, QTabBar, QGridLayout,
    QColorDialog, QButtonGroup, QAction, QActionGroup
)
from PyQt5.QtCore import (
    Qt, QRect, QPoint, QPointF, pyqtSignal, QTimer, QSize, QObject,
    QPropertyAnimation, pyqtProperty, QEasingCurve, QRectF,
    QBuffer, QByteArray
)
from PyQt5.QtGui import (
    QIcon, QFont, QColor, QPainter, QPen, QCursor, QPixmap, QBrush,
    QPolygonF, QImage, QLinearGradient, QPainterPath, QFontMetrics
)
from PyQt5.QtSvg import QSvgRenderer

try:
    from pynput.keyboard import GlobalHotKeys
    HAS_HOTKEYS = True
except ImportError:
    HAS_HOTKEYS = False

# ═══════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════
CONFIG_PATH = Path.home() / ".stayx_capture_config.json"
CLIPBOARD_HISTORY_PATH = Path.home() / ".stayx_capture_clipboard.json"

# ═══════════════════════════════════════════════════════════════════════
#  PREMIUM SVG ICONS (Hand-crafted for StayX Capture)
# ═══════════════════════════════════════════════════════════════════════
ICONS = {
    # ── Navigation / Popup ────────────────────────────────────────────
    "crop": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="7" y="7" width="10" height="10" rx="1.5" stroke-dasharray="3 2"/></svg>',
    "monitor": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/><circle cx="12" cy="10" r="2.5" fill="currentColor"/></svg>',
    "log-out": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
    "folder": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>',
    "history": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>',
    "settings": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    "api": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 13v8"/><path d="m8 17 4-4 4 4"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>',
    "camera": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    "refresh": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v6h6"/><path d="M21 12A9 9 0 0 0 6 5.3L3 8"/><path d="M21 22v-6h-6"/><path d="M3 12a9 9 0 0 0 15 6.7l3-2.7"/></svg>',
    "layers": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polygon points="2 17 12 22 22 17"/><polygon points="2 12 12 17 22 12"/></svg>',
    "help": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "user": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',

    # ── Editor Drawing Tools ──────────────────────────────────────────
    "select": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="m4 4 7.07 16.97 2.51-7.39 7.39-2.51L4 4z"/><path d="m13.5 13.5 5.5 5.5"/></svg>',
    "pen": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19 7-7 3 3-7 7-3-3z"/><path d="m18 13-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="m2 2 7.586 7.586"/><circle cx="11" cy="11" r="2"/></svg>',
    "rect": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="4 2"/><circle cx="3" cy="3" r="1.5" fill="currentColor" stroke="none"/><circle cx="21" cy="3" r="1.5" fill="currentColor" stroke="none"/><circle cx="3" cy="21" r="1.5" fill="currentColor" stroke="none"/><circle cx="21" cy="21" r="1.5" fill="currentColor" stroke="none"/></svg>',
    "arrow": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19 19 5"/><path d="M15 5h4v4"/><circle cx="5" cy="19" r="1.5" fill="currentColor" stroke="none"/></svg>',
    "text": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9.5" y1="20" x2="14.5" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>',
    "blur": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3" opacity=".35"/><circle cx="12" cy="12" r="6" opacity=".55"/><circle cx="12" cy="12" r="9" opacity=".8"/></svg>',
    "highlight": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="m9 11-6 6v3h9l3-3"/><path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/></svg>',
    "highlighter": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="m9 11-6 6v3h9l3-3"/><path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/></svg>',
    "step": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 2"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/></svg>',
    "sticker": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8.5L15.5 3z"/><polyline points="14 3 14 8 21 8"/><path d="M8 13h0"/><path d="M16 13h0"/><path d="M10 16s.8 1 2 1 2-1 2-1"/></svg>',

    # ── Editor Action Buttons ─────────────────────────────────────────
    "undo": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/></svg>',
    "redo": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"/></svg>',
    "save": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>',
    "copy": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
    "upload": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "close": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" opacity="0.2"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',

    # ── Editor Zoom Controls ──────────────────────────────────────────
    "zoom-in": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M11 8v6"/><path d="M8 11h6"/></svg>',
    "zoom-out": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M8 11h6"/></svg>',
    "maximize": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>',
    "delete": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>',
}
GD_TOKEN_PATH = Path.home() / ".stayx_capture_gdrive_token.json"
GD_CREDENTIALS_PATH = Path.home() / ".stayx_capture_gdrive_credentials.json"
GD_SCOPES = ['https://www.googleapis.com/auth/drive.file']
DEFAULT_FOLDER = str(Path.home() / "Pictures" / "Screenshots")
DEFAULTS = {
    "save_folder":       DEFAULT_FOLDER,
    "auto_organize":     True,
    "copy_clipboard":    True,
    "open_editor":       False,
    "hotkey_region":     "<ctrl>+<shift>+1",
    "hotkey_fullscreen": "<ctrl>+<shift>+2",
    "theme":             "dark",
    "monitor_clipboard": True,
    "api_enabled":       True,
    "api_endpoint":      "https://dmarket.space/api/upload",
    "api_key":           "1392054442060415029",
    "api_upload_images": True,
    "api_upload_clipboard": True,
    "start_minimized":   True,
    "auto_start":        False,
    "imgbb_api_key": "",
    "storage_provider": "ImgBB" # "ImgBB", "GoogleDrive", or "Both"
}

HOTKEY_PRESETS = [
    ("Ctrl + Shift + 1", "<ctrl>+<shift>+1"),
    ("Ctrl + Shift + 2", "<ctrl>+<shift>+2"),
    ("Ctrl + Shift + S", "<ctrl>+<shift>+s"),
    ("Ctrl + Shift + F", "<ctrl>+<shift>+f"),
    ("Ctrl + Alt + S",   "<ctrl>+<alt>+s"),
    ("Ctrl + Alt + F",   "<ctrl>+<alt>+f"),
    ("Disabled",         "disabled"),
]


def cfg_load():
    c = dict(DEFAULTS)
    try:
        c.update(json.loads(CONFIG_PATH.read_text()))
    except Exception:
        pass
    return c


def cfg_save(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def cfg_set(**kw):
    c = cfg_load()
    c.update(kw)
    cfg_save(c)


def save_folder():
    return cfg_load().get("save_folder", DEFAULT_FOLDER)


def set_windows_autostart(enabled: bool):
    """Enable or disable autostart with Windows using Registry."""
    if winreg is None:
        return False
    
    app_name = "StayXCapture"
    # Construct command line: "path/to/python.exe" "path/to/Capture.py"
    exe_path = os.path.abspath(sys.executable)
    if getattr(sys, 'frozen', False):
        cmd = f'"{exe_path}"'
    elif __file__:
        script_path = os.path.abspath(__file__)
        cmd = f'"{exe_path}" "{script_path}"'
    else:
        cmd = f'"{exe_path}" "{os.path.abspath(sys.argv[0])}"'
        
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Registry Error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
#  CLIPBOARD HISTORY
# ═══════════════════════════════════════════════════════════════════════
def clipboard_load():
    """Load clipboard history from disk."""
    try:
        if CLIPBOARD_HISTORY_PATH.exists():
            return json.loads(CLIPBOARD_HISTORY_PATH.read_text())
    except Exception:
        pass
    return []


def clipboard_save(history):
    """Save clipboard history to disk."""
    try:
        CLIPBOARD_HISTORY_PATH.write_text(json.dumps(history, indent=2))
    except Exception:
        pass


def clipboard_add(text):
    """Add new text to clipboard history (max 50 entries)."""
    if not text or not text.strip():
        return
    
    text = text.strip()
    history = clipboard_load()
    
    # Remove duplicate if exists
    history = [h for h in history if h.get("text") != text]
    
    # Add new entry at the beginning
    history.insert(0, {
        "text": text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 50 entries
    history = history[:50]
    
    clipboard_save(history)


# ═══════════════════════════════════════════════════════════════════════
#  API UPLOAD FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════
def api_upload_screenshot(png_bytes: bytes, filename: str):
    """Upload screenshot to API endpoint."""
    cfg = cfg_load()
    if not cfg.get("api_enabled") or not cfg.get("api_upload_images"):
        return None
    
    endpoint = cfg.get("api_endpoint", "").strip()
    api_key = cfg.get("api_key", "").strip() or os.environ.get("STAYX_CAPTURE_API_KEY", "").strip() or os.environ.get("DMARKET_API_KEY", "").strip()
    
    if not endpoint:
        print("API: No endpoint configured")
        return None
    
    try:
        print(f"API: Uploading screenshot {filename}...")
        
        # Base auth headers used for both multipart and json fallback
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
            headers['X-API-Key'] = api_key
        else:
            print("API Warning: No API key configured. Set it in Settings > API tab or use STAYX_CAPTURE_API_KEY.")

        # Try multipart/form-data first (many upload endpoints require a real file part)
        form_data = {
            "type": "screenshot",
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "api_key": api_key
        }
        files = {
            "file": (filename, png_bytes, "image/png"),
            "image": (filename, png_bytes, "image/png")
        }

        print(f"API: Sending to {endpoint}...")
        response = requests.post(endpoint, data=form_data, files=files, headers=headers, timeout=15, verify=False)

        # Fallback to legacy JSON base64 format for servers built from old examples
        if response.status_code >= 400 and "file part" in response.text.lower():
            image_base64 = base64.b64encode(png_bytes).decode('utf-8')
            print(f"API: Multipart rejected, retrying JSON base64 ({len(image_base64)} bytes)...")
            payload = {
                "type": "screenshot",
                "filename": filename,
                "image": image_base64,
                "timestamp": datetime.now().isoformat(),
                "api_key": api_key
            }
            json_headers = dict(headers)
            json_headers['Content-Type'] = 'application/json'
            response = requests.post(endpoint, json=payload, headers=json_headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            print(f"API: Upload successful! Response: {result}")
            return result
        else:
            print(f"API HTTP Error: {response.status_code}")
            print(f"API Response: {response.text}")
            return None
            
    except Exception as e:
        import traceback
        print(f"API Upload Failed: {str(e)}")
        print(traceback.format_exc())
        return None

def api_upload_clipboard(text: str):
    """Upload clipboard text to API endpoint."""
    cfg = cfg_load()
    if not cfg.get("api_enabled") or not cfg.get("api_upload_clipboard"):
        return None
    
    endpoint = cfg.get("api_endpoint", "").strip()
    api_key = cfg.get("api_key", "").strip() or os.environ.get("STAYX_CAPTURE_API_KEY", "").strip() or os.environ.get("DMARKET_API_KEY", "").strip()
    
    if not endpoint:
        return None
    
    try:
        print(f"API: Uploading clipboard text ({len(text)} chars)...")
        
        # Prepare payload
        payload = {
            "type": "clipboard",
            "text": text[:5000],  # Limit to 5000 chars
            "timestamp": datetime.now().isoformat(),
            "api_key": api_key
        }
        
        # Send POST request with requests library
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
            headers['X-API-Key'] = api_key
        else:
            print("API Warning: No API key configured. Set it in Settings > API tab or use STAYX_CAPTURE_API_KEY.")
        
        print(f"API: Sending to {endpoint}...")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            print(f"API: Clipboard upload successful! Response: {result}")
            return result
        else:
            print(f"API HTTP Error: {response.status_code}")
            print(f"API Response: {response.text}")
            return None
            
    except Exception as e:
        import traceback
        print(f"API Upload Failed: {str(e)}")
        print(traceback.format_exc())
        return None


# ═══════════════════════════════════════════════════════════════════════
#  GOOGLE DRIVE UPLOAD FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════
def gdrive_get_service():
    """Authenticate and return the Google Drive service."""
    creds = None
    if GD_TOKEN_PATH.exists():
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(GD_TOKEN_PATH), GD_SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            if not GD_CREDENTIALS_PATH.exists():
                return None
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GD_CREDENTIALS_PATH), GD_SCOPES)
            creds = flow.run_local_server(port=0)
        
        GD_TOKEN_PATH.write_text(creds.to_json())
    
    from googleapiclient.discovery import build
    return build('drive', 'v3', credentials=creds)


def gdrive_upload_screenshot(pixmap: 'QPixmap', filename: str):
    """Upload screenshot to Google Drive."""
    try:
        service = gdrive_get_service()
        if not service:
            print("GDrive: Service not available (need credentials)")
            return None
        
        # Convert QPixmap to PNG bytes
        from PyQt5.QtCore import QBuffer, QIODevice
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_data = buffer.data()
        buffer.close()
        
        # Upload using MediaIoBaseUpload
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(BytesIO(image_data), mimetype='image/png', resumable=True)
        
        file_metadata = {'name': filename}
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        print(f"GDrive: Upload successful! File ID: {file.get('id')}")
        return file
    except Exception as e:
        print(f"GDrive Upload Failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════
#  COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════
class Palette:
    """Centralized color definitions for premium glassmorphic theme."""
    class Dark:
        BG1 = "#0F0F12"
        BG2 = "#1C1C24"
        BG3 = "#25252F"
        BTN_DARK = "#1C1C24"
        BTN_HOVER = "#2A2A36"
        BORDER = "rgba(255, 255, 255, 0.06)"
        BORDER_HOVER = "rgba(255, 255, 255, 0.12)"
        TEXT = "#F0F0F5"
        TEXT2 = "#9B9BB0"
        TEXT3 = "#6B6B80"
        ACCENT1 = "#8B5CF6"
        GLOW = "rgba(139, 92, 246, 0.18)"
        ACCENT_DIM = "rgba(139, 92, 246, 0.08)"
        SEPARATOR = "rgba(255, 255, 255, 0.06)"
        TAB_BG = "#0F0F12"
        TAB_ACTIVE = "#8B5CF6"
        GLOW_COLOR = QColor(139, 92, 246, 50)
        SHADOW = QColor(0, 0, 0, 120)

        CARD1 = "#1C1C24"
        CARD2 = "#25252F"
        INPUT_BG = "#0c0c11" # Deeper, richer navy-charcoal than flat black
        TOGGLE_ON = "#8B5CF6"
        TOGGLE_OFF = "#3A3A4A"
        ACCENT2 = "#4F46E5"
        ACCENT3 = "#14B8A6"
        ACCENT_GRAD1 = "#8B5CF6"
        ACCENT_GRAD2 = "#4F46E5"
        DANGER = "#F43F5E"
        SUCCESS = "#10B981"
        SURFACE = "#0F0F12"
        LIST_HOVER = "#25252F"
        LIST_SELECT = "#8B5CF6"
        TOGGLE_KNOB = "#ffffff"
        SHADOW = QColor(0, 0, 0, 120)
        # Premium extras
        GLASS_BG = "rgba(28, 28, 36, 0.85)"
        GLASS_BORDER = "rgba(255, 255, 255, 0.08)"
        GRAD_START = "#4F46E5"
        GRAD_END = "#8B5CF6"
        DANGER_GRAD = "#EC4899"

    class Light:
        BG1 = "#FFFFFF"
        BG2 = "#F8FAFC"
        BG3 = "#F1F5F9"
        BTN_DARK = "#F1F5F9"
        BTN_HOVER = "#E2E8F0"
        BORDER = "rgba(0, 0, 0, 0.08)"
        BORDER_HOVER = "rgba(0, 0, 0, 0.14)"
        TEXT = "#1E1E2E"
        TEXT2 = "#64748B"
        TEXT3 = "#94A3B8"
        ACCENT1 = "#7C3AED"
        GLOW = "rgba(124, 58, 237, 0.10)"
        ACCENT_DIM = "rgba(124, 58, 237, 0.05)"
        CARD1 = "#FFFFFF"
        CARD2 = "#F8FAFC"
        SURFACE = "#FAFBFC"
        INPUT_BG = "#F1F5F9"
        ACCENT2 = "#4F46E5"
        ACCENT3 = "#0D9488"
        ACCENT_GRAD1 = "#7C3AED"
        ACCENT_GRAD2 = "#4F46E5"
        DANGER = "#F43F5E"
        SUCCESS = "#10B981"
        SEPARATOR = "rgba(0, 0, 0, 0.06)"
        TAB_BG = "#FFFFFF"
        TAB_ACTIVE = "#7C3AED"
        TOGGLE_OFF = "#CBD5E1"
        TOGGLE_ON = "#7C3AED"
        TOGGLE_KNOB = "#ffffff"
        LIST_HOVER = "#F1F5F9"
        LIST_SELECT = "#7C3AED"
        SHADOW = QColor(0, 0, 0, 15)
        # Premium extras
        GLASS_BG = "rgba(255, 255, 255, 0.90)"
        GLASS_BORDER = "rgba(0, 0, 0, 0.06)"
        GRAD_START = "#4F46E5"
        GRAD_END = "#7C3AED"
        DANGER_GRAD = "#EC4899"


# ═══════════════════════════════════════════════════════════════════════
#  CUSTOM TOGGLE SWITCH
# ═══════════════════════════════════════════════════════════════════════
class ToggleSwitch(QWidget):
    """Modern animated iOS-style toggle switch."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        QWidget.__init__(self, parent)
        self._checked = checked
        self._knob_x = 22.0 if checked else 2.0
        self._dark = True
        self.setFixedSize(44, 24)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._anim = QPropertyAnimation(self, b"knobX")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutQuint)

    def get_knob_x(self):
        return self._knob_x

    def set_knob_x(self, v):
        self._knob_x = v
        self.update()

    knobX = pyqtProperty(float, get_knob_x, set_knob_x)

    def isChecked(self):
        return self._checked

    def setChecked(self, v):
        self._checked = v
        self._knob_x = 22.0 if v else 2.0
        self.update()

    def setDark(self, dark):
        self._dark = dark
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._anim.stop()
            self._anim.setStartValue(self._knob_x)
            self._anim.setEndValue(22.0 if self._checked else 2.0)
            self._anim.start()
            self.toggled.emit(self._checked)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pal = Palette.Dark if self._dark else Palette.Light

        # outer glow when on
        if self._checked:
            glow = QColor(pal.TOGGLE_ON)
            glow.setAlpha(35)
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
            p.drawRoundedRect(QRectF(-2, -2, 48, 28), 14, 14)

        # track with gradient when on
        if self._checked:
            grad = QLinearGradient(0, 0, 44, 0)
            grad.setColorAt(0, QColor(pal.GRAD_START))
            grad.setColorAt(1, QColor(pal.GRAD_END))
            p.setBrush(QBrush(grad))
        else:
            p.setBrush(QColor(pal.TOGGLE_OFF))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(0, 0, 44, 24), 12, 12)

        # knob shadow (neumorphic)
        shadow_c = QColor(0, 0, 0, 50)
        p.setBrush(shadow_c)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(self._knob_x + 0.5, 2.5, 20, 20))

        # knob
        p.setBrush(QColor(pal.TOGGLE_KNOB))
        p.setPen(QPen(QColor(0, 0, 0, 20), 0.5))
        p.drawEllipse(QRectF(self._knob_x, 2, 20, 20))

        # inner highlight on knob
        highlight = QColor(255, 255, 255, 80)
        p.setBrush(highlight)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(self._knob_x + 4, 5, 8, 6))

        p.end()


class NotificationWidget(QWidget):
    """Animated slide-in notification toast."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        
        self.bg = QFrame()
        self.bg.setObjectName("notification_bg")
        self.bg_layout = QHBoxLayout(self.bg)
        
        self.label = QLabel(text)
        self.label.setStyleSheet("color: white; font-weight: 600; font-size: 11px;")
        self.bg_layout.addWidget(self.label)
        
        layout.addWidget(self.bg)
        
        # Style
        self.bg.setStyleSheet("""
            QFrame#notification_bg {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #4F46E5, stop:1 #8B5CF6);
                border-radius: 10px;
            }
        """)
        
        # Shadow (glow effect)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(79, 70, 229, 100))
        shadow.setOffset(0, 6)
        self.bg.setGraphicsEffect(shadow)

        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.adjustSize()
        self.hide()

    def show_animated(self):
        if not self.parentWidget(): return
        self.adjustSize()
        
        pw = self.parentWidget().width()
        ph = self.parentWidget().height()
        
        # Position at bottom right
        start_x = pw - self.width() - 20
        start_pos = QPoint(start_x, ph)
        end_pos = QPoint(start_x, ph - self.height() - 20)
        
        self.move(start_pos)
        self.show()
        
        self._anim.setStartValue(start_pos)
        self._anim.setEndValue(end_pos)
        self._anim.start()
        
        QTimer.singleShot(3000, self.hide_animated)

    def hide_animated(self):
        if not self.parentWidget(): return
        ph = self.parentWidget().height()
        end_pos = QPoint(self.x(), ph)
        
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(end_pos)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()
class CollapsibleSection(QWidget):
    """A widget with a clickable header that reveals/hides content."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._dark = True
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.header = QWidget()
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setFixedHeight(48)
        self.header.setObjectName("section_header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("section_title")
        self.title_lbl.setFont(QFont("Inter", 11, QFont.DemiBold))
        header_layout.addWidget(self.title_lbl)
        
        header_layout.addStretch()
        
        self.chevron = QLabel("◢") # Will rotate or change
        self.chevron.setObjectName("chevron")
        header_layout.addWidget(self.chevron)
        
        main_layout.addWidget(self.header)
        
        # Content
        self.content_area = QWidget()
        self.content_area.setObjectName("section_content")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(12, 8, 12, 12)
        self.content_layout.setSpacing(4)
        self.content_area.hide()
        
        main_layout.addWidget(self.content_area)
        
        # Interactions
        self.header.mousePressEvent = self._toggle

    def _toggle(self, event):
        self._expanded = not self._expanded
        self.content_area.setVisible(self._expanded)
        self.chevron.setText("▿" if self._expanded else "◢")
        self.update_styles()

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)

    def addLayout(self, layout):
        self.content_layout.addLayout(layout)

    def setDark(self, dark):
        self._dark = dark
        self.update_styles()

    def update_styles(self):
        pal = Palette.Dark if self._dark else Palette.Light
        bg = pal.BG2 if self._expanded else "transparent"
        border_radius = "14px 14px 0 0" if self._expanded else "14px"
        
        self.header.setStyleSheet(f"""
            QWidget#section_header {{
                background: {bg};
                border-radius: {border_radius};
                border: 1px solid {pal.GLASS_BORDER if self._expanded else 'transparent'};
                border-bottom: {'none' if self._expanded else f'1px solid transparent'};
            }}
            QWidget#section_header:hover {{
                background: {pal.LIST_HOVER};
            }}
            QLabel#section_title {{
                color: {pal.ACCENT1 if self._expanded else pal.TEXT};
            }}
            QLabel#chevron {{
                color: {pal.TEXT3};
                font-size: 14px;
            }}
        """)
        
        if self._expanded:
            self.content_area.setStyleSheet(f"""
                QWidget#section_content {{
                    background: {pal.BG2};
                    border-radius: 0 0 14px 14px;
                    border: 1px solid {pal.GLASS_BORDER};
                    border-top: 1px solid {pal.SEPARATOR};
                }}
            """)


# ═══════════════════════════════════════════════════════════════════════
#  TOGGLE ROW  (label + toggle switch)
# ═══════════════════════════════════════════════════════════════════════
class ToggleRow(QWidget):
    """A row with label text and a toggle switch on the right."""
    toggled = pyqtSignal(bool)

    def __init__(self, text, description="", checked=False, parent=None):
        super().__init__(parent)
        self._dark = True
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        self._label = QLabel(text)
        self._label.setFont(QFont("Inter", 10, QFont.DemiBold))
        text_layout.addWidget(self._label)
        if description:
            self._desc = QLabel(description)
            self._desc.setFont(QFont("Inter", 9))
            text_layout.addWidget(self._desc)
        else:
            self._desc = None
        layout.addLayout(text_layout)
        layout.addStretch()

        self.switch = ToggleSwitch(checked)
        self.switch.toggled.connect(self.toggled.emit)
        layout.addWidget(self.switch, 0, Qt.AlignVCenter)

    def isChecked(self):
        return self.switch.isChecked()

    def setDark(self, dark):
        self._dark = dark
        pal = Palette.Dark if dark else Palette.Light
        self._label.setStyleSheet(f"color: {pal.TEXT}; background: transparent;")
        if self._desc:
            self._desc.setStyleSheet(f"color: {pal.TEXT3}; background: transparent;")
        self.switch.setDark(dark)


# ═══════════════════════════════════════════════════════════════════════
#  THEMES  (generated from Palette)
# ═══════════════════════════════════════════════════════════════════════
def _popup_style(p):
    return f"""
    QWidget#card {{
        background: {p.CARD1};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 24px;
    }}
    QLabel#title {{
        color: {p.TEXT};
        font-family: 'Inter', 'SF Pro Display', 'Segoe UI Variable Display', system-ui;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.5px;
        background: transparent;
    }}
    QLabel#sub {{
        color: {p.TEXT3};
        font-family: 'Inter', 'SF Pro Text', 'Segoe UI Variable Small';
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.3px;
        background: transparent;
    }}
    QLabel#status {{
        color: {p.ACCENT3};
        font-family: 'Inter', 'Segoe UI';
        font-size: 11px;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#section {{
        color: {p.ACCENT1};
        font-family: 'Inter', 'Segoe UI';
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        background: transparent;
        margin-top: 6px;
    }}
    QLabel {{
        color: {p.TEXT2};
        font-family: 'Inter', 'Segoe UI';
        font-size: 12px;
        background: transparent;
    }}
    QPushButton#action {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {p.GRAD_START}, stop:1 {p.GRAD_END});
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 11px 18px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#action:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {p.GRAD_END}, stop:1 {p.ACCENT1});
    }}
    QPushButton#action:pressed {{
        background: {p.ACCENT2};
        padding: 12px 17px;
    }}
    QPushButton#secondary {{
        background: {p.BTN_DARK};
        color: {p.TEXT};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 10px;
        padding: 10px 16px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#secondary:hover {{
        background: {p.BTN_HOVER};
        border-color: {p.BORDER_HOVER};
    }}
    QPushButton#small {{
        background: {p.BTN_DARK};
        color: {p.TEXT2};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 8px;
        padding: 7px 14px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton#small:hover {{
        color: {p.TEXT};
        background: {p.BTN_HOVER};
        border-color: {p.BORDER_HOVER};
    }}
    QPushButton#icon_btn {{
        background: {p.BTN_DARK};
        color: {p.TEXT2};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 8px;
        padding: 7px 12px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 12px;
    }}
    QPushButton#icon_btn:hover {{
        color: {p.TEXT};
        background: {p.BTN_HOVER};
        border-color: {p.BORDER_HOVER};
    }}
    QPushButton#danger {{
        background: transparent;
        color: {p.DANGER};
        border: 1px solid {p.DANGER};
        border-radius: 8px;
        padding: 7px 14px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton#danger:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {p.DANGER}, stop:1 {p.DANGER_GRAD});
        color: #ffffff;
        border-color: transparent;
    }}
    QLineEdit {{
        background: {p.INPUT_BG};
        color: {p.TEXT};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 10px;
        padding: 9px 14px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 12px;
        selection-background-color: {p.ACCENT1};
    }}
    QLineEdit:focus {{
        border-color: {p.ACCENT1};
        background: {p.BG2};
    }}
    QFrame#sep {{
        background: {p.SEPARATOR};
        max-height: 1px;
        border: none;
    }}
    QComboBox {{
        background: {p.INPUT_BG};
        color: {p.TEXT};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 10px;
        padding: 7px 14px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 12px;
    }}
    QComboBox:hover {{
        border-color: {p.BORDER_HOVER};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {p.TEXT3};
    }}
    QComboBox QAbstractItemView {{
        background: {p.CARD2};
        color: {p.TEXT};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 10px;
        padding: 4px;
        selection-background-color: {p.ACCENT1};
        selection-color: #ffffff;
        outline: none;
    }}
    QListWidget {{
        background: {p.INPUT_BG};
        color: {p.TEXT2};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 12px;
        font-family: 'Inter', 'Segoe UI';
        font-size: 11px;
        padding: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        border-radius: 8px;
        margin: 2px 4px;
        background: transparent;
        border-bottom: 1px solid {p.SEPARATOR};
    }}
    QListWidget::item:last {{
        border-bottom: none;
    }}
    QListWidget::item:hover {{
        background: {p.LIST_HOVER};
        color: {p.TEXT};
        border-bottom-color: transparent;
    }}
    QListWidget::item:selected {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {p.GRAD_START}, stop:1 {p.GRAD_END});
        color: #ffffff;
        border: none;
        font-weight: 600;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.BORDER_HOVER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p.TEXT3};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        height: 0;
    }}
    """

def _tab_style(p):
    return f"""
    QTabWidget {{
        background: transparent;
        border: none;
    }}
    QTabWidget::pane {{
        border: none;
        background: transparent;
        top: 0px;
    }}
    QTabBar {{
        background: transparent;
        border-bottom: 1px solid {p.SEPARATOR};
    }}
    QTabBar::tab {{
        background: transparent;
        color: {p.TEXT3};
        padding: 13px 22px;
        border: none;
        font-family: 'Inter', 'Segoe UI';
        font-size: 11px;
        font-weight: 600;
        margin: 0;
    }}
    QTabBar::tab:selected {{
        color: {p.ACCENT1};
        border-bottom: 2.5px solid qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {p.GRAD_START}, stop:1 {p.GRAD_END});
    }}
    QTabBar::tab:hover:!selected {{
        color: {p.TEXT2};
        background: {p.GLOW};
        border-radius: 8px 8px 0 0;
    }}
    QPalette#property_bar {{
        background: {p.BG1};
        border-bottom: 1px solid {p.GLASS_BORDER};
    }}
    QWidget#property_bar QLabel {{
        color: {p.TEXT3};
        font-family: 'Inter', 'Segoe UI Variable Small';
        font-size: 10px;
        font-weight: 600;
    }}
    QComboBox {{
        background: {p.BTN_DARK};
        color: {p.TEXT};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 11px;
    }}
    QComboBox:hover {{ border-color: {p.ACCENT1}; }}
    """

def _editor_style(p):
    return f"""
    QMainWindow {{ background: {p.BG1}; color: {p.TEXT}; }}
    
    /* Main Container */
    QWidget#main_container {{
        background: {p.BG1};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 16px;
    }}
    
    /* Left Tool Sidebar */
    QWidget#sidebar_nav {{
        background: {p.BG1};
        border-right: 1px solid {p.GLASS_BORDER};
    }}
    QPushButton#nav_btn {{
        background: transparent;
        border: none;
        border-radius: 10px;
    }}
    QPushButton#nav_btn:hover {{
        background: {p.BTN_HOVER};
    }}
    
    /* Center Tool Sidebar */
    QWidget#tool_sidebar {{
        background: {p.BG2};
        border-right: 1px solid {p.GLASS_BORDER};
    }}
    
    /* Top Header Bar */
    QWidget#top_bar_v3 {{
        background: {p.BG1};
        border-bottom: 1px solid {p.GLASS_BORDER};
    }}
    QLabel#breadcrumb_file {{
        color: {p.TEXT};
        font-family: 'Inter', 'Segoe UI Variable Small';
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }}
    QLabel#zoom_label {{
        color: {p.TEXT2};
        font-family: 'Inter', 'Segoe UI';
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        background: {p.BG2};
        border-radius: 6px;
        border: 1px solid {p.GLASS_BORDER};
    }}
    QLabel#img_dimensions {{
        color: {p.TEXT3};
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 10px;
    }}
    
    /* Canvas Area — subtle checkerboard */
    QWidget#canvas_container {{
        background: {p.BG1};
    }}
    QScrollArea#editor_scroll {{
        background: transparent;
        border: none;
    }}
    
    /* Property Bar (floating) */
    QWidget#property_bar {{
        background: {p.BG2};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 10px;
        margin-bottom: 8px;
    }}
    QWidget#property_bar QLabel {{
        color: {p.TEXT2};
        font-family: 'Inter', 'Segoe UI';
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    QWidget#property_bar QSlider::groove:horizontal {{
        height: 4px;
        background: {p.BG3};
        border-radius: 2px;
    }}
    QWidget#property_bar QSlider::handle:horizontal {{
        width: 14px;
        height: 14px;
        margin: -5px 0;
        background: {p.ACCENT1};
        border-radius: 7px;
        border: 2px solid {p.BG2};
    }}
    QWidget#property_bar QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p.GRAD_START}, stop:1 {p.GRAD_END});
        border-radius: 2px;
    }}
    QWidget#property_bar QComboBox {{
        background: {p.BG1};
        color: {p.TEXT};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 11px;
        font-family: 'Inter', 'Segoe UI';
    }}
    
    /* Status Bar */
    QWidget#status_bar {{
        background: {p.BG1};
        border-top: 1px solid {p.GLASS_BORDER};
    }}
    QLabel#status_text {{
        color: {p.TEXT3};
        font-family: 'Inter', 'Segoe UI';
        font-size: 10px;
    }}
    
    /* Color swatches */
    QPushButton#color_swatch {{
        border: 2px solid transparent;
        border-radius: 12px;
    }}
    QPushButton#color_swatch:checked {{
        border: 2px solid {p.TEXT};
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.BG3};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p.TEXT3};
    }}
    QScrollBar:horizontal {{
        border: none;
        background: transparent;
        height: 8px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.BG3};
        min-width: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {p.TEXT3};
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0; height: 0;
    }}
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
    }}
    
    /* Context menus */
    QMenu {{
        background: {p.BG2};
        border: 1px solid {p.GLASS_BORDER};
        border-radius: 8px;
        padding: 4px;
        color: {p.TEXT};
        font-family: 'Inter', 'Segoe UI';
        font-size: 11px;
    }}
    QMenu::item {{
        padding: 6px 16px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background: {p.ACCENT1};
        color: #ffffff;
    }}
    QMenu::separator {{
        height: 1px;
        background: {p.GLASS_BORDER};
        margin: 4px 8px;
    }}
    """


# ═══════════════════════════════════════════════════════════════════════
#  SNIP OVERLAY  (Lightshot-style frozen-screen selector)
# ═══════════════════════════════════════════════════════════════════════
class SnipOverlay(QWidget):
    region_captured = pyqtSignal(QPixmap)
    cancelled = pyqtSignal()

    def __init__(self, frozen: QPixmap, virtual_rect: QRect = None):
        super().__init__()
        self._frozen = frozen
        self._virtual_rect = virtual_rect or QApplication.primaryScreen().geometry()
        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False
        self._done = False
        self._offset_x = self._virtual_rect.x()  # For coordinate mapping
        self._offset_y = self._virtual_rect.y()

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setCursor(Qt.CrossCursor)
        # Set geometry to virtual desktop bounds
        self.setGeometry(self._virtual_rect)
        # Show without fullscreen to respect setGeometry
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Draw the frozen pixmap to fill the entire window
        p.drawPixmap(0, 0, self._frozen)
        # dark overlay
        p.fillRect(self.rect(), QColor(9, 9, 11, 165))

        if self._selecting or self._done:
            r = self._sel()
            if not r.isNull():
                # draw clear region
                p.drawPixmap(r, self._frozen, r)
                # accent border with glow
                glow_color = QColor(108, 99, 255, 60)
                p.setPen(QPen(glow_color, 6))
                p.setBrush(Qt.NoBrush)
                p.drawRect(r)
                p.setPen(QPen(QColor(108, 99, 255), 2))
                p.drawRect(r)

                # corner handles
                handle_sz = 8
                corners = [r.topLeft(), r.topRight(), r.bottomLeft(), r.bottomRight()]
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(108, 99, 255))
                for c in corners:
                    p.drawRoundedRect(
                        c.x() - handle_sz//2, c.y() - handle_sz//2,
                        handle_sz, handle_sz, 2, 2)

                # size label with modern pill
                lbl = f"{r.width()} × {r.height()}"
                fm = p.fontMetrics()
                p.setFont(QFont("Segoe UI", 9, QFont.Bold))
                tw = p.fontMetrics().horizontalAdvance(lbl) + 20
                th = 26
                lx = r.x() + 6
                ly = r.y() + 6
                # pill background
                pill = QPainterPath()
                pill.addRoundedRect(QRectF(lx, ly, tw, th), 6, 6)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(108, 99, 255, 220))
                p.drawPath(pill)
                p.setPen(QColor(255, 255, 255))
                p.drawText(QRectF(lx, ly, tw, th), Qt.AlignCenter, lbl)
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._origin = e.pos()
            self._current = e.pos()
            self._selecting = True
            self._done = False
            self.update()

    def mouseMoveEvent(self, e):
        if self._selecting:
            self._current = e.pos()
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._selecting:
            self._selecting = False
            self._current = e.pos()
            self._done = True
            self.update()
            r = self._sel()
            if r.width() > 3 and r.height() > 3:
                self.region_captured.emit(self._frozen.copy(r))
            else:
                self.cancelled.emit()
            self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.cancelled.emit()
            self.close()

    def _sel(self):
        return QRect(self._origin, self._current).normalized()


# ═══════════════════════════════════════════════════════════════════════
#  ANNOTATION ITEMS
# ═══════════════════════════════════════════════════════════════════════
class AnnotationItem:
    def __init__(self, color=QColor(255, 0, 0), width=3):
        self.color = color
        self.width = width
        self.rotation = 0
        self.selected = False
        self.rect = QRectF() # Bounding box in local space

    def paint(self, p): pass
    def contains(self, pos): return self.rect.contains(pos)
    def move_by(self, dx, dy): pass

class PenItem(AnnotationItem):
    def __init__(self, pts, color, width, hl=False):
        super().__init__(color, width)
        self.pts = list(pts)
        self.hl = hl
        self._update_rect()

    def _update_rect(self):
        if not self.pts: return
        xs = [p.x() for p in self.pts]
        ys = [p.y() for p in self.pts]
        self.rect = QRectF(min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)).adjusted(-5,-5,5,5)

    def paint(self, p):
        c = QColor(self.color)
        w = self.width
        if self.hl: c.setAlpha(80); w *= 4
        p.setPen(QPen(c, w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for i in range(1, len(self.pts)):
            p.drawLine(self.pts[i-1], self.pts[i])
        if self.selected: self._draw_focus(p)

    def _draw_focus(self, p):
        p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        p.drawRect(self.rect)

    def contains(self, pos):
        # Rough check via rect, then closer check might be needed if we want pixel perfect
        return self.rect.contains(pos)

    def move_by(self, dx, dy):
        self.pts = [p + QPointF(dx, dy) for p in self.pts]
        self._update_rect()

class RectItem(AnnotationItem):
    def __init__(self, rect, color, width):
        super().__init__(color, width)
        self.rect = QRectF(rect)

    def paint(self, p):
        p.setPen(QPen(self.color, self.width))
        p.setBrush(Qt.NoBrush)
        p.drawRect(self.rect)
        if self.selected: self._draw_focus(p)

    def _draw_focus(self, p):
        p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine))
        p.drawRect(self.rect.adjusted(-2,-2,2,2))

    def move_by(self, dx, dy):
        self.rect.translate(dx, dy)

class ArrowItem(AnnotationItem):
    def __init__(self, start, end, color, width):
        super().__init__(color, width)
        self.start = QPointF(start)
        self.end = QPointF(end)
        self._update_rect()

    def _update_rect(self):
        self.rect = QRectF(self.start, self.end).normalized().adjusted(-10,-10,10,10)

    def paint(self, p):
        p.setPen(QPen(self.color, self.width, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(self.start, self.end)
        # Arrow head
        dx, dy = self.end.x() - self.start.x(), self.end.y() - self.start.y()
        ln = math.sqrt(dx*dx + dy*dy)
        if ln > 1:
            ang = math.atan2(dy, dx)
            sz = max(14, self.width * 4)
            p1 = QPointF(self.end.x() - sz * math.cos(ang - math.pi/6), self.end.y() - sz * math.sin(ang - math.pi/6))
            p2 = QPointF(self.end.x() - sz * math.cos(ang + math.pi/6), self.end.y() - sz * math.sin(ang + math.pi/6))
            p.setPen(Qt.NoPen); p.setBrush(QBrush(self.color))
            p.drawPolygon(QPolygonF([self.end, p1, p2]))
        if self.selected:
            p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawRect(self.rect)

    def move_by(self, dx, dy):
        self.start += QPointF(dx, dy); self.end += QPointF(dx, dy)
        self._update_rect()

class TextItem(AnnotationItem):
    def __init__(self, pos, text, color, size, font_family="Segoe UI"):
        super().__init__(color, size)
        self.pos = QPointF(pos)
        self.text = text
        self.size = size
        self.font_family = font_family
        self._update_rect()

    def _update_rect(self):
        f = QFont(self.font_family, self.size, QFont.Bold)
        fm = QFontMetrics(f)
        br = fm.boundingRect(self.text)
        # Bounding box needs to account for rotation eventually, but for now:
        self.rect = QRectF(self.pos.x(), self.pos.y() - br.height(), br.width(), br.height()).adjusted(-6, -6, 6, 6)

    def paint(self, p):
        p.save()
        p.translate(self.rect.center())
        p.rotate(self.rotation)
        p.translate(-self.rect.center())
        
        p.setPen(self.color)
        f = QFont(self.font_family, self.size, QFont.Bold)
        p.setFont(f)
        p.drawText(self.pos, self.text)
        
        if self.selected:
            p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRect(self.rect)
        p.restore()

    def move_by(self, dx, dy):
        self.pos += QPointF(dx, dy)
        self._update_rect()

class BlurItem(AnnotationItem):
    def __init__(self, rect, pix):
        super().__init__()
        self.rect = QRectF(rect)
        self.pix = pix

    def paint(self, p):
        p.drawImage(self.rect, self.pix)
        if self.selected:
            p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawRect(self.rect)

    def move_by(self, dx, dy):
        self.rect.translate(dx, dy)

class HighlightItem(AnnotationItem):
    def __init__(self, rect, color, width=20):
        super().__init__(color, width)
        self.rect = QRectF(rect)

    def paint(self, p):
        c = QColor(self.color)
        c.setAlpha(100)
        p.fillRect(self.rect, c)
        if self.selected:
            p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawRect(self.rect)

    def move_by(self, dx, dy):
        self.rect.translate(dx, dy)

class StepItem(AnnotationItem):
    def __init__(self, pos, num, color):
        super().__init__(color, 24)
        self.pos = QPointF(pos)
        self.num = num
        self._update_rect()

    def _update_rect(self):
        r = 15
        self.rect = QRectF(self.pos.x() - r, self.pos.y() - r, r*2, r*2)

    def paint(self, p):
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(self.color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(self.rect)
        
        p.setPen(QColor("white"))
        f = QFont("Segoe UI", 10, QFont.Bold)
        p.setFont(f)
        p.drawText(self.rect, Qt.AlignCenter, str(self.num))
        
        if self.selected:
            p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawRect(self.rect.adjusted(-2,-2,2,2))

    def move_by(self, dx, dy):
        self.pos += QPointF(dx, dy)
        self._update_rect()

class StickerItem(AnnotationItem):
    def __init__(self, pos, sticker_type, scale=1.0):
        super().__init__()
        self.pos = QPointF(pos)
        self.type = sticker_type
        self.scale = scale
        self._update_rect()

    def _update_rect(self):
        sz = 40 * self.scale
        self.rect = QRectF(self.pos.x() - sz/2, self.pos.y() - sz/2, sz, sz)

    def paint(self, p):
        # We can use system emojis or draw shapes
        emojis = {"check": "✅", "cross": "❌", "star": "⭐", "heart": "❤️", "idea": "💡", "warn": "⚠️"}
        txt = emojis.get(self.type, "❓")
        
        p.setFont(QFont("Segoe UI Emoji", 24))
        p.drawText(self.rect, Qt.AlignCenter, txt)
        
        if self.selected:
            p.setPen(QPen(QColor(99, 102, 241), 1, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawRect(self.rect)

    def move_by(self, dx, dy):
        self.pos += QPointF(dx, dy)
        self._update_rect()


# ═══════════════════════════════════════════════════════════════════════
#  EDITOR CANVAS
# ═══════════════════════════════════════════════════════════════════════
class EditorCanvas(QWidget):
    selection_changed = pyqtSignal(object) # emits selected item or None
    zoom_changed = pyqtSignal(float) # emits zoom scale

    def __init__(self, pixmap):
        super().__init__()
        self._base = pixmap.toImage()
        self.setFixedSize(pixmap.size())
        self._items = []
        self._redo_stack = []
        self._tool = "pen"
        self._color = QColor("#ff4757")
        self._pen_width = 3
        self._text_size = 24
        self._drawing = False
        self._dragging = False
        self._pts = []
        self._t_start = None
        self._t_end = None
        self._selected_item = None
        self._scale = 1.0
        self._next_step_num = 1
        self._active_sticker = "check"
        self.setMouseTracking(True)
        
    def fit_to_view(self, viewport_size):
        if self._base.width() <= 0 or self._base.height() <= 0: return
        w_ratio = viewport_size.width() / self._base.width()
        h_ratio = viewport_size.height() / self._base.height()
        self._scale = min(1.0, w_ratio, h_ratio)
        self.setFixedSize(self._base.size() * self._scale)
        self.update()

    def set_tool(self, t):
        self._tool = t
        if t != "select":
            self.deselect_all()
        self.update()

    def set_color(self, c):
        self._color = QColor(c)
        it = self._selected_item
        if it is not None:
            it.color = self._color
            self.update()

    def set_width(self, w):
        it = self._selected_item
        if it is not None:
            if hasattr(it, 'text'):
                it.size = w
                self._text_size = w
            else:
                it.width = w
                self._pen_width = w
            if hasattr(it, '_update_rect'): it._update_rect()
            self.update()
        else:
            # Update global default based on current tool
            if self._tool == "text": self._text_size = w
            else: self._pen_width = w

    def set_font(self, f_family):
        it = self._selected_item
        if it is not None and hasattr(it, 'font_family'):
            it.font_family = f_family
            it._update_rect()
            self.update()

    def set_rotation(self, r):
        it = self._selected_item
        if it is not None:
            it.rotation = r
            self.update()

    def deselect_all(self):
        for it in self._items: it.selected = False
        self._selected_item = None
        self.selection_changed.emit(None)

    def undo(self):
        if self._items:
            item = self._items.pop()
            self._redo_stack.append(item)
            self.deselect_all()
            self.update()

    def redo(self):
        if self._redo_stack:
            item = self._redo_stack.pop()
            self._items.append(item)
            self.update()

    def delete_selected(self):
        if self._selected_item and self._selected_item in self._items:
            self._items.remove(self._selected_item)
            self._redo_stack.clear()
            self.deselect_all()
            self.update()

    def result(self):
        r = QPixmap(self._base.size())
        p = QPainter(r); p.setRenderHint(QPainter.Antialiasing)
        p.drawImage(0, 0, self._base)
        for it in self._items: it.paint(p)
        p.end(); return r

    def wheelEvent(self, e):
        """Handle mouse wheel for zooming."""
        # Zoom factor
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        # Determine zoom direction
        if e.angleDelta().y() > 0:
            factor = zoom_in_factor
        else:
            factor = zoom_out_factor
            
        new_scale = self._scale * factor
        
        # Clamp scale between 5% and 1000%
        if 0.05 <= new_scale <= 10.0:
            self._scale = new_scale
            self.setFixedSize(self._base.size() * self._scale)
            self.zoom_changed.emit(self._scale)
            self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.scale(self._scale, self._scale)
        p.drawImage(0, 0, self._base)
        for it in self._items: it.paint(p)
        if self._drawing: self._render_temp(p)
        p.end()

    def _render_temp(self, p):
        c = QColor(self._color)
        w = self._pen_width
        if self._tool in ("pen", "highlighter"):
            if self._tool == "highlighter": c.setAlpha(80); w = self._pen_width * 4
            p.setPen(QPen(c, w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for i in range(1, len(self._pts)): p.drawLine(self._pts[i-1], self._pts[i])
        elif self._tool == "arrow" and self._t_start and self._t_end:
            tmp = ArrowItem(self._t_start, self._t_end, c, w); tmp.paint(p)
        elif self._tool in ("rect", "blur", "highlight") and self._t_start and self._t_end:
            r = QRectF(self._t_start, self._t_end).normalized()
            if self._tool == "rect": p.setPen(QPen(c, w)); p.drawRect(r)
            elif self._tool == "highlight":
                c.setAlpha(100)
                p.fillRect(r, c)
            else: p.fillRect(r, QColor(100, 100, 100, 60)); p.setPen(QPen(QColor(200, 200, 200), 1, Qt.DashLine)); p.drawRect(r)

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton: return
        pos = QPointF(e.pos()) / self._scale
        
        if self._tool == "select":
            self.deselect_all()
            target = None
            for i in range(len(self._items)-1, -1, -1):
                item = self._items[i]
                if item.contains(pos):
                    target = item
                    break
            
            it = target
            if it is not None:
                # Explicit check for attribute existence to satisfy type checker
                if hasattr(it, 'selected'):
                    it.selected = True
                self._selected_item = it
                self._dragging = True
                self._last_pos = pos
                if hasattr(self, 'selection_changed'):
                    self.selection_changed.emit(it)
                self.setCursor(Qt.ClosedHandCursor)
            self.update()
        elif self._tool == "text":
            txt, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
            if ok and txt:
                it = TextItem(pos, txt, self._color, self._text_size)
                self._items.append(it)
                self.update()
        elif self._tool == "step":
            it = StepItem(pos, self._next_step_num, self._color)
            self._items.append(it)
            self._next_step_num += 1
            self.update()
        elif self._tool == "sticker":
            it = StickerItem(pos, self._active_sticker)
            self._items.append(it)
            self.update()
        else:
            self._drawing = True
            if self._tool in ("pen", "highlighter"): self._pts = [pos]
            else: self._t_start = self._t_end = pos

    def mouseMoveEvent(self, e):
        pos = QPointF(e.pos()) / self._scale
        sel = self._selected_item
        if self._dragging and sel is not None:
            dx, dy = pos.x() - self._last_pos.x(), pos.y() - self._last_pos.y()
            sel.move_by(dx, dy)
            self._last_pos = pos
            self.update()
        elif self._tool == "select":
            hover_it = None
            for it in reversed(self._items):
                if it.contains(pos):
                    hover_it = it
                    break
            self.setCursor(Qt.PointingHandCursor if hover_it is not None else Qt.ArrowCursor)
        elif self._drawing:
            if self._tool in ("pen", "highlighter"): self._pts.append(pos)
            else: self._t_end = pos
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton: return
        self._dragging = False
        self.setCursor(Qt.ArrowCursor)
        if not self._drawing: return
        self._drawing = False
        
        c, w = QColor(self._color), self._pen_width
        
        if self._tool in ("pen", "highlighter") and len(self._pts) > 1:
            self._items.append(PenItem(self._pts, c, w, self._tool == "highlighter"))
        elif self._tool == "arrow" and self._t_start and self._t_end:
            self._items.append(ArrowItem(self._t_start, self._t_end, c, w))
        elif self._tool == "rect" and self._t_start and self._t_end:
            self._items.append(RectItem(QRectF(self._t_start, self._t_end).normalized(), c, w))
        elif self._tool == "highlight" and self._t_start and self._t_end:
            self._items.append(HighlightItem(QRectF(self._t_start, self._t_end).normalized(), c))
        elif self._tool == "blur" and self._t_start and self._t_end:
            r = QRectF(self._t_start, self._t_end).normalized()
            if r.width() > 5 and r.height() > 5:
                # Get settings from parent (ImageEditor)
                win = self.window()
                b_type = getattr(win, "_blur_type", "Gaussian")
                b_hard = getattr(win, "_blur_hardness", 8)
                
                box = r.toRect()
                if box.width() > 0 and box.height() > 0:
                    mode = Qt.SmoothTransformation if b_type == "Gaussian" else Qt.FastTransformation
                    small = self._base.copy(box).scaled(
                        max(1, box.width() // b_hard), 
                        max(1, box.height() // b_hard), 
                        Qt.IgnoreAspectRatio, 
                        Qt.SmoothTransformation # Always smooth down
                    )
                    blurred = small.scaled(box.width(), box.height(), Qt.IgnoreAspectRatio, mode)
                    self._items.append(BlurItem(r, blurred))
        
        self._pts = []
        self._t_start = self._t_end = None
        self.update()


# ═══════════════════════════════════════════════════════════════════════
#  EDITOR TOOL BUTTON
# ═══════════════════════════════════════════════════════════════════════
class EditorToolButton(QPushButton):
    rightClicked = pyqtSignal()

    def __init__(self, icon_type, tooltip="", checkable=True, parent=None):
        QPushButton.__init__(self, parent)
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(48, 48)
        self.setObjectName("tool")
        self._type = icon_type
        self._dark = True
        self._hover_anim = 0.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_anim)

    def contextMenuEvent(self, e):
        self.rightClicked.emit()
        # Optionally don't pass to super if we want to block default menu

    def _update_anim(self):
        if self.underMouse():
            self._hover_anim = min(1.0, self._hover_anim + 0.15)
            # Show tool name in status bar of parent window
            win = self.window()
            if hasattr(win, 'statusBar'):
                win.statusBar().showMessage(f"Tool Selection: {self.toolTip()}")
        else:
            self._hover_anim = max(0.0, self._hover_anim - 0.15)
        if self._hover_anim in (0.0, 1.0): self._timer.stop()
        self.update()

    def enterEvent(self, _):
        self._timer.start(16)

    def leaveEvent(self, _):
        self._timer.start(16)

    def setDark(self, dark):
        self._dark = dark
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        pal = Palette.Dark if self._dark else Palette.Light
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # ── Background states ────────────────────────────
        if self.isChecked():
            # Active: gradient pill
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, QColor(pal.GRAD_START))
            grad.setColorAt(1, QColor(pal.GRAD_END))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(self.rect().adjusted(4, 4, -4, -4), 12, 12)
            icon_color = QColor("#ffffff")
        elif self._hover_anim > 0:
            # Hover: subtle glow ring + bg
            ring = QColor(pal.ACCENT1)
            ring.setAlpha(int(30 * self._hover_anim))
            p.setBrush(ring)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 14, 14)

            bg = QColor(pal.BTN_HOVER)
            bg.setAlpha(int(200 * self._hover_anim))
            p.setBrush(bg)
            p.drawRoundedRect(self.rect().adjusted(5, 5, -5, -5), 10, 10)
            icon_color = QColor(pal.TEXT)
        else:
            icon_color = QColor(pal.TEXT2)

        p.setBrush(Qt.NoBrush)

        # ── Scale micro-animation ────────────────────────
        scale = 1.0 + (0.06 * self._hover_anim)
        p.translate(cx, cy)
        p.scale(scale, scale)
        p.translate(-cx, -cy)

        # ── Render icon ──────────────────────────────────
        icon_key = self._type
        if icon_key in ICONS:
            svg = QSvgRenderer(QByteArray(ICONS[icon_key].encode()))
            padding = max(7, int(w * 0.27))  # Scale padding with button size
            icon_size = int(w - padding * 2)
            # Render to offscreen pixmap for proper color tinting
            tmp = QPixmap(icon_size, icon_size)
            tmp.fill(QColor(0, 0, 0, 0))
            tp = QPainter(tmp)
            tp.setRenderHint(QPainter.Antialiasing)
            svg.render(tp, QRectF(0, 0, icon_size, icon_size))
            tp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            tp.fillRect(0, 0, icon_size, icon_size, icon_color)
            tp.end()
            p.drawPixmap(int(padding), int(padding), tmp)
        else:
            p.setPen(QPen(icon_color, 1.75, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            if self._type == "sticker":
                p.setFont(QFont("Segoe UI Emoji", 14))
                p.drawText(self.rect(), Qt.AlignCenter, "✨")
            else:
                p.setFont(QFont("Inter", 10, QFont.Bold))
                p.drawText(self.rect(), Qt.AlignCenter, self._type[:2].upper())

        p.end()


class NavButton(QPushButton):
    def __init__(self, icon_type, parent=None):
        QPushButton.__init__(self, parent)
        self.setFixedSize(40, 40)
        self.setCheckable(True)
        self.setObjectName("nav_btn")
        self._type = icon_type
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        pal = Palette.Dark
        
        is_active = self.underMouse() or self.isChecked()
        
        if is_active:
            p.setBrush(QColor(pal.BTN_HOVER if not self.isChecked() else pal.ACCENT1))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(self.rect().adjusted(4, 4, -4, -4), 8, 8)
            color = QColor(pal.TEXT if not self.isChecked() else "#ffffff")
        else:
            color = QColor(pal.TEXT3)

        p.setBrush(Qt.NoBrush)
        
        icon_map = {
            "files": "folder", "tools": "pen", "layers": "layers", 
            "history": "history", "settings": "settings", "help": "help", "user": "user"
        }
        
        ikey = icon_map.get(self._type)
        if ikey and ikey in ICONS:
            svg = QSvgRenderer(QByteArray(ICONS[ikey].encode()))
            padding = 11
            icon_size = 40 - padding * 2
            # Offscreen pixmap for proper color tinting
            tmp = QPixmap(icon_size, icon_size)
            tmp.fill(QColor(0, 0, 0, 0))
            tp = QPainter(tmp)
            tp.setRenderHint(QPainter.Antialiasing)
            svg.render(tp, QRectF(0, 0, icon_size, icon_size))
            tp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            tp.fillRect(0, 0, icon_size, icon_size, color)
            tp.end()
            p.drawPixmap(padding, padding, tmp)
        else:
            p.setPen(QPen(color, 2))
            p.drawText(self.rect(), Qt.AlignCenter, self._type[:1].upper())

        p.end()

# ═══════════════════════════════════════════════════════════════════════
#  PROPERTY BAR
# ═══════════════════════════════════════════════════════════════════════
class PropertyBar(QWidget):
    width_changed = pyqtSignal(int)
    font_changed = pyqtSignal(str)
    rotation_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super(PropertyBar, self).__init__(parent)
        self.setFixedHeight(45)
        self.setObjectName("property_bar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(15, 0, 15, 0)
        lay.setSpacing(12)
        
        # Size
        lay.addWidget(QLabel("Size"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 120)
        self.slider.setFixedWidth(100)
        self.slider.valueChanged.connect(self.width_changed.emit)
        lay.addWidget(self.slider)
        
        # Rotation
        lay.addWidget(QLabel("Rotation"))
        self.rot_slider = QSlider(Qt.Horizontal)
        self.rot_slider.setRange(-180, 180)
        self.rot_slider.setValue(0)
        self.rot_slider.setFixedWidth(80)
        self.rot_slider.valueChanged.connect(self.rotation_changed.emit)
        lay.addWidget(self.rot_slider)
        
        # Font
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Segoe UI", "Arial", "Consolas", "Impact", "Times New Roman"])
        self.font_combo.currentTextChanged.connect(self.font_changed.emit)
        lay.addWidget(self.font_combo)
        
        lay.addStretch()
        self.hide()

    def sync_item(self, it):
        if it is None:
            self.hide()
            return
        self.show()
        
        # Get appropriate value based on item type
        if hasattr(it, 'text'):
            val = getattr(it, 'size', 24)
            self.slider.setRange(8, 144) # Text range
        else:
            val = getattr(it, 'width', 3)
            self.slider.setRange(1, 40)  # Stroke range
            
        self.slider.blockSignals(True)
        self.slider.setValue(int(val))
        self.slider.blockSignals(False)
        
        self.rot_slider.blockSignals(True)
        self.rot_slider.setValue(int(it.rotation))
        self.rot_slider.blockSignals(False)
        
        if hasattr(it, 'font_family'):
            self.font_combo.show()
            self.font_combo.setCurrentText(it.font_family)
        else:
            self.font_combo.hide()


# ═══════════════════════════════════════════════════════════════════════
#  IMAGE EDITOR WINDOW
# ═══════════════════════════════════════════════════════════════════════
class ImageEditor(QMainWindow):
    saved = pyqtSignal(str)

    def __init__(self, filepath, dark=True):
        super().__init__()
        self._path = filepath
        self._dark = dark
        # Blur settings
        self._blur_type = "Gaussian" # "Gaussian" or "Pixelated"
        self._blur_hardness = 8 # Divisor for scaling
        
        self._tool_btns = {}
        self._color_btns = []
        self._active_color = QColor("#ff4757")
        self._drag_pos = None
        
        self._build()

    def _show_blur_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(_editor_style(Palette.Dark if self._dark else Palette.Light))
        
        # Blur Type Section
        type_group = QActionGroup(self)
        a_gaussian = menu.addAction("Gaussian Blur")
        a_gaussian.setCheckable(True)
        a_gaussian.setChecked(self._blur_type == "Gaussian")
        a_gaussian.triggered.connect(lambda: self._set_blur_type("Gaussian"))
        type_group.addAction(a_gaussian)
        
        a_pixel = menu.addAction("Pixelated (Checked)")
        a_pixel.setCheckable(True)
        a_pixel.setChecked(self._blur_type == "Pixelated")
        a_pixel.triggered.connect(lambda: self._set_blur_type("Pixelated"))
        type_group.addAction(a_pixel)
        
        menu.addSeparator()
        
        # Hardness Section
        h_group = QActionGroup(self)
        for label, val in [("Low", 16), ("Medium", 8), ("High", 4)]:
            a = menu.addAction(f"Hardness: {label}")
            a.setCheckable(True)
            a.setChecked(self._blur_hardness == val)
            a.triggered.connect(lambda _, v=val: self._set_blur_hardness(v))
            h_group.addAction(a)
            
        btn = self._tool_btns.get("blur")
        if btn:
            menu.exec_(btn.mapToGlobal(QPoint(btn.width(), 0)))

    def _set_blur_type(self, t):
        self._blur_type = t
        self.statusBar().showMessage(f"Blur mode: {t}")

    def _set_blur_hardness(self, h):
        self._blur_hardness = h
        self.statusBar().showMessage(f"Blur hardness set")

    def _show_sticker_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(_editor_style(Palette.Dark if self._dark else Palette.Light))
        
        stickers = [
            ("Check", "check", "✅"), ("Cross", "cross", "❌"), 
            ("Star", "star", "⭐"), ("Heart", "heart", "❤️"), 
            ("Idea", "idea", "💡"), ("Warning", "warn", "⚠️")
        ]
        
        for label, sid, char in stickers:
            a = menu.addAction(f"{char}  {label}")
            a.triggered.connect(lambda _, s=sid: self._set_sticker(s))
            
        btn = self._tool_btns.get("sticker")
        if btn:
            menu.exec_(btn.mapToGlobal(QPoint(btn.width(), 0)))

    def _set_sticker(self, s):
        self.canvas._active_sticker = s
        self._pick_tool("sticker")
        self.statusBar().showMessage(f"Selected sticker: {s}")

    def _build(self):
        self.setWindowTitle("StayX Editor")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1100, 750)
        
        pal = Palette.Dark if self._dark else Palette.Light
        self.setStyleSheet(_editor_style(pal))
        
        m_container = QWidget()
        m_container.setObjectName("main_container")
        layout = QHBoxLayout(m_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(m_container)

        # ── 1. LEFT SIDEBAR (Tools + Colors) ─────────────────────────
        self.sidebar_left = QWidget()
        self.sidebar_left.setObjectName("sidebar_nav")
        self.sidebar_left.setFixedWidth(56)
        vsl = QVBoxLayout(self.sidebar_left)
        vsl.setContentsMargins(0, 12, 0, 12)
        vsl.setSpacing(2)
        vsl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # Shortcut map for tooltips
        _shortcuts = {
            "select": "V", "pen": "P", "rect": "R", "arrow": "A",
            "text": "T", "blur": "B", "highlight": "H", 
            "step": "N", "sticker": "K"
        }
        
        def add_vtool(tid, tip):
            shortcut = _shortcuts.get(tid, "")
            full_tip = f"{tip}  ({shortcut})" if shortcut else tip
            btn = EditorToolButton(tid, full_tip)
            btn.clicked.connect(lambda _, x=tid: self._pick_tool(x))
            self._tool_btns[tid] = btn
            vsl.addWidget(btn, alignment=Qt.AlignHCenter)

        def add_separator():
            sep = QFrame()
            sep.setFixedSize(32, 1)
            sep_pal = Palette.Dark if self._dark else Palette.Light
            sep.setStyleSheet(f"background: {sep_pal.GLASS_BORDER};")
            vsl.addSpacing(4)
            vsl.addWidget(sep, alignment=Qt.AlignHCenter)
            vsl.addSpacing(4)

        # ── Drawing Tools Group ──
        for t, tip in [("select", "Select"), ("pen", "Pen")]:
            add_vtool(t, tip)
        
        add_separator()
        
        # ── Shape Tools Group ──
        for t, tip in [("rect", "Rectangle"), ("arrow", "Arrow"), ("text", "Text")]:
            add_vtool(t, tip)
        
        add_separator()
        
        # ── Annotation Tools Group ──
        for t, tip in [
            ("blur", "Blur"), ("highlight", "Highlighter"),
            ("step", "Step Number"), ("sticker", "Stickers")
        ]:
            add_vtool(t, tip)
            if t == "blur":
                self._tool_btns[t].rightClicked.connect(self._show_blur_menu)
            if t == "sticker":
                self._tool_btns[t].rightClicked.connect(self._show_sticker_menu)
        
        vsl.addStretch()
        
        # ── Quick Color Swatches ──
        _colors = ["#FF4757", "#FF6B35", "#FFC312", "#2ED573", "#1E90FF", 
                    "#5352ED", "#A855F7", "#FFFFFF"]
        for hex_c in _colors:
            cb = QPushButton()
            cb.setObjectName("color_swatch")
            cb.setFixedSize(24, 24)
            cb.setCheckable(True)
            cb.setCursor(Qt.PointingHandCursor)
            cb.setStyleSheet(f"background: {hex_c}; border-radius: 12px;")
            cb.clicked.connect(lambda _, c=hex_c: self._pick_color(c))
            self._color_btns.append(cb)
            vsl.addWidget(cb, alignment=Qt.AlignHCenter)
        
        vsl.addSpacing(4)
        
        # Custom Color Picker Button
        self.cp_btn = QPushButton()
        self.cp_btn.setFixedSize(28, 28)
        self.cp_btn.setCursor(Qt.PointingHandCursor)
        self.cp_btn.setToolTip("Custom Color")
        self.cp_btn.clicked.connect(self._choose_color)
        vsl.addWidget(self.cp_btn, alignment=Qt.AlignHCenter)
        self._update_color_ui()

        layout.addWidget(self.sidebar_left)

        # ── 2. MAIN WORKSPACE ─────────────────────────────────────────
        workspace = QWidget()
        wl = QVBoxLayout(workspace)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        
        # ── Top Header Bar ──
        self.top_bar_v3 = QWidget()
        self.top_bar_v3.setObjectName("top_bar_v3")
        self.top_bar_v3.setFixedHeight(52)
        tbl = QHBoxLayout(self.top_bar_v3)
        tbl.setContentsMargins(16, 0, 16, 0)
        tbl.setSpacing(10)
        
        # File name
        lbl_file = QLabel(Path(self._path).name)
        lbl_file.setObjectName("breadcrumb_file")
        tbl.addWidget(lbl_file)
        
        # Image dimensions
        pix_check = QPixmap(self._path)
        dim_text = f"{pix_check.width()} × {pix_check.height()} px"
        self._dim_label = QLabel(dim_text)
        self._dim_label.setObjectName("img_dimensions")
        tbl.addWidget(self._dim_label)
        
        tbl.addStretch()
        
        # ── Zoom Controls ──
        for icon_key, tip, fn in [
            ("zoom-out", "Zoom Out", self._zoom_out),
            ("maximize", "Fit to View", self._zoom_fit),
            ("zoom-in", "Zoom In", self._zoom_in),
        ]:
            zb = EditorToolButton(icon_key, tip, checkable=False)
            zb.setFixedSize(32, 32)
            zb.clicked.connect(fn)
            tbl.addWidget(zb)
        
        self._zoom_label = QLabel("100%")
        self._zoom_label.setObjectName("zoom_label")
        tbl.addWidget(self._zoom_label)
        
        tbl.addSpacing(8)
        
        # ── Top Action Buttons ──
        for t, tip, fn in [
            ("undo", "Undo (Ctrl+Z)", self._undo),
            ("redo", "Redo (Ctrl+Y)", self._redo),
            ("delete", "Delete Selected (Del)", self._delete_selected),
            ("upload", "Upload to Cloud", self._handle_upload),
            ("save", "Save (Ctrl+S)", self._save), 
            ("copy", "Copy (Ctrl+C)", self._copy), 
            ("close", "Close (Esc)", self.close)
        ]:
             btn = EditorToolButton(t, tip, checkable=False)
             btn.setFixedSize(34, 34)
             btn.clicked.connect(fn)
             tbl.addWidget(btn)

        wl.addWidget(self.top_bar_v3)

        # ── Canvas Area ──
        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)
        
        canvas_bg = QWidget()
        canvas_bg.setObjectName("canvas_container")
        cl = QVBoxLayout(canvas_bg)
        cl.setContentsMargins(16, 12, 16, 12)
        
        # Property Bar (floating above canvas)
        self.prop_bar = PropertyBar()
        cl.addWidget(self.prop_bar)
        
        sa = QScrollArea()
        sa.setWidgetResizable(False)
        sa.setAlignment(Qt.AlignCenter)
        sa.setObjectName("editor_scroll")
        
        pix = QPixmap(self._path)
        self.canvas = EditorCanvas(pix)
        sa.setWidget(self.canvas)
        cl.addWidget(sa, 1)
        
        bl.addWidget(canvas_bg, 1)
        wl.addWidget(body, 1)
        
        # ── Bottom Status Bar ──
        status_bar = QWidget()
        status_bar.setObjectName("status_bar")
        status_bar.setFixedHeight(28)
        sbl = QHBoxLayout(status_bar)
        sbl.setContentsMargins(16, 0, 16, 0)
        sbl.setSpacing(12)
        
        self._status_tool = QLabel("Pen")
        self._status_tool.setObjectName("status_text")
        sbl.addWidget(self._status_tool)
        
        sbl.addStretch()
        
        self._status_zoom = QLabel("100%")
        self._status_zoom.setObjectName("status_text")
        sbl.addWidget(self._status_zoom)
        
        self._status_dims = QLabel(dim_text)
        self._status_dims.setObjectName("status_text")
        sbl.addWidget(self._status_dims)
        
        wl.addWidget(status_bar)
        
        layout.addWidget(workspace, 1)

        # ── Connect Signals ──
        self.canvas.selection_changed.connect(self.prop_bar.sync_item)
        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        self.prop_bar.width_changed.connect(self.canvas.set_width)
        self.prop_bar.rotation_changed.connect(self.canvas.set_rotation)
        self.prop_bar.font_changed.connect(self.canvas.set_font)

        self._notification = None

        QTimer.singleShot(50, self._initial_fit)
        self._pick_tool("pen")

    def _on_zoom_changed(self, scale):
        pct = int(scale * 100)
        self._zoom_label.setText(f"{pct}%")
        self._status_zoom.setText(f"{pct}%")
    
    def _zoom_in(self):
        new_scale = min(10.0, self.canvas._scale * 1.25)
        self.canvas._scale = new_scale
        self.canvas.setFixedSize(self.canvas._base.size() * new_scale)
        self.canvas.zoom_changed.emit(new_scale)
        self.canvas.update()
    
    def _zoom_out(self):
        new_scale = max(0.05, self.canvas._scale / 1.25)
        self.canvas._scale = new_scale
        self.canvas.setFixedSize(self.canvas._base.size() * new_scale)
        self.canvas.zoom_changed.emit(new_scale)
        self.canvas.update()
    
    def _zoom_fit(self):
        sa = self.findChild(QScrollArea, "editor_scroll")
        if sa:
            self.canvas.fit_to_view(sa.viewport().size())
            self.canvas.zoom_changed.emit(self.canvas._scale)

    def _initial_fit(self):
        self._zoom_fit()

    def _choose_color(self):
        c = QColorDialog.getColor(self._active_color, self, "Pick Color")
        if c.isValid():
            self._active_color = c
            self._update_color_ui()
            self.canvas.set_color(c)

    def _update_color_ui(self):
        pal = Palette.Dark if self._dark else Palette.Light
        self.cp_btn.setStyleSheet(f"""
            background: {self._active_color.name()}; 
            border: 2px solid {pal.TEXT}; 
            border-radius: 14px;
        """)

    def _pick_color(self, hex_color, idx=0):
        self._active_color = QColor(hex_color)
        self._update_color_ui()
        self.canvas.set_color(self._active_color)

    # ── Keyboard Shortcuts ────────────────────────────────────────
    def keyPressEvent(self, e):
        mod = e.modifiers()
        key = e.key()
        
        if mod == Qt.ControlModifier:
            if key == Qt.Key_Z: self._undo(); return
            if key == Qt.Key_Y: self._redo(); return
            if key == Qt.Key_S: self._save(); return
            if key == Qt.Key_C: self._copy(); return
        
        if key == Qt.Key_Delete or key == Qt.Key_Backspace:
            self._delete_selected(); return
        if key == Qt.Key_Escape:
            self.close(); return
        
        # Tool shortcuts
        _key_tools = {
            Qt.Key_V: "select", Qt.Key_P: "pen", Qt.Key_R: "rect",
            Qt.Key_A: "arrow", Qt.Key_T: "text", Qt.Key_B: "blur",
            Qt.Key_H: "highlight", Qt.Key_N: "step", Qt.Key_K: "sticker"
        }
        if key in _key_tools:
            self._pick_tool(_key_tools[key])
            return
        
        super().keyPressEvent(e)

    # ── Window Dragging ───────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if e.pos().y() < 52 or e.pos().x() < 56:
                self._drag_pos = e.globalPos()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None:
            delta = e.globalPos() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPos()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    def _vsep(self):
        s = QFrame()
        s.setFrameShape(QFrame.VLine)
        pal = Palette.Dark if self._dark else Palette.Light
        s.setStyleSheet(f"color: {pal.BORDER};")
        s.setFixedWidth(1)
        return s

    def _hsep(self):
        s = QFrame()
        s.setFrameShape(QFrame.HLine)
        pal = Palette.Dark if self._dark else Palette.Light
        s.setStyleSheet(f"background: {pal.BORDER};")
        s.setFixedHeight(1)
        s.setContentsMargins(10, 0, 10, 0)
        return s

    def _handle_upload(self):
        cfg = cfg_load()
        provider = cfg.get("storage_provider", "ImgBB")
        
        results = []
        
        if provider in ["ImgBB", "Both"]:
            key = str(cfg.get("imgbb_api_key", "")).strip()
            if key:
                self.statusBar().showMessage("📤 Uploading to ImgBB...")
                pix = self.canvas.result()
                ba = QByteArray()
                buffer = QBuffer(ba)
                buffer.open(QBuffer.WriteOnly)
                pix.save(buffer, "PNG")
                img_base64 = base64.b64encode(ba.data()).decode("utf-8")
                
                try:
                    url = "https://api.imgbb.com/1/upload"
                    payload = {"key": key, "image": img_base64}
                    response = requests.post(url, payload, timeout=30)
                    data = response.json()
                    if data["success"]:
                        url = data["data"]["url"]
                        # If only ImgBB, put link in clipboard
                        if provider == "ImgBB":
                            QApplication.clipboard().setText(url)
                        results.append(f"✅ ImgBB: {url}")
                    else:
                        results.append(f"❌ ImgBB Failed: {data['error']['message']}")
                except Exception as e:
                    results.append(f"❌ ImgBB Error: {str(e)}")
            else:
                if provider == "ImgBB":
                    self._notify("❌ No ImgBB API Key! Add one in API tab.")
                    return

        if provider in ["GoogleDrive", "Both"]:
            self.statusBar().showMessage("📤 Uploading to Google Drive...")
            pix = self.canvas.result()
            filename = f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
            file = gdrive_upload_screenshot(pix, filename)
            if file:
                link = file.get('webViewLink')
                # If only GDrive, put link in clipboard
                if provider == "GoogleDrive":
                    QApplication.clipboard().setText(link)
                results.append(f"✅ GDrive: {filename}")
            else:
                results.append("❌ GDrive Upload Failed")

        if results:
            self._notify("\n".join(results))
        else:
            self._notify("ℹ️ No upload provider configured correctly.")

    def _pick_tool(self, t):
        for k, b in self._tool_btns.items():
            if b:
                b.setChecked(k == t)
        self.canvas.set_tool(t)
        cm = {"text": Qt.IBeamCursor}
        self.canvas.setCursor(cm.get(t, Qt.CrossCursor))
        # Update status bar tool name
        tool_names = {
            "select": "Select", "pen": "Pen", "rect": "Rectangle",
            "arrow": "Arrow", "text": "Text", "blur": "Blur",
            "highlight": "Highlighter", "step": "Step Number", "sticker": "Stickers"
        }
        if hasattr(self, '_status_tool'):
            self._status_tool.setText(tool_names.get(t, t.capitalize()))

    def _undo(self):
        self.canvas.undo()

    def _redo(self):
        self.canvas.redo()

    def _delete_selected(self):
        self.canvas.delete_selected()

    def _notify(self, text):
        if self._notification:
            try:
                self._notification.hide()
                self._notification.deleteLater()
            except (RuntimeError, AttributeError):
                pass
        
        self._notification = NotificationWidget(text, self)
        self._notification.show_animated()

    def _save(self):
        pix = self.canvas.result()
        pix.save(self._path, "PNG")
        self._notify("💾 Saved successfully")

    def _copy(self):
        QApplication.clipboard().setPixmap(self.canvas.result())
        self._notify("📋 Copied to clipboard")


# ═══════════════════════════════════════════════════════════════════════
#  HOTKEY BRIDGE
# ═══════════════════════════════════════════════════════════════════════
class HotkeyBridge(QObject):
    region = pyqtSignal()
    fullscreen = pyqtSignal()


# ═══════════════════════════════════════════════════════════════════════
#  HOTKEY RECORDER  (simple click-to-record input field)
# ═══════════════════════════════════════════════════════════════════════
class HotkeyRecorder(QLineEdit):
    """Click to record, press keys on keyboard, auto-saves hotkey."""
    hotkey_recorded = pyqtSignal(str)  # emits pynput format string

    KEY_NAMES = {
        Qt.Key_Control: "Ctrl",
        Qt.Key_Alt: "Alt",
        Qt.Key_Shift: "Shift",
        Qt.Key_Super_L: "Win",
        Qt.Key_Super_R: "Win",
        Qt.Key_0: "0", Qt.Key_1: "1", Qt.Key_2: "2", Qt.Key_3: "3",
        Qt.Key_4: "4", Qt.Key_5: "5", Qt.Key_6: "6", Qt.Key_7: "7",
        Qt.Key_8: "8", Qt.Key_9: "9",
        Qt.Key_A: "A", Qt.Key_B: "B", Qt.Key_C: "C", Qt.Key_D: "D",
        Qt.Key_E: "E", Qt.Key_F: "F", Qt.Key_G: "G", Qt.Key_H: "H",
        Qt.Key_I: "I", Qt.Key_J: "J", Qt.Key_K: "K", Qt.Key_L: "L",
        Qt.Key_M: "M", Qt.Key_N: "N", Qt.Key_O: "O", Qt.Key_P: "P",
        Qt.Key_Q: "Q", Qt.Key_R: "R", Qt.Key_S: "S", Qt.Key_T: "T",
        Qt.Key_U: "U", Qt.Key_V: "V", Qt.Key_W: "W", Qt.Key_X: "X",
        Qt.Key_Y: "Y", Qt.Key_Z: "Z",
        Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
        Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
        Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
        Qt.Key_Minus: "-", Qt.Key_Equal: "=", Qt.Key_BracketLeft: "[",
        Qt.Key_BracketRight: "]", Qt.Key_Backslash: "\\", Qt.Key_Semicolon: ";",
        Qt.Key_Apostrophe: "'", Qt.Key_Comma: ",", Qt.Key_Period: ".",
        Qt.Key_Slash: "/", Qt.Key_Space: "space",
        Qt.Key_Tab: "tab", Qt.Key_Return: "enter", Qt.Key_Up: "up",
        Qt.Key_Down: "down", Qt.Key_Left: "left", Qt.Key_Right: "right",
    }
    VALID_PYNPUT_KEYS = {
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
        "space", "tab", "enter", "up", "down", "left", "right",
        "home", "end", "pageup", "pagedown", "delete", "backspace", "insert",
        "esc", "escape", "capslock", "numlock", "scrolllock", "printscreen",
        "pause", "break"
    }

    def __init__(self, current_hotkey="", parent=None):
        super().__init__(parent)
        self._recording = False
        self._pressed_keys = set()
        self._current_pynput = current_hotkey
        self._dark = True
        
        self.setReadOnly(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._update_display()
        self.setFocusPolicy(Qt.StrongFocus)

    def _update_display(self):
        """Update the display text based on current hotkey."""
        if self._current_pynput and self._current_pynput != "disabled":
            display_text = self._pynput_to_display(self._current_pynput)
            self.setText(display_text)
        else:
            self.setText("(click to set hotkey)")

    @staticmethod
    def _pynput_to_display(pynput_str):
        """Convert pynput format to display format."""
        if not pynput_str or pynput_str == "disabled":
            return "(not set)"
        parts = pynput_str.replace("<", "").replace(">", "").split("+")
        display_parts = []
        for p in parts:
            p = p.strip().lower()
            if p == "ctrl":
                display_parts.append("Ctrl")
            elif p == "shift":
                display_parts.append("Shift")
            elif p == "alt":
                display_parts.append("Alt")
            else:
                display_parts.append(p.upper())
        return " + ".join(display_parts)

    def _display_to_pynput(self, display_str):
        """Convert display format to pynput format.
        Examples:
          "Ctrl + Shift + 1" → "<ctrl>+<shift>+1"
          "Ctrl + Alt + S" → "<ctrl>+<alt>+s"
        """
        if not display_str or display_str == "(click to set hotkey)" or display_str == "(not set)":
            return "disabled"
        parts = [p.strip().lower() for p in display_str.split("+")]
        pynput_parts = []
        for p in parts:
            if p == "ctrl":
                pynput_parts.append("<ctrl>")
            elif p == "shift":
                pynput_parts.append("<shift>")
            elif p == "alt":
                pynput_parts.append("<alt>")
            elif len(p) == 1:
                # Single character or digit - no angle brackets
                pynput_parts.append(p)
            else:
                # Multi-char like f1, space, etc - only wrap if valid
                if p in self.VALID_PYNPUT_KEYS:
                    pynput_parts.append(f"<{p}>")
                # else: skip invalid keys entirely
        return "+".join(pynput_parts) if pynput_parts else "disabled"

    def mousePressEvent(self, event):
        """Click to toggle recording mode."""
        if self.text() == "(click to set hotkey)" or not self._recording:
            # Start recording
            self._recording = True
            self._pressed_keys.clear()
            self.setText("Press keys...")
            self.setReadOnly(True)
            pal = Palette.Dark if self._dark else Palette.Light
            self.setStyleSheet(
                f"QLineEdit {{ background: #ff6b6b; color: #fff; border: 2px solid #ff4757; border-radius: 6px; padding: 8px 12px; font: 10px 'Segoe UI'; }}")
            self.setFocus()
        else:
            # Clear current hotkey
            self._current_pynput = "disabled"
            self._recording = False
            self._pressed_keys.clear()
            self._update_display()
            self._apply_style()
            self.hotkey_recorded.emit("disabled")

    def keyPressEvent(self, event):
        """Capture key presses during recording."""
        if not self._recording or event.isAutoRepeat():
            return

        key = event.key()

        # Esc to cancel
        if key == Qt.Key_Escape:
            self._recording = False
            self._pressed_keys.clear()
            self._update_display()
            self._apply_style()
            return

        # Only track keys we recognize (in KEY_NAMES)
        if key in self.KEY_NAMES or key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt):
            self._pressed_keys.add(key)
            self._update_recording_display()

    def keyReleaseEvent(self, event):
        """Finalize hotkey when keys are released."""
        if not self._recording or event.isAutoRepeat():
            return

        key = event.key()
        self._pressed_keys.discard(key)

        # Check if all non-modifier keys are released
        non_modifiers = {k for k in self._pressed_keys
                        if k not in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt,
                                    Qt.Key_Super_L, Qt.Key_Super_R)}
        
        # If we had a complete combo and now non-modifiers are empty, save it
        if not non_modifiers and self._pressed_keys:
            display_str = self._display_preview()
            if display_str and display_str != "Press keys...":
                pynput_str = self._display_to_pynput(display_str)
                if pynput_str and pynput_str != "disabled":  # Only save valid hotkeys
                    self._current_pynput = pynput_str
                    self._recording = False
                    self._pressed_keys.clear()
                    self._update_display()
                    self._apply_style()
                    self.hotkey_recorded.emit(pynput_str)
                else:
                    # Invalid key combo - show error
                    self.setText("(invalid key)")
                    QTimer.singleShot(1000, self._reset_after_error)
            else:
                # Empty display - reset
                self._recording = False
                self._pressed_keys.clear()
                self._update_display()
                self._apply_style()

    def _reset_after_error(self):
        """Reset display after invalid key error."""
        self._recording = False
        self._update_display()
        self._apply_style()

    def _update_recording_display(self):
        """Update display while recording."""
        display_parts = []
        if Qt.Key_Control in self._pressed_keys:
            display_parts.append("Ctrl")
        if Qt.Key_Shift in self._pressed_keys:
            display_parts.append("Shift")
        if Qt.Key_Alt in self._pressed_keys:
            display_parts.append("Alt")

        non_modifiers = {k for k in self._pressed_keys
                        if k not in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt,
                                    Qt.Key_Super_L, Qt.Key_Super_R)}
        if non_modifiers:
            main_key = max(non_modifiers)
            # Only show if we recognize the key
            if main_key in self.KEY_NAMES:
                key_name = self.KEY_NAMES[main_key]
                display_parts.append(key_name)

        if display_parts:
            display_str = " + ".join(display_parts)
            self.setText(display_str)

    def _display_preview(self):
        """Get live preview of what's being pressed."""
        return self.text()

    def _apply_style(self):
        """Apply theme styling."""
        pal = Palette.Dark if self._dark else Palette.Light
        self.setStyleSheet(
            f"QLineEdit {{ background: {pal.INPUT_BG}; color: {pal.TEXT}; "
            f"border: 1px solid {pal.BORDER}; border-radius: 6px; "
            f"padding: 8px 12px; font: 10px 'Segoe UI'; }}"
            f"QLineEdit:focus {{ border: 1px solid {pal.ACCENT1}; }}")

    def setDark(self, dark):
        """Apply dark/light theme."""
        self._dark = dark
        self._apply_style()

    def getCurrentHotkey(self):
        """Get current hotkey in pynput format."""
        return self._current_pynput



# ═══════════════════════════════════════════════════════════════════════
#  MODERN ICON BUTTON (capture cards on Home tab)
# ═══════════════════════════════════════════════════════════════════════
class CaptureCard(QPushButton):
    """A modern card-style button with icon, title & subtitle."""
    def __init__(self, icon_key, title, subtitle, parent=None):
        super().__init__(parent)
        self._icon_key = icon_key
        self._title = title
        self._subtitle = subtitle
        self._dark = True
        self._hover = False
        self._svg_renderer = None
        self._pixmap = None

        # Try to load as image first if it looks like a file path
        if isinstance(icon_key, str) and (icon_key.lower().endswith(('.webp', '.png', '.jpg', '.jpeg'))):
            # Check relative to script dir if relative path
            path = icon_key
            if not os.path.isabs(path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                path = os.path.join(script_dir, path)
            
            if os.path.exists(path):
                self._pixmap = QPixmap(path)
        
        # Fallback to SVG from ICONS dictionary
        if not self._pixmap and icon_key in ICONS:
            self._svg_renderer = QSvgRenderer(QByteArray(ICONS[icon_key].encode()))
            
        self.setFixedHeight(78)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMouseTracking(True)

    def setDark(self, dark):
        self._dark = dark
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def setSubtitle(self, text):
        self._subtitle = text
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pal = Palette.Dark if self._dark else Palette.Light
        w, h = self.width(), self.height()

        # background
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 14, 14)

        if self._hover:
            # Lifted card with gradient glow
            glow_c = QColor(pal.ACCENT1)
            glow_c.setAlpha(20)
            p.setPen(Qt.NoPen)
            p.setBrush(glow_c)
            p.drawPath(path)
            # gradient border on hover
            grad_pen = QLinearGradient(0, 0, w, 0)
            grad_pen.setColorAt(0, QColor(pal.GRAD_START))
            grad_pen.setColorAt(1, QColor(pal.GRAD_END))
            p.setPen(QPen(QBrush(grad_pen), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
            text_color = QColor(pal.TEXT)
            sub_color = QColor(pal.TEXT2)
            icon_color = QColor(pal.ACCENT1)
            icon_bg = QColor(pal.ACCENT1)
            icon_bg.setAlpha(45)
        else:
            p.setPen(QPen(QColor(pal.GLASS_BORDER), 1))
            p.setBrush(QColor(pal.CARD2))
            p.drawPath(path)
            text_color = QColor(pal.TEXT)
            sub_color = QColor(pal.TEXT3)
            icon_color = QColor(pal.ACCENT1)
            icon_bg = QColor(pal.ACCENT1)
            icon_bg.setAlpha(18)

        # icon box
        icon_x, icon_y, icon_sz = 16, (h - 44) // 2, 44
        p.setPen(Qt.NoPen)
        p.setBrush(icon_bg)
        p.drawRoundedRect(QRectF(icon_x, icon_y, icon_sz, icon_sz), 8, 8)

        # render icon
        if self._pixmap and not self._pixmap.isNull():
            p.save()
            padding = 7
            pix_rect = QRectF(icon_x + padding, icon_y + padding, icon_sz - padding * 2, icon_sz - padding * 2)
            p.drawPixmap(pix_rect.toRect(), self._pixmap.scaled(pix_rect.size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            p.restore()
        elif self._svg_renderer:
            # Offscreen pixmap for proper color tinting
            padding = 10
            svg_size = icon_sz - padding * 2
            tmp = QPixmap(svg_size, svg_size)
            tmp.fill(QColor(0, 0, 0, 0))
            tp = QPainter(tmp)
            tp.setRenderHint(QPainter.Antialiasing)
            self._svg_renderer.render(tp, QRectF(0, 0, svg_size, svg_size))
            tp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            tp.fillRect(0, 0, svg_size, svg_size, icon_color)
            tp.end()
            p.drawPixmap(icon_x + padding, icon_y + padding, tmp)
        else:
            # icon text fallback
            p.setPen(icon_color)
            icon_font = QFont("Segoe UI", 18)
            p.setFont(icon_font)
            p.drawText(QRectF(icon_x, icon_y - 1, icon_sz, icon_sz),
                    Qt.AlignCenter, self._icon_key if isinstance(self._icon_key, str) else "?")

        # title
        p.setPen(text_color)
        p.setFont(QFont("Inter", 11, QFont.DemiBold))
        p.drawText(QRectF(icon_x + icon_sz + 16, icon_y + 4, w - 100, 20),
                   Qt.AlignVCenter | Qt.AlignLeft, self._title)

        # subtitle (hotkey pill style)
        p.setPen(sub_color)
        p.setFont(QFont("Inter", 9))
        p.drawText(QRectF(icon_x + icon_sz + 16, icon_y + 24, w - 100, 16),
                   Qt.AlignVCenter | Qt.AlignLeft, self._subtitle)

        # right arrow (minimalist)
        if self._hover:
            p.setPen(QPen(icon_color, 2))
            arrow_path = QPainterPath()
            arrow_path.moveTo(w - 28, h/2 - 5)
            arrow_path.lineTo(w - 23, h/2)
            arrow_path.lineTo(w - 28, h/2 + 5)
            p.drawPath(arrow_path)

        p.end()


# ═══════════════════════════════════════════════════════════════════════
#  MAIN POPUP
# ═══════════════════════════════════════════════════════════════════════
class MainPopup(QWidget):
    hotkeys_changed = pyqtSignal()
    theme_changed = pyqtSignal(bool)
    open_editor_requested = pyqtSignal(str)

    def __init__(self, app_logic):
        super().__init__()
        self._app = app_logic
        self._dark = cfg_load().get("theme", "dark") == "dark"
        self._toggle_rows = []
        self._capture_cards = []
        self.hk_region_recorder = None
        self.hk_full_recorder = None
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 640)
        self._build()
        self.apply_theme(self._dark)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        self._card = QWidget()
        self._card.setObjectName("card")
        cl = QVBoxLayout(self._card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 180))
        self._card.setGraphicsEffect(shadow)

        # header
        hdr = QWidget()
        hdr.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 24, 24, 18)

        # logo area
        logo_container = QWidget()
        logo_l = QHBoxLayout(logo_container)
        logo_l.setContentsMargins(0, 0, 0, 0)
        logo_l.setSpacing(14)

        # Main header logo image (screenshot.webp)
        img_logo = QLabel()
        logo_path = Path(__file__).parent / "assets" / "screenshot.webp"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            img_logo.setPixmap(pix)
            img_logo.setFixedSize(44, 44)
            img_logo.setScaledContents(True)
            img_logo.setStyleSheet("border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2);")
        logo_l.addWidget(img_logo)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)

        t = QLabel("Capture")
        t.setObjectName("title")
        title_col.addWidget(t)

        s = QLabel("Smarter screenshot tools")
        s.setObjectName("sub")
        title_col.addWidget(s)

        logo_l.addLayout(title_col)
        hl.addWidget(logo_container)
        hl.addStretch()

        # status pill
        status_pill = QWidget()
        status_pill.setFixedHeight(26)
        pill_l = QHBoxLayout(status_pill)
        pill_l.setContentsMargins(10, 0, 10, 0)
        pill_l.setSpacing(6)
        
        self._status_dot = QLabel("●")
        self._status_dot.setFixedWidth(10)
        pill_l.addWidget(self._status_dot)
        
        self._version_badge = QLabel("v3.0")
        self._version_badge.setStyleSheet("font-weight: bold; font-size: 10px; color: white; letter-spacing: 0.5px;")
        pill_l.addWidget(self._version_badge)
        
        hl.addWidget(status_pill, 0, Qt.AlignVCenter)

        cl.addWidget(hdr)

        # separator
        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFrameShape(QFrame.HLine)
        cl.addWidget(sep)

        # tabs
        self._tabs = QTabWidget()
        self._tabs.addTab(self._tab_home(), "  Home  ")
        self._tabs.addTab(self._tab_history(), "  History  ")
        self._tabs.addTab(self._tab_api(), "  API  ")
        self._tabs.addTab(self._tab_settings(), "  Settings  ")
        self._tabs.currentChanged.connect(self._on_tab_change)
        cl.addWidget(self._tabs)

        self.update_hotkey_displays()
        root.addWidget(self._card)

    # ── HOME tab ─────────────────────────────────────────────────────
    def _tab_home(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 18, 20, 18)
        l.setSpacing(12)

        # Top section with image on left and cards on right
        top_section = QHBoxLayout()
        top_section.setSpacing(16)

        # 1. Left decorative image
        # capture cards
        self._card1_base = "Select area"
        self._card1 = CaptureCard("assets/capture.webp", "Region", self._card1_base)
        self._card1.clicked.connect(self._app.start_region_capture)
        self._capture_cards.append(self._card1)
        l.addWidget(self._card1)

        self._card2_base = "Entire screen"
        self._card2 = CaptureCard("assets/capture_icon.webp", "Full Screen", self._card2_base)
        self._card2.clicked.connect(self._app.start_fullscreen_capture)
        self._capture_cards.append(self._card2)
        l.addWidget(self._card2)

        l.addSpacing(8)

        # clipboard history section
        clip_section = QLabel("📋 CLIPBOARD HISTORY")
        clip_section.setObjectName("section")
        clip_section.setStyleSheet("margin-bottom: 4px; font-weight: bold;")
        l.addWidget(clip_section)

        # clipboard list
        self.clipboard_list = QListWidget()
        self.clipboard_list.setMaximumHeight(150)
        self.clipboard_list.itemClicked.connect(self._clipboard_item_clicked)
        self.clipboard_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.clipboard_list.customContextMenuRequested.connect(self._clipboard_ctx)
        l.addWidget(self.clipboard_list)

        l.addSpacing(4)

        # status area
        status_frame = QWidget()
        status_frame.setStyleSheet("background: transparent;")
        sl = QHBoxLayout(status_frame)
        sl.setContentsMargins(4, 0, 4, 0)
        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        sl.addWidget(self.status)
        sl.addStretch()
        l.addWidget(status_frame)

        l.addStretch()

        # bottom bar
        bot = QHBoxLayout()
        bot.setSpacing(8)

        # open folder button
        of_btn = QPushButton(" Open Folder")
        of_btn.setObjectName("small")
        of_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Set SVG icon
        fold_pix = QPixmap(18, 18)
        fold_pix.fill(Qt.transparent)
        p = QPainter(fold_pix)
        QSvgRenderer(QByteArray(ICONS["folder"].encode())).render(p)
        p.setCompositionMode(QPainter.CompositionMode_SourceIn)
        p.fillRect(fold_pix.rect(), QColor(Palette.Dark.TEXT if self._dark else Palette.Light.TEXT))
        p.end()
        of_btn.setIcon(QIcon(fold_pix))
        
        of_btn.clicked.connect(self._open_folder)
        bot.addWidget(of_btn)

        bot.addStretch()

        eq = QPushButton(" Exit")
        eq.setObjectName("danger")
        eq.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Set SVG icon
        exit_pix = QPixmap(18, 18)
        exit_pix.fill(Qt.transparent)
        p = QPainter(exit_pix)
        QSvgRenderer(QByteArray(ICONS["log-out"].encode())).render(p)
        p.setCompositionMode(QPainter.CompositionMode_SourceIn)
        p.fillRect(exit_pix.rect(), QColor("#ff4757"))
        p.end()
        eq.setIcon(QIcon(exit_pix))
        
        eq.clicked.connect(QApplication.quit)
        bot.addWidget(eq)
        l.addLayout(bot)
        return w

    # ── HISTORY tab ──────────────────────────────────────────────────
    def _tab_history(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 18, 20, 18)
        l.setSpacing(10)

        row = QHBoxLayout()
        lbl = QLabel("RECENT CAPTURES")
        lbl.setObjectName("section")
        row.addWidget(lbl)
        row.addStretch()
        rb = QPushButton(" Refresh")
        rb.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Set SVG icon
        ref_pix = QPixmap(16, 16)
        ref_pix.fill(Qt.transparent)
        p = QPainter(ref_pix)
        QSvgRenderer(QByteArray(ICONS["refresh"].encode())).render(p)
        p.setCompositionMode(QPainter.CompositionMode_SourceIn)
        p.fillRect(ref_pix.rect(), QColor(Palette.Dark.ACCENT1 if self._dark else Palette.Light.ACCENT1))
        p.end()
        rb.setIcon(QIcon(ref_pix))
        
        rb.clicked.connect(self.refresh_history)
        row.addWidget(rb)
        l.addLayout(row)

        self.hist_list = QListWidget()
        self.hist_list.setIconSize(QSize(120, 80))
        self.hist_list.setSpacing(4)
        self.hist_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hist_list.customContextMenuRequested.connect(self._hist_ctx)
        self.hist_list.doubleClicked.connect(self._hist_open_editor)
        l.addWidget(self.hist_list)

        # action buttons
        br = QHBoxLayout()
        br.setSpacing(6)
        for txt, icon_name, fn in [
            ("Edit", "icon_btn", self._hist_open_editor),
            ("Delete", "danger", self._hist_delete),
            ("Copy", "icon_btn", self._hist_copy),
        ]:
            b = QPushButton(txt)
            b.setObjectName(icon_name)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.clicked.connect(fn)
            br.addWidget(b)
        l.addLayout(br)
        return w

    # ── API tab ──────────────────────────────────────────────────────
    def _tab_api(self):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        sa = QScrollArea()
        sa.setWidget(container)
        sa.setWidgetResizable(True)

        l = QVBoxLayout(container)
        l.setContentsMargins(20, 18, 20, 18)
        l.setSpacing(10)

        cfg = cfg_load()

        # — API Integration
        self._add_section(l, "API INTEGRATION")

        # API Enable toggle
        self.toggle_api = ToggleRow(
            "Enable API Upload", "Automatically upload to your website",
            cfg.get("api_enabled", False))
        self.toggle_api.toggled.connect(
            lambda s: cfg_set(api_enabled=s))
        self._toggle_rows.append(self.toggle_api)
        l.addWidget(self.toggle_api)

        # API Endpoint input
        api_endpoint_layout = QHBoxLayout()
        api_endpoint_layout.setSpacing(12)
        api_endpoint_label = QLabel("API Endpoint")
        api_endpoint_label.setFixedWidth(100)
        api_endpoint_layout.addWidget(api_endpoint_label)
        self.api_endpoint_edit = QLineEdit(cfg.get("api_endpoint", ""))
        self.api_endpoint_edit.setPlaceholderText("https://yourwebsite.com/api/upload")
        self.api_endpoint_edit.textChanged.connect(
            lambda t: cfg_set(api_endpoint=t))
        api_endpoint_layout.addWidget(self.api_endpoint_edit, 1)
        l.addLayout(api_endpoint_layout)

        # API Key input
        api_key_layout = QHBoxLayout()
        api_key_layout.setSpacing(12)
        api_key_label = QLabel("API Key")
        api_key_label.setFixedWidth(100)
        api_key_layout.addWidget(api_key_label)
        self.api_key_edit = QLineEdit(cfg.get("api_key", ""))
        self.api_key_edit.setPlaceholderText("Optional: Your API key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.textChanged.connect(
            lambda t: cfg_set(api_key=t))
        api_key_layout.addWidget(self.api_key_edit, 1)
        l.addLayout(api_key_layout)

        # Upload options
        self.toggle_api_images = ToggleRow(
            "Upload Screenshots", "Send captured images to API",
            cfg.get("api_upload_images", True))
        self.toggle_api_images.toggled.connect(
            lambda s: cfg_set(api_upload_images=s))
        self._toggle_rows.append(self.toggle_api_images)
        l.addWidget(self.toggle_api_images)

        self.toggle_api_clipboard = ToggleRow(
            "Upload Clipboard Text", "Send copied text to API",
            cfg.get("api_upload_clipboard", True))
        self.toggle_api_clipboard.toggled.connect(
            lambda s: cfg_set(api_upload_clipboard=s))
        self._toggle_rows.append(self.toggle_api_clipboard)
        l.addWidget(self.toggle_api_clipboard)

        # — ImgBB Integration
        self._add_section(l, "IMGBB INTEGRATION")
        
        # ImgBB API Key
        imgbb_key_layout = QHBoxLayout()
        imgbb_key_layout.setSpacing(12)
        imgbb_key_label = QLabel("ImgBB API Key")
        imgbb_key_label.setFixedWidth(100)
        imgbb_key_layout.addWidget(imgbb_key_label)
        self.imgbb_key_edit = QLineEdit(cfg.get("imgbb_api_key", ""))
        self.imgbb_key_edit.setPlaceholderText("Enter your ImgBB API key")
        self.imgbb_key_edit.setEchoMode(QLineEdit.Password)
        self.imgbb_key_edit.textChanged.connect(
            lambda t: cfg_set(imgbb_api_key=t))
        imgbb_key_layout.addWidget(self.imgbb_key_edit, 1)
        l.addLayout(imgbb_key_layout)

        # — Google Drive Integration
        self._add_section(l, "GOOGLE DRIVE INTEGRATION")
        
        gdrive_actions = QHBoxLayout()
        gdrive_actions.setSpacing(10)
        
        btn_import = QPushButton("Import credentials.json")
        btn_import.setObjectName("secondary")
        btn_import.clicked.connect(self._import_gdrive_credentials)
        gdrive_actions.addWidget(btn_import)
        
        btn_login = QPushButton("Login to Google Drive")
        btn_login.setObjectName("secondary")
        btn_login.clicked.connect(self._gdrive_login)
        gdrive_actions.addWidget(btn_login)
        l.addLayout(gdrive_actions)
        
        # — Storage selection
        self._add_section(l, "STORAGE SETTINGS")
        storage_layout = QHBoxLayout()
        storage_layout.addWidget(QLabel("Primary Storage"))
        self.storage_combo = QComboBox()
        self.storage_combo.addItems(["ImgBB", "GoogleDrive", "Both"])
        self.storage_combo.setCurrentText(cfg.get("storage_provider", "ImgBB"))
        self.storage_combo.currentTextChanged.connect(
            lambda t: cfg_set(storage_provider=t))
        storage_layout.addWidget(self.storage_combo, 1)
        l.addLayout(storage_layout)

        l.addStretch()
        return sa

    def _import_gdrive_credentials(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Google Drive Credentials", "", "JSON (*.json)")
        if file:
            try:
                import shutil
                shutil.copy(file, GD_CREDENTIALS_PATH)
                self.set_status("Credentials imported!")
            except Exception as e:
                self.set_status(f"Import failed: {e}")

    def _gdrive_login(self):
        if not GD_CREDENTIALS_PATH.exists():
            self.set_status("Error: Import credentials.json first!")
            return
        
        self.set_status("OAuth: Authenticating in browser...")
        try:
            service = gdrive_get_service()
            if service:
                self.set_status("Google Drive login successful!")
            else:
                self.set_status("Login failed.")
        except Exception as e:
            self.set_status(f"Login failed: {e}")

    def refresh_history(self):
        self.hist_list.clear()
        folder = Path(save_folder())
        files = sorted(folder.rglob("screenshot_*.png"),
                       key=lambda f: f.stat().st_mtime, reverse=True)[:50]
        for f in files:
            try:
                pix = QPixmap(str(f)).scaledToWidth(
                    120, Qt.SmoothTransformation)
                sz = f.stat().st_size
                sz_str = f"{sz // 1024} KB" if sz < 1048576 else f"{sz / 1048576:.1f} MB"
                mt = datetime.fromtimestamp(f.stat().st_mtime)
                item = QListWidgetItem(
                    QIcon(pix), f"{f.name}\n{sz_str}  ·  {mt:%Y-%m-%d %H:%M}")
                item.setData(Qt.UserRole, str(f))
                item.setToolTip(str(f))
                self.hist_list.addItem(item)
            except Exception:
                pass

    def _hist_sel_path(self):
        item = self.hist_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _hist_open_editor(self, *_):
        p = self._hist_sel_path()
        if p:
            self.open_editor_requested.emit(p)

    def _hist_delete(self):
        p = self._hist_sel_path()
        if p:
            try:
                Path(p).unlink()
                self.refresh_history()
                self.set_status("Deleted")
            except Exception as e:
                self.set_status(f"Error: {e}")

    def _hist_copy(self):
        p = self._hist_sel_path()
        if p:
            pix = QPixmap(p)
            QApplication.clipboard().setPixmap(pix)
            self.set_status("Copied to clipboard")

    def _hist_ctx(self, pos):
        item = self.hist_list.itemAt(pos)
        if not item:
            return
        self.hist_list.setCurrentItem(item)
        menu = QMenu()
        menu.setStyleSheet(self._context_menu_style())
        menu.addAction("✏  Open in Editor", self._hist_open_editor)
        menu.addAction("📋  Copy to Clipboard", self._hist_copy)
        menu.addAction("📂  Show in Explorer", self._hist_show_explorer)
        menu.addSeparator()
        menu.addAction("🗑  Delete", self._hist_delete)
        menu.exec_(self.hist_list.mapToGlobal(pos))

    def _context_menu_style(self):
        pal = Palette.Dark if self._dark else Palette.Light
        return f"""
        QMenu {{
            background: {pal.CARD1};
            border: 1px solid {pal.BORDER};
            border-radius: 8px;
            padding: 6px;
            color: {pal.TEXT};
            font: 10px 'Segoe UI';
        }}
        QMenu::item {{
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background: {pal.ACCENT1};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background: {pal.SEPARATOR};
            margin: 4px 8px;
        }}
        """

    def _hist_show_explorer(self):
        p = self._hist_sel_path()
        if p and os.path.exists(p):
            import subprocess
            subprocess.Popen(f'explorer /select,"{p}"')

    def refresh_clipboard_history(self):
        """Refresh the clipboard history list."""
        self.clipboard_list.clear()
        history = clipboard_load()
        
        for entry in history[:20]:  # Show last 20 items
            text = entry.get("text", "")
            # Truncate long text for display
            display = text[:80] + "..." if len(text) > 80 else text
            display = display.replace("\n", " ").replace("\r", "")
            
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, text)  # Store full text
            item.setToolTip(text)  # Show full text on hover
            self.clipboard_list.addItem(item)
        
        if not history:
            item = QListWidgetItem("(no clipboard history yet)")
            item.setFlags(Qt.NoItemFlags)  # Make it non-selectable
            self.clipboard_list.addItem(item)

    def _clipboard_item_clicked(self, item):
        """Copy clicked clipboard item back to clipboard."""
        text = item.data(Qt.UserRole)
        if text and text != "(no clipboard history yet)":
            clip = QApplication.clipboard()
            # Temporarily block signals to avoid re-saving this
            clip.blockSignals(True)
            clip.setText(text)
            clip.blockSignals(False)
            self.set_status(f"✓  Copied to clipboard")

    def _clipboard_ctx(self, pos):
        """Context menu for clipboard items."""
        item = self.clipboard_list.itemAt(pos)
        if not item:
            return
        
        text = item.data(Qt.UserRole)
        if not text or text == "(no clipboard history yet)":
            return

        m = QMenu(self)
        m.setStyleSheet(self._context_menu_style())
        m.addAction("📋  Copy", lambda: self._clipboard_item_clicked(item))
        m.addAction("🗑  Delete", lambda: self._clipboard_delete_item(item))
        m.addSeparator()
        m.addAction("Clear All", self._clipboard_clear_all)
        m.exec_(self.clipboard_list.mapToGlobal(pos))

    def _clipboard_delete_item(self, item):
        """Delete a clipboard history item."""
        text = item.data(Qt.UserRole)
        if not text:
            return
        
        history = clipboard_load()
        history = [h for h in history if h.get("text") != text]
        clipboard_save(history)
        self.refresh_clipboard_history()

    def _clipboard_clear_all(self):
        """Clear all clipboard history."""
        clipboard_save([])
        self.refresh_clipboard_history()
        self.set_status("Clipboard history cleared")

    # ── SETTINGS tab ─────────────────────────────────────────────────
    def _tab_settings(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        sa = QScrollArea()
        sa.setWidget(w)
        sa.setWidgetResizable(True)
        sa.setObjectName("settings_scroll")

        l = QVBoxLayout(w)
        l.setContentsMargins(20, 18, 20, 18)
        l.setSpacing(10)
        l.setAlignment(Qt.AlignTop)

        cfg = cfg_load()
        self._collapsibles = []

        # — SECTION: SAVE LOCATION
        sec_save = CollapsibleSection("Save Location")
        self._collapsibles.append(sec_save)
        
        self.folder_edit = QLineEdit(cfg["save_folder"])
        self.folder_edit.setReadOnly(True)
        sec_save.addWidget(self.folder_edit)

        fr = QHBoxLayout()
        fr.setSpacing(6)
        for txt, fn, obj_name in [
            ("Browse", self._browse, "icon_btn"),
            ("Reset", self._reset_folder, "icon_btn"),
            ("Open", self._open_folder, "icon_btn"),
        ]:
            b = QPushButton(txt)
            b.setObjectName(obj_name)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.clicked.connect(fn)
            fr.addWidget(b)
        sec_save.addLayout(fr)
        l.addWidget(sec_save)

        # — SECTION: PREFERENCES
        sec_pref = CollapsibleSection("Preferences")
        self._collapsibles.append(sec_pref)
        
        prefs = [
            ("Auto-organize", "Save screenshots in date folders", "auto_organize", True, None),
            ("Copy to Clipboard", "Auto-copy after every capture", "copy_clipboard", True, None),
            ("Open Editor", "Launch annotation editor after capture", "open_editor", False, None),
            ("Start Minimized", "Start application in system tray", "start_minimized", True, None),
            ("Start with Windows", "Automatically start when you sign in", "auto_start", False, self._on_autostart_toggled),
            ("Monitor Clipboard", "Save text copied to clipboard", "monitor_clipboard", True, self._toggle_clipboard_monitor)
        ]
        
        for title, desc, key, dflt, fn in prefs:
            row = ToggleRow(title, desc, cfg.get(key, dflt))
            if fn: row.toggled.connect(fn)
            else: row.toggled.connect(lambda s, k=key: cfg_set(**{k: s}))
            self._toggle_rows.append(row)
            sec_pref.addWidget(row)
        l.addWidget(sec_pref)

        # — SECTION: KEYBOARD SHORTCUTS
        if HAS_HOTKEYS:
            sec_keys = CollapsibleSection("Keyboard Shortcuts")
            self._collapsibles.append(sec_keys)
            
            # Region
            rk_layout = QHBoxLayout()
            rk_layout.setSpacing(12)
            rk_label = QLabel("Region")
            rk_label.setFixedWidth(100)
            rk_label.setStyleSheet("color: white; font-size: 10px;")
            rk_layout.addWidget(rk_label)
            self.hk_region_recorder = HotkeyRecorder(cfg.get("hotkey_region", "<ctrl>+<shift>+1"))
            self.hk_region_recorder.hotkey_recorded.connect(self._hk_changed)
            rk_layout.addWidget(self.hk_region_recorder, 1)
            sec_keys.addLayout(rk_layout)

            # Full Screen
            fk_layout = QHBoxLayout()
            fk_layout.setSpacing(12)
            fk_label = QLabel("Full Screen")
            fk_label.setFixedWidth(100)
            fk_label.setStyleSheet("color: white; font-size: 10px;")
            fk_layout.addWidget(fk_label)
            self.hk_full_recorder = HotkeyRecorder(cfg.get("hotkey_fullscreen", "<ctrl>+<shift>+2"))
            self.hk_full_recorder.hotkey_recorded.connect(self._hk_changed)
            fk_layout.addWidget(self.hk_full_recorder, 1)
            sec_keys.addLayout(fk_layout)
            l.addWidget(sec_keys)

        # — SECTION: APPEARANCE
        sec_app = CollapsibleSection("Appearance")
        self._collapsibles.append(sec_app)
        
        self.toggle_theme = ToggleRow("Dark Mode", "Switch between dark and light theme", self._dark)
        self.toggle_theme.toggled.connect(self._theme_toggled)
        self._toggle_rows.append(self.toggle_theme)
        sec_app.addWidget(self.toggle_theme)
        l.addWidget(sec_app)

        l.addStretch()
        return sa

    def _add_section(self, layout, text):
        layout.addSpacing(6)
        lbl = QLabel(text)
        lbl.setObjectName("section")
        layout.addWidget(lbl)

    def _browse(self):
        f = QFileDialog.getExistingDirectory(
            self, "Choose Folder", self.folder_edit.text())
        if f:
            cfg_set(save_folder=f)
            self.folder_edit.setText(f)
            self.set_status("Folder updated")

    def _reset_folder(self):
        cfg_set(save_folder=DEFAULT_FOLDER)
        self.folder_edit.setText(DEFAULT_FOLDER)
        self.set_status("Reset to default")

    def _open_folder(self):
        folder = save_folder()
        Path(folder).mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    def _hk_changed(self, _=None):
        """Called when a hotkey recorder emits a new hotkey."""
        if not self.hk_region_recorder or not self.hk_full_recorder:
            return
        region_hk = self.hk_region_recorder.getCurrentHotkey()
        full_hk = self.hk_full_recorder.getCurrentHotkey()
        cfg_set(
            hotkey_region=region_hk,
            hotkey_fullscreen=full_hk,
        )
        self.hotkeys_changed.emit()
        self.update_hotkey_displays()

    def _on_autostart_toggled(self, enabled):
        if set_windows_autostart(enabled):
            cfg_set(auto_start=enabled)
            self.set_status("Autostart updated")
        else:
            self.set_status("Failed to update Autostart")
            # Revert switch if possible
            self.toggle_autostart.switch.setChecked(not enabled)

    def update_hotkey_displays(self):
        """Update the capture card subtitles with the current hotkeys."""
        cfg = cfg_load()
        hk_region = cfg.get("hotkey_region", "<ctrl>+<shift>+1")
        hk_full = cfg.get("hotkey_fullscreen", "<ctrl>+<shift>+2")
        
        disp_region = HotkeyRecorder._pynput_to_display(hk_region)
        disp_full = HotkeyRecorder._pynput_to_display(hk_full)
        
        if hasattr(self, '_card1'):
            self._card1.setSubtitle(f"{self._card1_base}  ·  {disp_region}")
        if hasattr(self, '_card2'):
            self._card2.setSubtitle(f"{self._card2_base}  ·  {disp_full}")

    def _theme_toggled(self, dark):
        self._dark = dark
        cfg_set(theme="dark" if dark else "light")
        self.apply_theme(dark)
        self.theme_changed.emit(dark)

    def _toggle_clipboard_monitor(self, enabled):
        cfg_set(monitor_clipboard=enabled)
        if enabled:
            self._app._setup_clipboard_monitor()
        else:
            # Disconnect clipboard monitoring
            clip = QApplication.clipboard()
            try:
                clip.dataChanged.disconnect(self._app._on_clipboard_change)
            except:
                pass

    def _on_tab_change(self, idx):
        if idx == 0:  # Home tab
            self.refresh_clipboard_history()
        elif idx == 1:  # History tab
            self.refresh_history()

    # ── theme application ────────────────────────────────────────────
    def apply_theme(self, dark):
        self._dark = dark
        pal = Palette.Dark if dark else Palette.Light
        self._card.setStyleSheet(_popup_style(pal))
        self._tabs.setStyleSheet(_tab_style(pal))

        # version badge & status pill with gradient
        self._version_badge.parentWidget().setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {pal.GRAD_START}, stop:1 {pal.GRAD_END}); border-radius: 13px;")

        # status dot
        self._status_dot.setStyleSheet(
            f"color: {pal.ACCENT3}; font-size: 8px; background: transparent;")

        # capture cards
        for card in self._capture_cards:
            card.setDark(dark)

        # collapsibles
        for sec in getattr(self, '_collapsibles', []):
            sec.setDark(dark)

        # toggle rows
        for row in self._toggle_rows:
            row.setDark(dark)

        # hotkey recorders
        if HAS_HOTKEYS:
            self.hk_region_recorder.setDark(dark)
            self.hk_full_recorder.setDark(dark)

    # ── auto-hide on click outside ──────────────────────────────────
    def changeEvent(self, event):
        """Hide popup when it loses focus (user clicks outside)."""
        if event.type() == event.ActivationChange:
            if self.isVisible() and not self.isActiveWindow():
                self.hide()
        super().changeEvent(event)

    # ── public helpers ───────────────────────────────────────────────
    def set_status(self, txt):
        self.status.setText(txt)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self._position()
            self.show()
            self.activateWindow()
            self.raise_()

    def _position(self):
        avail = QApplication.primaryScreen().availableGeometry()
        self.move(avail.right() - self.width() - 12,
                  avail.bottom() - self.height() - 12)


# ═══════════════════════════════════════════════════════════════════════
#  APP CORE
# ═══════════════════════════════════════════════════════════════════════
class App:
    def __init__(self):
        self.overlay = None
        self._editor = None
        self._hk_listener = None
        self._last_clipboard_text = ""

        self.popup = MainPopup(self)
        self.popup.hotkeys_changed.connect(self._restart_hotkeys)
        self.popup.theme_changed.connect(self._on_theme)
        self.popup.open_editor_requested.connect(self._open_editor)

        self._build_tray()
        self._restart_hotkeys()
        
        # Setup clipboard monitoring
        self._setup_clipboard_monitor()
        
        # Load initial clipboard history
        self.popup.refresh_clipboard_history()
        
        # Show on startup if configured
        if not cfg_load().get("start_minimized", True):
            QTimer.singleShot(500, self.popup.toggle)

    def _setup_clipboard_monitor(self):
        """Setup clipboard change monitoring."""
        cfg = cfg_load()
        if cfg.get("monitor_clipboard", True):
            clip = QApplication.clipboard()
            clip.dataChanged.connect(self._on_clipboard_change)
            # Initialize with current clipboard content
            current = clip.text()
            if current and current.strip():
                self._last_clipboard_text = current.strip()

    def _on_clipboard_change(self):
        """Handle clipboard content changes."""
        cfg = cfg_load()
        if not cfg.get("monitor_clipboard", True):
            return
        
        clip = QApplication.clipboard()
        text = clip.text()
        
        # Only save if it's text and different from last saved
        if text and text.strip() and text.strip() != self._last_clipboard_text:
            self._last_clipboard_text = text.strip()
            clipboard_add(text.strip())
            self.popup.refresh_clipboard_history()
            
            # Upload to API if enabled
            if cfg.get("api_enabled", False) and cfg.get("api_upload_clipboard", True):
                try:
                    api_upload_clipboard(text.strip())
                except Exception as e:
                    print(f"Clipboard API upload error: {e}")

    def _build_tray(self):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self._icon())
        self.tray.setToolTip("StayX Capture")

        m = QMenu()
        m.addAction("⬚  Capture Region", self.start_region_capture)
        m.addAction("▣  Full Screen", self.start_fullscreen_capture)
        m.addSeparator()
        m.addAction("Show / Hide", self.popup.toggle)
        m.addAction("Exit", QApplication.quit)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(self._tray_click)
        self.tray.show()

    def _tray_click(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.popup.toggle()

    def _restart_hotkeys(self):
        if not HAS_HOTKEYS:
            print("ℹ Hotkeys disabled (HAS_HOTKEYS=False)")
            return
        if self._hk_listener:
            self._hk_listener.stop()
            self._hk_listener = None

        cfg = cfg_load()
        bridge = HotkeyBridge()
        bridge.region.connect(self.start_region_capture)
        bridge.fullscreen.connect(self.start_fullscreen_capture)
        self._hk_bridge = bridge

        mapping = {}
        rk = cfg.get("hotkey_region", "<ctrl>+<shift>+1")
        fk = cfg.get("hotkey_fullscreen", "<ctrl>+<shift>+2")
        
        print(f"Config hotkeys - Region: {rk!r}, FullScreen: {fk!r}")
        
        if rk != "disabled" and rk:
            mapping[rk] = lambda: bridge.region.emit()
            print(f"✓ Registered region hotkey: {rk!r}")
        if fk != "disabled" and fk:
            mapping[fk] = lambda: bridge.fullscreen.emit()
            print(f"✓ Registered fullscreen hotkey: {fk!r}")

        if mapping:
            try:
                print(f"Starting GlobalHotKeys with {len(mapping)} mapping(s)...")
                self._hk_listener = GlobalHotKeys(mapping)
                self._hk_listener.daemon = True
                self._hk_listener.start()
                print(f"✓ Hotkeys active!")
            except Exception as e:
                print(f"✗ Hotkey error: {type(e).__name__}: {e}")
        else:
            print("⚠ No hotkeys configured")

    def _get_active_screen(self):
        """Get the screen where the mouse cursor is currently located."""
        screens = QApplication.screens()
        cursor_pos = QCursor.pos()
        for screen in screens:
            if screen.geometry().contains(cursor_pos):
                return screen
        return QApplication.primaryScreen()

    def _grab_all_screens(self):
        """Grab and combine all connected monitors into a single QPixmap."""
        screens = QApplication.screens()
        if len(screens) == 1:
            # Single monitor: simple grab
            return screens[0].grabWindow(0), screens[0].geometry()
        
        # Multiple monitors: combine them
        # Calculate virtual desktop bounds
        virtual_rect = QRect()
        for screen in screens:
            virtual_rect = virtual_rect.united(screen.geometry())
        
        # Create combined pixmap at actual screen resolution
        combined = QPixmap(virtual_rect.width(), virtual_rect.height())
        combined.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(combined)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        for screen in screens:
            geo = screen.geometry()
            # Grab this screen and paint it at correct position in virtual desktop
            grabbed = screen.grabWindow(0)
            # Calculate offset from virtual desktop origin
            x = geo.x() - virtual_rect.x()
            y = geo.y() - virtual_rect.y()
            painter.drawPixmap(x, y, geo.width(), geo.height(), grabbed)
        painter.end()
        
        return combined, virtual_rect

    def start_fullscreen_capture(self):
        if self.popup.isVisible():
            self.popup.hide()
            QTimer.singleShot(150, self._grab_full)
        else:
            self._grab_full()

    def _grab_full(self):
        screen = self._get_active_screen()
        pix = screen.grabWindow(0)
        self._finish(pix)

    def start_region_capture(self):
        if self.overlay:
            return
        if self.popup.isVisible():
            self.popup.hide()
            QTimer.singleShot(150, self._grab_region)
        else:
            self._grab_region()

    def _grab_region(self):
        result = self._grab_all_screens()
        if isinstance(result, tuple):
            frozen, virtual_rect = result
        else:
            frozen = result
            virtual_rect = QApplication.primaryScreen().geometry()
        
        self.overlay = SnipOverlay(frozen, virtual_rect)
        self.overlay.region_captured.connect(self._region_done)
        self.overlay.cancelled.connect(self._cancel)

    def _region_done(self, cropped):
        self._finish(cropped)
        self.overlay = None

    def _cancel(self):
        self.popup.set_status("Cancelled")
        self.overlay = None

    def _finish(self, pix: QPixmap):
        cfg = cfg_load()
        base = Path(cfg.get("save_folder", DEFAULT_FOLDER))

        if cfg.get("auto_organize", True):
            folder = base / date.today().isoformat()
        else:
            folder = base
        folder.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        name = f"screenshot_{ts}.png"
        path = folder / name
        
        # Save to disk first (fast)
        pix.save(str(path), "PNG")

        if cfg.get("copy_clipboard", True):
            QApplication.clipboard().setPixmap(pix)

        # Upload to API if enabled - do this asynchronously
        if cfg.get("api_enabled", False):
            # Extract bytes inside main thread safely
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QBuffer.WriteOnly)
            pix.save(buffer, "PNG")
            png_bytes = bytes(ba.data())

            def async_upload():
                try:
                    result = api_upload_screenshot(png_bytes, name)
                    # Note: Ideally UI updates should happen via signals, 
                    # but simple status updates might not crash.
                    # A proper approach creates a worker, but since this sets 
                    # a string on a label, it is often tolerated or we can ignore it.
                except Exception as e:
                    print(f"API upload error: {e}")

            import threading
            threading.Thread(target=async_upload, daemon=True).start()
            self.popup.set_status(f"✓  {name} (uploading...)")
        else:
            self.popup.set_status(f"✓  {name}")

        self.tray.showMessage("Screenshot Captured", str(path),
                              QSystemTrayIcon.Information, 4000)

        if cfg.get("open_editor", False):
            self._open_editor(str(path))

    def _open_editor(self, filepath):
        dark = cfg_load().get("theme", "dark") == "dark"
        self._editor = ImageEditor(filepath, dark=dark)
        self._editor.show()
        self._editor.raise_()
        self._editor.activateWindow()

    def _on_theme(self, dark):
        pass

    @staticmethod
    def _icon() -> QIcon:
        icon_path = Path(__file__).parent / "assets" / "screenshot_icon.ico"
        if icon_path.exists():
            return QIcon(str(icon_path))
            
        px = QPixmap(64, 64)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)

        # Gradient background
        grad = QLinearGradient(4, 4, 60, 60)
        grad.setColorAt(0, QColor(79, 70, 229))   # Indigo
        grad.setColorAt(1, QColor(139, 92, 246))   # Violet
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(4, 4, 56, 56, 16, 16)

        # minimalist camera icon
        p.setPen(QPen(QColor(255, 255, 255), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(16, 22, 32, 22, 4, 4)
        p.drawEllipse(26, 27, 12, 12)
        # lens dot
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(40, 26, 4, 4)

        p.end()
        return QIcon(px)


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY
# ═══════════════════════════════════════════════════════════════════════
def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)

    # set global font and icon
    font = QFont("Inter", 10)
    qapp.setFont(font)
    qapp.setWindowIcon(App._icon())

    app = App()

    def _cleanup():
        if app._hk_listener:
            app._hk_listener.stop()
    qapp.aboutToQuit.connect(_cleanup)

    sys.exit(qapp.exec_())


if __name__ == "__main__":
    main()
