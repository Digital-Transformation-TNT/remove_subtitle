"""
notifier.py — Thông báo hệ thống (toast) hiện NGOÀI cửa sổ tool.

Mục tiêu: người dùng bấm Bắt đầu rồi THU NHỎ tool đi làm việc khác, khi xong 1 video
(hoặc xong hết / gặp lỗi) vẫn thấy thông báo nổi ở góc màn hình + nháy taskbar/dock.

Cách hiện thông báo theo hệ điều hành (tự chọn cái nào chạy được, có fallback):

  Windows : icon khay hệ thống (QSystemTrayIcon.showMessage) -> toast Windows 10/11,
            vào cả Action Center. Hiện kể cả khi cửa sổ đang thu nhỏ.
  macOS   : `osascript -e 'display notification ...'` -> Notification Center.
            KHÔNG dùng QSystemTrayIcon.showMessage trên mac vì Qt gọi API
            NSUserNotification đã bị Apple khai tử -> nhiều máy im lặng không hiện gì.
            (Vẫn thử tray như phương án 2 nếu osascript lỗi.)
  Linux   : `notify-send`, sau đó mới tới tray.

Nếu TẤT CẢ đều không chạy được -> notify() trả về False để phía gọi tự bung popup.
"""

import os
import shutil
import subprocess
import sys

IS_MAC = sys.platform == "darwin"
IS_WIN = os.name == "nt"

# Gọi thẳng đường dẫn tuyệt đối: bản .app đóng gói có thể có PATH khác thường.
_OSASCRIPT = "/usr/bin/osascript" if os.path.exists("/usr/bin/osascript") else "osascript"


def _clean_env():
    """Env sạch để gọi lệnh HỆ THỐNG (osascript/notify-send) từ bản đóng gói.

    PyInstaller nhét DYLD_LIBRARY_PATH / LD_LIBRARY_PATH trỏ vào thư viện của app;
    lệnh hệ thống nạp nhầm thư viện này sẽ chết -> thông báo im lặng. Khôi phục lại
    biến gốc (*_ORIG) hoặc bỏ hẳn.
    """
    env = os.environ.copy()
    for var in ("DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH", "LD_LIBRARY_PATH",
                "DYLD_INSERT_LIBRARIES"):
        orig = env.pop(var + "_ORIG", None)
        if orig:
            env[var] = orig
        else:
            env.pop(var, None)
    return env


def _osa_str(text):
    """Bọc chuỗi cho AppleScript (escape \\ và ", bỏ xuống dòng vì AppleScript không nhận)."""
    s = str(text).replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\r", " ").replace("\n", " · ")
    return '"' + s + '"'


class Notifier:
    """Gửi thông báo hệ thống; giữ luôn icon khay để khôi phục cửa sổ khi bấm vào."""

    def __init__(self, app_name="TNT Video Tool", icon=None, parent=None,
                 on_activated=None, log=None):
        self.app_name = app_name
        self._log = log or (lambda m: None)
        self._tray = None
        self._mac_ok = None          # None = chưa thử osascript lần nào
        self._linux_cmd = shutil.which("notify-send") if not (IS_WIN or IS_MAC) else None
        self._mac_cmd = shutil.which("terminal-notifier") if IS_MAC else None

        # Icon khay: dùng cho Windows/Linux. Trên macOS KHÔNG tạo tray để menu bar
        # khỏi mọc thêm icon thừa (mac đã có Notification Center qua osascript).
        if not IS_MAC:
            self._tray = self._make_tray(icon, parent, on_activated)

    # ------------------------------------------------------------------ tray
    def _make_tray(self, icon, parent, on_activated):
        try:
            from PySide6.QtWidgets import QApplication, QSystemTrayIcon
            if QApplication.instance() is None:   # chưa có app Qt -> tạo tray sẽ crash
                return None
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return None
            ic = icon if (icon is not None and not icon.isNull()) else _fallback_icon()
            tray = QSystemTrayIcon(ic, parent)
            tray.setToolTip(self.app_name)
            if on_activated is not None:
                tray.activated.connect(lambda _r: on_activated())
            tray.show()
            return tray
        except Exception:
            return None

    # --------------------------------------------------------------- gửi báo
    def notify(self, title, body, detail="", sound=True):
        """Hiện 1 thông báo hệ thống. Trả về True nếu đã đẩy được ra ngoài tool."""
        if IS_MAC and self._mac_notify(title, body, detail, sound):
            return True
        if self._linux_cmd and self._linux_notify(title, body, detail):
            return True
        if self._tray_notify(title, body, detail):
            return True
        # macOS: osascript hỏng -> thử nốt tray của Qt (có máy vẫn hiện).
        if IS_MAC and self._tray is None:
            try:
                from PySide6.QtWidgets import QSystemTrayIcon
                if QSystemTrayIcon.isSystemTrayAvailable():
                    self._tray = self._make_tray(None, None, None)
                    return self._tray_notify(title, body, detail)
            except Exception:
                pass
        return False

    def _tray_notify(self, title, body, detail):
        if self._tray is None:
            return False
        try:
            from PySide6.QtWidgets import QSystemTrayIcon
            text = body if not detail else f"{body}\n{detail}"
            self._tray.showMessage(title, text, QSystemTrayIcon.Information, 8000)
            return True
        except Exception:
            return False

    def _mac_notify(self, title, body, detail, sound):
        # terminal-notifier (nếu máy có) đẹp hơn: bấm vào mở được, không mượn tên app khác.
        if self._mac_cmd:
            try:
                cmd = [self._mac_cmd, "-title", str(title), "-message", str(body)]
                if detail:
                    cmd += ["-subtitle", str(detail)]
                if sound:
                    cmd += ["-sound", "Glass"]
                subprocess.run(cmd, timeout=8, capture_output=True, env=_clean_env())
                return True
            except Exception:
                pass
        if self._mac_ok is False:      # đã thử và hỏng -> khỏi thử lại cho nhanh
            return False
        script = "display notification %s with title %s" % (
            _osa_str(body), _osa_str(title))
        if detail:
            script += " subtitle %s" % _osa_str(detail)
        if sound:
            script += ' sound name "Glass"'
        try:
            r = subprocess.run([_OSASCRIPT, "-e", script], timeout=8,
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               env=_clean_env())
            ok = (r.returncode == 0)
            self._mac_ok = ok
            if not ok:
                self._log("Không gửi được thông báo macOS: " + (r.stderr or "").strip())
            return ok
        except Exception as e:
            self._mac_ok = False
            self._log(f"Không gửi được thông báo macOS: {e}")
            return False

    def _linux_notify(self, title, body, detail):
        try:
            text = body if not detail else f"{body}\n{detail}"
            subprocess.run([self._linux_cmd, "-a", self.app_name, str(title), text],
                           timeout=8, capture_output=True, env=_clean_env())
            return True
        except Exception:
            return False

    # -------------------------------------------------------------- dọn dẹp
    def shutdown(self):
        if self._tray is not None:
            try:
                self._tray.hide()
            except Exception:
                pass


def _fallback_icon():
    """Icon dự phòng khi không có logo.png — tray icon RỖNG thì Windows không hiện toast."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#FF791C"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 60, 60)
    p.setPen(QColor("#FFFFFF"))
    f = QFont()
    f.setBold(True)
    f.setPointSize(24)
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignCenter, "T")
    p.end()
    return QIcon(pix)
