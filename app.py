"""
app.py — Tool PySide6 (TNT GROUP): tách video -> xoá phụ đề qua vmake.ai -> ghép lại.

Chạy:  python app.py

Cấu trúc thư mục đầu ra (output):
  output/
    segments/<ten_video>/<ten_video>_000.mp4   (các đoạn đã cắt)
    processed/<ten_video>/<ten_video>_000.mp4  (đoạn đã xoá phụ đề từ vmake)
    final/<ten_video>_nosub.mp4                 (video hoàn chỉnh)
    manifest.json

Cấu hình được lưu tại:  ~/.tnt_video_tool/config.json
"""

import json
import os
import sys
import threading

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QRadioButton, QButtonGroup,
    QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox, QGroupBox, QPlainTextEdit,
    QProgressBar, QMessageBox, QFrame, QTabWidget,
)

from tnt_license import check_license
from notifier import Notifier
import video_utils as vu
import vmake_client

# --- Bộ màu thương hiệu TNT GROUP ---
MAROON = "#3B0000"
MAROON_DEEP = "#2A0000"
MAROON_SOFT = "#5A1414"
ORANGE = "#FF791C"
ORANGE_HOVER = "#FF8C3D"
ORANGE_DARK = "#E0660F"
CREAM = "#FBF6F2"

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Session/cấu hình lưu theo TỪNG MÁY tại %USERPROFILE%\.tnt_video_tool\ — KHÔNG nằm
# trong exe. Vì vậy exe phát hành không chứa session của người build; mỗi người dùng
# tự đăng nhập và lưu session riêng của họ trên máy họ.
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".tnt_video_tool")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
SESSION_PATH = os.path.join(CONFIG_DIR, "vmake_session.json")

STYLESHEET = f"""
QWidget#central {{ background: {CREAM}; }}
QLabel {{ color: {MAROON}; }}

QFrame#header {{
    background: #FFFFFF;
    border: 1px solid #ECD9D1;
    border-radius: 14px;
}}
QLabel#title {{ color: {MAROON}; font-size: 19px; font-weight: 800; }}
QLabel#subtitle {{ color: {ORANGE_DARK}; font-size: 12px; font-weight: 600; }}

QGroupBox {{
    font-weight: 700; color: {MAROON};
    border: 1px solid #E8D5CD; border-radius: 12px;
    margin-top: 16px; padding: 12px 10px 10px 10px; background: #FFFFFF;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 14px; padding: 2px 8px; background: {MAROON};
    color: #FFFFFF; border-radius: 6px;
}}

/* Tab: macOS mặc định render chữ trắng trên nền trắng -> mất tên tab. Ép style
   theo tone thương hiệu: tab thường nền kem chữ maroon, tab chọn nền cam chữ trắng. */
QTabWidget::pane {{
    border: 1px solid #E8D5CD; border-radius: 12px;
    background: #FFFFFF; top: -1px;
}}
QTabWidget::tab-bar {{ left: 8px; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{
    background: #F2E6DF; color: {MAROON};
    border: 1px solid #E8D5CD;
    border-top-left-radius: 9px; border-top-right-radius: 9px;
    padding: 8px 18px; margin-right: 4px; font-weight: 700;
}}
QTabBar::tab:selected {{
    background: {ORANGE}; color: #FFFFFF; border-color: {ORANGE};
}}
QTabBar::tab:hover:!selected {{ color: {ORANGE_DARK}; border-color: {ORANGE}; }}

QLineEdit, QDoubleSpinBox, QComboBox {{
    border: 1px solid #D8C2B9; border-radius: 7px; padding: 6px 9px;
    background: #FFFFFF; color: {MAROON_DEEP};
    selection-background-color: {ORANGE}; selection-color: #FFFFFF;
}}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border: 1px solid {ORANGE}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: #FFFFFF; color: {MAROON_DEEP};
    selection-background-color: {ORANGE}; selection-color: #FFFFFF;
    border: 1px solid #D8C2B9;
}}

QCheckBox, QRadioButton {{ color: {MAROON}; spacing: 7px; }}
QCheckBox::indicator {{
    width: 17px; height: 17px; border: 1px solid #C9A99E;
    border-radius: 5px; background: #FFFFFF;
}}
QCheckBox::indicator:checked {{ background: {ORANGE}; border-color: {ORANGE}; }}
QRadioButton::indicator {{
    width: 17px; height: 17px; border: 1px solid #C9A99E;
    border-radius: 9px; background: #FFFFFF;
}}
QRadioButton::indicator:checked {{ background: {ORANGE}; border-color: {ORANGE}; }}

QPushButton {{
    background: #FFFFFF; color: {MAROON}; border: 1px solid #CBA89C;
    border-radius: 8px; padding: 7px 14px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {ORANGE}; color: {ORANGE_DARK}; }}

QPushButton#primary {{
    background: {ORANGE}; color: #FFFFFF; border: none;
    border-radius: 8px; padding: 9px 22px; font-weight: 800;
}}
QPushButton#primary:hover {{ background: {ORANGE_HOVER}; }}
QPushButton#primary:disabled {{ background: #E9C6B2; color: #FFF7F2; }}

QPushButton#danger {{
    background: #FFFFFF; color: {MAROON}; border: 1px solid {MAROON};
    border-radius: 8px; padding: 9px 22px; font-weight: 700;
}}
QPushButton#danger:hover {{ background: {MAROON}; color: #FFFFFF; }}
QPushButton#danger:disabled {{ color: #B9A39D; border-color: #D9C7C1; }}

QProgressBar {{
    border: 1px solid #E8D5CD; border-radius: 9px; background: #F2E6DF;
    text-align: center; color: {MAROON}; height: 20px; font-weight: 600;
}}
QProgressBar::chunk {{ background: {ORANGE}; border-radius: 8px; }}

QPlainTextEdit {{
    background: {MAROON_DEEP}; color: #F6E2D6; border: 1px solid {MAROON};
    border-radius: 10px; font-family: Consolas, Menlo, "DejaVu Sans Mono", monospace;
    font-size: 12px; padding: 9px; selection-background-color: {ORANGE};
}}
"""


# ---------------------------------------------------------------------------
# Lưu / nạp cấu hình
# ---------------------------------------------------------------------------
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Worker chạy pipeline ở luồng riêng để không treo giao diện
# ---------------------------------------------------------------------------
class PipelineWorker(QThread):
    sig_log = Signal(str)
    sig_progress = Signal(int, int)
    sig_done = Signal(str)
    sig_error = Signal(str)
    sig_file_done = Signal(str, str)   # (tên video, đường dẫn file kết quả) -> báo popup
    sig_notify = Signal(str, str, str)  # (tiêu đề, nội dung, chi tiết) -> thông báo hệ thống

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self._stop = False
        self.result_dir = ""    # thư mục kết quả cuối (đưa vào thông báo lúc xong)
        self.done_count = 0     # số video đã ghép xong (đưa vào thông báo lúc xong)

    def stop(self):
        self._stop = True

    def should_stop(self):
        return self._stop

    def log(self, msg):
        self.sig_log.emit(str(msg))

    def run(self):
        try:
            self._run()
            self.sig_done.emit("Đã dừng." if self._stop else "Hoàn tất!")
        except Exception as e:
            self.sig_error.emit(str(e))

    def _run(self):
        c = self.cfg
        ffmpeg = vu.find_binary("ffmpeg")
        ffprobe = vu.find_binary("ffprobe")
        if not ffmpeg or not ffprobe:
            raise RuntimeError(
                "Không tìm thấy ffmpeg/ffprobe trong PATH. Hãy cài ffmpeg trước."
            )

        out_dir = c["output"]
        seg_root = os.path.join(out_dir, "segments")
        proc_root = os.path.join(out_dir, "processed")
        final_root = os.path.join(out_dir, "final")
        manifest_path = os.path.join(out_dir, "manifest.json")
        os.makedirs(out_dir, exist_ok=True)

        # 1) TÁCH
        if c["do_split"]:
            videos = vu.collect_videos(c["input"], recursive=c["recursive"])
            if not videos:
                raise RuntimeError("Không tìm thấy video nào ở đầu vào.")
            self.log(f"Tìm thấy {len(videos)} video.")
            manifest = {"segment_seconds": c["seg_seconds"], "videos": []}
            for vi, src in enumerate(videos, 1):
                if self._stop:
                    return
                self.log(f"[Tách {vi}/{len(videos)}] {os.path.basename(src)}")
                self.sig_progress.emit(vi - 1, len(videos))
                rec = vu.split_video(
                    src, seg_root, seg_seconds=c["seg_seconds"],
                    ffmpeg=ffmpeg, ffprobe=ffprobe,
                    log=self.log, should_stop=self.should_stop,
                )
                manifest["videos"].append(rec)
                self.sig_progress.emit(vi, len(videos))
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            self.log(f"Đã lưu manifest: {manifest_path}")
            if not (c["do_vmake"] or c["do_merge"]):
                # Chỉ chạy bước Tách -> báo ngay ở đây (không có bước Ghép để báo).
                self.sig_notify.emit("✅ Xong bước Tách video",
                                     f"Đã tách {len(videos)} video thành các đoạn.",
                                     seg_root)
        else:
            if not os.path.exists(manifest_path):
                raise RuntimeError(
                    "Bỏ qua bước Tách nhưng không thấy manifest.json trong thư mục output.\n"
                    "Hãy chạy bước Tách ít nhất 1 lần."
                )
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            self.log("Đã nạp manifest có sẵn.")

        if self._stop:
            return

        # 2) XOÁ PHỤ ĐỀ QUA VMAKE
        if c["do_vmake"]:
            jobs = []
            for v in manifest["videos"]:
                safe = v["safe"]
                for seg in v["segments"]:
                    dst = os.path.join(proc_root, safe, os.path.basename(seg["file"]))
                    jobs.append((seg["file"], dst))
            self.log(f"Bắt đầu xử lý vmake: {len(jobs)} đoạn (chế độ {c['vmake_mode']}).")
            self.log(f"Nghỉ ngẫu nhiên giữa các đoạn: {c['delay_min']:.0f}–{c['delay_max']:.0f}s.")
            if c["headless"]:
                self.log("Chạy ẩn (không mở cửa sổ) — cứ thu nhỏ / làm việc khác, vẫn xử lý bình thường.")
            else:
                self.log("Cửa sổ trình duyệt sẽ mở ra. Đừng đóng tới khi xong.")
            total = len(jobs)
            # SỐ ĐOẠN XỬ LÝ SONG SONG. vmake xử lý PHÍA CLIENT (WebGL) nên mọi đoạn
            # song song DÙNG CHUNG 1 GPU trình duyệt: mở quá nhiều -> GPU dồn -> đoạn
            # cuối/áp chót đói tài nguyên, xử lý mãi không xong trong timeout -> bị bỏ
            # (đúng triệu chứng "1 đoạn quá lâu"). Nạp dồn dập cũng dễ bị vmake bóp.
            # -> chặn trần THẤP (4) cho ổn định; pipeline vẫn đẩy đoạn kế khi 1 đoạn
            # xong nên không nghỉ máy. (Tăng nếu máy khỏe & muốn nhanh hơn.)
            auto_batch = min(total, 4)
            self.log(f"Batch tự động = {auto_batch} (song song tối đa 4 cho ổn định).")
            processed = vmake_client.process_videos(
                jobs, mode=c["vmake_mode"], headless=c["headless"],
                per_video_timeout=c["timeout"],
                delay_min=c["delay_min"], delay_max=c["delay_max"],
                removal_type=c.get("removal_type", "Smart"),
                # session_path=SESSION_PATH,  # (đăng nhập đã tắt)
                batch_size=auto_batch,
                session_path=(SESSION_PATH if os.path.exists(SESSION_PATH) else None),
                log=self.log, should_stop=self.should_stop,
            )
            self.sig_progress.emit(processed, total)
            self.log(f"Đã xử lý {processed}/{total} đoạn qua vmake.")
            if not c["do_merge"]:
                # Không ghép -> bước vmake là bước cuối, báo luôn kẻo không có gì báo.
                self.sig_notify.emit("✅ Xong bước Xoá phụ đề",
                                     f"Đã xử lý {processed}/{total} đoạn qua vmake.",
                                     proc_root)

        if self._stop:
            return

        # 3) GHÉP
        if c["do_merge"]:
            vids = manifest["videos"]
            for vi, v in enumerate(vids, 1):
                if self._stop:
                    return
                safe = v["safe"]
                seg_files = []
                audio_files = []   # đoạn GỐC (để lấy lại tiếng nếu vmake rớt audio)
                durs = []
                starts = []
                for seg in v["segments"]:
                    base = os.path.basename(seg["file"])
                    proc = os.path.join(proc_root, safe, base)
                    seg_files.append(proc if os.path.exists(proc) else seg["file"])
                    audio_files.append(seg["file"])
                    durs.append(seg.get("dur"))
                    starts.append(seg.get("start"))
                out_path = os.path.join(final_root, f"{safe}_nosub.mp4")
                self.log(f"[Ghép {vi}/{len(vids)}] {v['name']}")
                self.sig_progress.emit(vi - 1, len(vids))
                vu.merge_segments(seg_files, out_path, ffmpeg=ffmpeg, ffprobe=ffprobe,
                                  log=self.log, durations=durs, starts=starts,
                                  source_path=v.get("source"),
                                  target_fps=v.get("fps"),
                                  audio_files=audio_files)
                self.log(f"  -> {out_path}")
                self.sig_progress.emit(vi, len(vids))
                # Báo ra ngoài tool: XONG 1 file (video hoàn chỉnh vừa ghép xong).
                self.done_count += 1
                self.sig_file_done.emit(v["name"], out_path)
            self.result_dir = final_root
            self.log(f"Video hoàn chỉnh nằm trong: {final_root}")


# ---------------------------------------------------------------------------
# Worker đăng nhập vmake (mở browser cho người dùng login rồi lưu session)
# ---------------------------------------------------------------------------
class LoginWorker(QThread):
    sig_log = Signal(str)
    sig_done = Signal(bool)

    def __init__(self, session_path):
        super().__init__()
        self.session_path = session_path
        self._finish = threading.Event()

    def confirm_finish(self):
        self._finish.set()

    def run(self):
        try:
            ok = vmake_client.open_login(
                self.session_path,
                should_finish=self._finish.is_set,
                log=lambda m: self.sig_log.emit(str(m)),
            )
            self.sig_done.emit(bool(ok))
        except Exception as e:
            self.sig_log.emit("LỖI đăng nhập: " + str(e))
            self.sig_done.emit(False)


# ---------------------------------------------------------------------------
# Worker lấy danh sách proxy free từ các nguồn công khai
# ---------------------------------------------------------------------------
class ProxyFetchWorker(QThread):
    sig_log = Signal(str)
    sig_done = Signal(list)

    SOURCES = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    ]
    LIMIT = 200

    def run(self):
        import urllib.request
        import re
        pat = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$")
        seen, found = set(), []
        for url in self.SOURCES:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                text = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
                add = 0
                for line in text.splitlines():
                    line = line.strip()
                    if pat.match(line) and line not in seen:
                        seen.add(line)
                        found.append(line)
                        add += 1
                self.sig_log.emit(f"  + {add} proxy từ {url.split('/')[2]} (tổng {len(found)})")
            except Exception as e:
                self.sig_log.emit(f"  Nguồn lỗi ({url.split('/')[2]}): {e}")
            if len(found) >= self.LIMIT:
                break
        self.sig_done.emit(found[: self.LIMIT])


# ---------------------------------------------------------------------------
# Cửa sổ chính
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TNT GROUP — Tách & Xoá phụ đề video")
        self.resize(720, 600)
        logo_path = os.path.join(APP_DIR, "logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        self.worker = None
        self.login_worker = None
        self.proxy_fetcher = None
        self._popups = []          # giữ tham chiếu popup không-chặn (khỏi bị dọn rác)
        # Thông báo hệ thống: hiện NGOÀI tool (toast góc màn hình / Notification Center)
        # nên người dùng thu nhỏ tool đi làm việc khác vẫn thấy báo xong.
        # Windows/Linux dùng icon khay; macOS dùng Notification Center — xem notifier.py.
        self._notifier = Notifier(
            app_name="TNT — Tách & Xoá phụ đề video",
            icon=self.windowIcon(),
            parent=self,
            on_activated=self.restore_window,   # bấm icon khay -> mở lại cửa sổ
        )
        self._build_ui()
        self._apply_cfg(load_config())
        self._update_session_label()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # --- Header ---
        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 12, 16, 12)
        logo_path = os.path.join(APP_DIR, "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(56, Qt.SmoothTransformation)
            logo_lbl = QLabel()
            logo_lbl.setPixmap(pix)
            hl.addWidget(logo_lbl)
        txt = QVBoxLayout()
        txt.setSpacing(2)
        title = QLabel("Tách & Xoá phụ đề video")
        title.setObjectName("title")
        sub = QLabel("TNT GROUP  •  Video Subtitle Remover (vmake.ai)")
        sub.setObjectName("subtitle")
        txt.addWidget(title)
        txt.addWidget(sub)
        hl.addLayout(txt)
        hl.addStretch(1)
        root.addWidget(header)

        # --- 2 tab cho gọn ---
        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        tab1 = QWidget()
        t1 = QVBoxLayout(tab1)
        t1.setSpacing(12)
        tabs.addTab(tab1, "1. Nguồn (vào / ra)")
        tab2 = QWidget()
        t2 = QVBoxLayout(tab2)
        t2.setSpacing(12)
        tabs.addTab(tab2, "2. Cấu hình & Chạy")

        # --- Đầu vào ---
        in_box = QGroupBox("Đầu vào")
        gl = QGridLayout(in_box)
        self.rb_file = QRadioButton("1 video")
        self.rb_folder = QRadioButton("1 thư mục chứa nhiều video")
        self.rb_file.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_file)
        grp.addButton(self.rb_folder)
        self.ed_input = QLineEdit()
        self.ed_input.setPlaceholderText("Đường dẫn video hoặc thư mục…")
        btn_in = QPushButton("Chọn…")
        btn_in.clicked.connect(self.pick_input)
        self.cb_recursive = QCheckBox("Quét cả thư mục con")
        gl.addWidget(self.rb_file, 0, 0)
        gl.addWidget(self.rb_folder, 0, 1)
        gl.addWidget(self.cb_recursive, 0, 2)
        gl.addWidget(QLabel("Đường dẫn:"), 1, 0)
        gl.addWidget(self.ed_input, 1, 1)
        gl.addWidget(btn_in, 1, 2)
        t1.addWidget(in_box)

        # --- Đầu ra ---
        out_box = QGroupBox("Thư mục lưu kết quả")
        ol = QHBoxLayout(out_box)
        self.ed_output = QLineEdit(os.path.join(os.getcwd(), "vmake_output"))
        btn_out = QPushButton("Chọn…")
        btn_out.clicked.connect(self.pick_output)
        ol.addWidget(self.ed_output)
        ol.addWidget(btn_out)
        t1.addWidget(out_box)

        # --- Tuỳ chọn ---
        opt_box = QGroupBox("Tuỳ chọn")
        og = QGridLayout(opt_box)
        og.addWidget(QLabel("Độ dài mỗi đoạn (giây):"), 0, 0)
        self.sp_seg = QDoubleSpinBox()
        self.sp_seg.setRange(1.0, 60.0)
        self.sp_seg.setSingleStep(0.5)
        self.sp_seg.setValue(4.0)
        og.addWidget(self.sp_seg, 0, 1)

        self.cb_split = QCheckBox("Tách video")
        self.cb_vmake = QCheckBox("Xoá phụ đề (vmake)")
        self.cb_merge = QCheckBox("Ghép lại")
        for cb in (self.cb_split, self.cb_vmake, self.cb_merge):
            cb.setChecked(True)
        og.addWidget(QLabel("Các bước:"), 1, 0)
        steps = QHBoxLayout()
        steps.addWidget(self.cb_split)
        steps.addWidget(self.cb_vmake)
        steps.addWidget(self.cb_merge)
        steps.addStretch(1)
        steps_w = QWidget()
        steps_w.setLayout(steps)
        og.addWidget(steps_w, 1, 1, 1, 2)

        og.addWidget(QLabel("Chế độ vmake:"), 2, 0)
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItem("Tự động", "auto")
        self.cmb_mode.addItem("Bán tự động", "semi")
        og.addWidget(self.cmb_mode, 2, 1)
        self.cb_headless = QCheckBox("Chạy ẩn (khuyên dùng)")
        self.cb_headless.setChecked(True)   # mặc định ẩn -> thu nhỏ/làm việc khác vẫn xử lý
        self.cb_headless.setToolTip(
            "Chạy ẩn (không mở cửa sổ trình duyệt). KHUYÊN DÙNG: không có cửa sổ nên "
            "không bị lỗi 'đợi lâu' khi bạn thu nhỏ / đi làm việc khác. Vẫn dùng GPU "
            "nên không chậm. Chỉ bỏ chọn nếu muốn NHÌN trình duyệt chạy để soi lỗi."
        )
        og.addWidget(self.cb_headless, 2, 2)

        og.addWidget(QLabel("Loại xoá (chế độ Tự động):"), 3, 0)
        self.cmb_removal = QComboBox()
        self.cmb_removal.addItem("Smart (xoá thông minh)", "Smart")
        self.cmb_removal.addItem("Subtitle (phụ đề)", "Subtitle")
        self.cmb_removal.addItem("Watermark", "Watermark")
        og.addWidget(self.cmb_removal, 3, 1, 1, 2)

        og.addWidget(QLabel("Timeout mỗi đoạn (giây):"), 4, 0)
        self.sp_timeout = QDoubleSpinBox()
        self.sp_timeout.setRange(30, 1800)
        self.sp_timeout.setSingleStep(30)
        self.sp_timeout.setValue(300)
        og.addWidget(self.sp_timeout, 4, 1)

        # Nghỉ ngẫu nhiên giữa các đoạn
        og.addWidget(QLabel("Nghỉ ngẫu nhiên giữa đoạn (giây):"), 5, 0)
        delay_w = QWidget()
        dh = QHBoxLayout(delay_w)
        dh.setContentsMargins(0, 0, 0, 0)
        # Giãn cách NGẪU NHIÊN giữa các lần up. Bản thân mỗi lần up (nạp file + chọn
        # loại + Apply) đã cách nhau ~4–5s nên chỉ cần thêm 1–2s cho vmake dựng lại
        # ô upload là đủ; đặt nhỏ để up nhanh (tool tự chặn trần ~8s nếu đặt lớn).
        self.sp_delay_min = QDoubleSpinBox()
        self.sp_delay_min.setRange(1.0, 3600.0)
        self.sp_delay_min.setValue(1.0)
        self.sp_delay_max = QDoubleSpinBox()
        self.sp_delay_max.setRange(1.0, 3600.0)
        self.sp_delay_max.setValue(2.0)
        dh.addWidget(QLabel("min"))
        dh.addWidget(self.sp_delay_min)
        dh.addWidget(QLabel("max"))
        dh.addWidget(self.sp_delay_max)
        dh.addStretch(1)
        og.addWidget(delay_w, 5, 1, 1, 2)

        og.addWidget(QLabel("Số video xử lý song song (batch):"), 6, 0)
        self.sp_batch = QSpinBox()
        self.sp_batch.setRange(1, 15)
        self.sp_batch.setValue(15)
        self.sp_batch.setEnabled(False)   # TỰ ĐỘNG = số đoạn (trần 15) — không chỉnh tay
        self.sp_batch.setToolTip(
            "Tự động = ĐÚNG số đoạn video bị cắt ra (xử lý hết trong 1 lượt), nhưng "
            "tối đa 15 để không mở quá nhiều task song song gây nặng máy/vmake."
        )
        og.addWidget(self.sp_batch, 6, 1)

        # --- Thông báo khi xong (hiện NGOÀI tool, kể cả lúc thu nhỏ) ---
        og.addWidget(QLabel("Thông báo khi xong:"), 7, 0)
        noti_w = QWidget()
        nh = QHBoxLayout(noti_w)
        nh.setContentsMargins(0, 0, 0, 0)
        self.cb_popup = QCheckBox("Kèm popup mỗi khi xong 1 video")
        self.cb_popup.setToolTip(
            "Mặc định tool báo bằng THÔNG BÁO HỆ THỐNG (góc màn hình / Notification "
            "Center) nên thu nhỏ tool vẫn thấy. Bật thêm mục này nếu muốn CHẮC CHẮN "
            "thấy: mỗi video xong sẽ bung thêm 1 cửa sổ popup nổi trên cùng."
        )
        btn_test_noti = QPushButton("Thử thông báo")
        btn_test_noti.setToolTip(
            "Bấm thử để xem máy có hiện thông báo không. Không thấy gì -> vào cài đặt "
            "Thông báo của hệ điều hành bật cho ứng dụng này (Windows: Settings → "
            "Notifications; macOS: Cài đặt → Thông báo)."
        )
        btn_test_noti.clicked.connect(self.test_notification)
        nh.addWidget(self.cb_popup)
        nh.addWidget(btn_test_noti)
        nh.addStretch(1)
        og.addWidget(noti_w, 7, 1, 1, 2)
        t2.addWidget(opt_box)

        # --- Phiên đăng nhập vmake (BẬT LẠI để test hạn mức theo tài khoản) ---
        login_box = QGroupBox("Phiên đăng nhập vmake (đăng nhập để dùng tiếp khi hết lượt free ẩn danh)")
        lr = QHBoxLayout(login_box)
        self.lbl_session = QLabel()
        self.btn_login = QPushButton("Đăng nhập vmake & lưu phiên")
        self.btn_login.clicked.connect(self.start_login)
        self.btn_login_done = QPushButton("Tôi đã đăng nhập xong")
        self.btn_login_done.clicked.connect(self.finish_login)
        self.btn_login_done.setEnabled(False)
        lr.addWidget(self.lbl_session, 1)
        lr.addWidget(self.btn_login)
        lr.addWidget(self.btn_login_done)
        t1.insertWidget(0, login_box)

        # --- Proxy / xoay IP / Tor: ĐÃ ẨN (proxy free đa số chết, Tor bị chặn — ưu
        #     tiên đăng nhập tài khoản + đổi IP tay khi cần). Muốn bật lại: bỏ comment
        #     khối dưới + các dòng proxies/tor trong _collect_cfg, _apply_cfg, start(). ---
        # proxy_box = QGroupBox("Proxy / xoay IP (mỗi dòng 1 proxy; để trống = dùng IP máy)")
        # pv = QVBoxLayout(proxy_box)
        # self.ed_proxies = QPlainTextEdit()
        # self.ed_proxies.setMaximumHeight(90)
        # pv.addWidget(self.ed_proxies)
        # self.btn_fetch_proxy = QPushButton("Lấy proxy free")
        # self.btn_fetch_proxy.clicked.connect(self.fetch_proxies)
        # pv.addWidget(self.btn_fetch_proxy)
        # self.cb_tor = QCheckBox("Dùng Tor (tự xoay IP free)")
        # self.ed_tor_socks = QLineEdit("9050"); self.ed_tor_ctrl = QLineEdit("9051")
        # self.ed_tor_pass = QLineEdit()
        # pv.addWidget(self.cb_tor)
        # t1.addWidget(proxy_box)

        t1.addStretch(1)

        # --- Nút điều khiển ---
        ctrl = QHBoxLayout()
        self.btn_save = QPushButton("Lưu cấu hình")
        self.btn_save.clicked.connect(self.on_save_config)
        ctrl.addWidget(self.btn_save)
        ctrl.addStretch(1)
        self.btn_start = QPushButton("Bắt đầu")
        self.btn_start.setObjectName("primary")
        self.btn_start.clicked.connect(self.start)
        self.btn_stop = QPushButton("Dừng")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        ctrl.addWidget(self.btn_start)
        ctrl.addWidget(self.btn_stop)
        t2.addLayout(ctrl)

        self.progress = QProgressBar()
        t2.addWidget(self.progress)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        t2.addWidget(self.log_view, 1)

    # ----- cấu hình -----
    def _collect_cfg(self):
        return {
            "input_is_file": self.rb_file.isChecked(),
            "input": self.ed_input.text().strip(),
            "output": self.ed_output.text().strip(),
            "recursive": self.cb_recursive.isChecked(),
            "seg_seconds": self.sp_seg.value(),
            "do_split": self.cb_split.isChecked(),
            "do_vmake": self.cb_vmake.isChecked(),
            "do_merge": self.cb_merge.isChecked(),
            "vmake_mode": self.cmb_mode.currentData(),
            "removal_type": self.cmb_removal.currentData(),
            "headless": self.cb_headless.isChecked(),
            "timeout": self.sp_timeout.value(),
            "delay_min": self.sp_delay_min.value(),
            "delay_max": self.sp_delay_max.value(),
            "batch_size": int(self.sp_batch.value()),
            "popup_each": self.cb_popup.isChecked(),
            # --- proxy/tor đã ẩn ---
            # "proxies": [...], "use_tor": ..., "tor_socks": ..., "tor_ctrl": ..., "tor_pass": ...,
        }

    def _apply_cfg(self, cfg):
        if not cfg:
            return
        if cfg.get("input_is_file", True):
            self.rb_file.setChecked(True)
        else:
            self.rb_folder.setChecked(True)
        self.ed_input.setText(cfg.get("input", self.ed_input.text()))
        if cfg.get("output"):
            self.ed_output.setText(cfg["output"])
        self.cb_recursive.setChecked(cfg.get("recursive", False))
        self.sp_seg.setValue(cfg.get("seg_seconds", 4.0))
        self.cb_split.setChecked(cfg.get("do_split", True))
        self.cb_vmake.setChecked(cfg.get("do_vmake", True))
        self.cb_merge.setChecked(cfg.get("do_merge", True))
        idx = self.cmb_mode.findData(cfg.get("vmake_mode", "auto"))
        if idx >= 0:
            self.cmb_mode.setCurrentIndex(idx)
        ridx = self.cmb_removal.findData(cfg.get("removal_type", "Smart"))
        # Cấu hình cũ có thể lưu 'Passerby' (đã bỏ) -> không tìm thấy -> về Smart.
        self.cmb_removal.setCurrentIndex(ridx if ridx >= 0 else 0)
        self.cb_headless.setChecked(cfg.get("headless", True))
        self.sp_timeout.setValue(cfg.get("timeout", 300))
        self.sp_delay_min.setValue(cfg.get("delay_min", 1.0))
        self.sp_delay_max.setValue(cfg.get("delay_max", 2.0))
        self.sp_batch.setValue(int(cfg.get("batch_size", 10)))
        self.cb_popup.setChecked(bool(cfg.get("popup_each", False)))
        # --- proxy/tor đã ẩn — không nạp ed_proxies/cb_tor/tor_* nữa ---

    def on_save_config(self):
        if save_config(self._collect_cfg()):
            self.append_log(f"Đã lưu cấu hình: {CONFIG_PATH}")
        else:
            self.append_log("Không lưu được cấu hình.")

    # ----- chọn file/folder -----
    def pick_input(self):
        if self.rb_file.isChecked():
            path, _ = QFileDialog.getOpenFileName(
                self, "Chọn video", "",
                "Video (*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.flv *.wmv *.ts);;Tất cả (*)",
            )
        else:
            path = QFileDialog.getExistingDirectory(self, "Chọn thư mục video")
        if path:
            self.ed_input.setText(path)

    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
        if path:
            self.ed_output.setText(path)

    # ----- log -----
    def append_log(self, msg):
        self.log_view.appendPlainText(msg)
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    def set_progress(self, cur, total):
        if total <= 0:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, total)
            self.progress.setValue(cur)

    # ----- đăng nhập vmake -----
    def _update_session_label(self):
        if os.path.exists(SESSION_PATH):
            self.lbl_session.setText("Đã có phiên đăng nhập ✓")
        else:
            self.lbl_session.setText("Chưa đăng nhập (đang chạy ẩn danh)")

    def start_login(self):
        if self.login_worker and self.login_worker.isRunning():
            return
        self.append_log("Mở trình duyệt để đăng nhập vmake… Đăng nhập xong bấm 'Tôi đã đăng nhập xong'.")
        self.btn_login.setEnabled(False)
        self.btn_login_done.setEnabled(True)
        self.login_worker = LoginWorker(SESSION_PATH)
        self.login_worker.sig_log.connect(self.append_log)
        self.login_worker.sig_done.connect(self.on_login_done)
        self.login_worker.start()

    def finish_login(self):
        if self.login_worker:
            self.login_worker.confirm_finish()
            self.btn_login_done.setEnabled(False)
            self.append_log("Đang lưu phiên…")

    def on_login_done(self, ok):
        self.btn_login.setEnabled(True)
        self.btn_login_done.setEnabled(False)
        self._update_session_label()
        self.append_log("Đã lưu phiên đăng nhập." if ok else "Không lưu được phiên (thử lại).")

    # ----- lấy proxy free -----
    def fetch_proxies(self):
        if self.proxy_fetcher and self.proxy_fetcher.isRunning():
            return
        self.append_log("Đang lấy danh sách proxy free…")
        self.btn_fetch_proxy.setEnabled(False)
        self.proxy_fetcher = ProxyFetchWorker()
        self.proxy_fetcher.sig_log.connect(self.append_log)
        self.proxy_fetcher.sig_done.connect(self.on_proxies_fetched)
        self.proxy_fetcher.start()

    def on_proxies_fetched(self, proxies):
        self.btn_fetch_proxy.setEnabled(True)
        if proxies:
            self.ed_proxies.setPlainText("\n".join(proxies))
            self.cb_tor.setChecked(False)  # dùng proxy nên tắt Tor cho khỏi xung đột
            self.append_log(
                f"Đã lấy {len(proxies)} proxy, điền vào ô proxy (đã tắt Tor). "
                "Bấm Bắt đầu — tool tự bỏ proxy chết, dùng cái sống."
            )
        else:
            self.append_log("Không lấy được proxy nào (mạng/nguồn lỗi). Thử lại sau.")

    # ----- chạy -----
    def start(self):
        cfg = self._collect_cfg()
        if not cfg["input"]:
            QMessageBox.warning(self, "Thiếu thông tin", "Hãy chọn video/thư mục đầu vào.")
            return
        if not cfg["output"]:
            QMessageBox.warning(self, "Thiếu thông tin", "Hãy chọn thư mục lưu kết quả.")
            return
        if cfg["delay_max"] < cfg["delay_min"]:
            cfg["delay_min"], cfg["delay_max"] = cfg["delay_max"], cfg["delay_min"]

        save_config(cfg)  # tự lưu cấu hình mỗi lần chạy

        self.log_view.clear()
        self.append_log("Bắt đầu…")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.worker = PipelineWorker(cfg)
        self.worker.sig_log.connect(self.append_log)
        self.worker.sig_progress.connect(self.set_progress)
        self.worker.sig_done.connect(self.on_done)
        self.worker.sig_error.connect(self.on_error)
        self.worker.sig_file_done.connect(self.on_file_done)
        self.worker.sig_notify.connect(self.notify_outside)
        self.worker.start()

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.append_log("Đang yêu cầu dừng (sẽ dừng sau bước hiện tại)…")

    # ----- thông báo hiện NGOÀI tool (kể cả khi cửa sổ đang thu nhỏ) -----
    def restore_window(self):
        """Mở lại cửa sổ khi bấm vào icon khay / thông báo."""
        try:
            self.showNormal()
            self.raise_()
            self.activateWindow()
        except Exception:
            pass

    def notify_outside(self, title, body, detail="", popup_fallback=True):
        """Đẩy 1 thông báo ra ngoài tool. Không gửi được -> bung popup nổi trên cùng."""
        shown = False
        try:
            shown = self._notifier.notify(title, body, detail)
        except Exception:
            shown = False
        if not shown and popup_fallback:
            self.show_popup(title, body, detail)
        self.flash_taskbar()

    def flash_taskbar(self):
        """Nháy nút taskbar (Windows) / nảy icon dock (macOS) để gây chú ý."""
        try:
            QApplication.alert(self)          # cửa sổ chính (đang thu nhỏ vẫn nháy)
            QApplication.alert(None)          # ứng dụng — mac nảy dock kể cả khi ẩn
        except Exception:
            pass

    def show_popup(self, title, body, detail=""):
        """Popup KHÔNG chặn xử lý. Không đặt cha để hiện được cả khi cửa sổ thu nhỏ."""
        try:
            box = QMessageBox(None)           # KHÔNG parent -> cửa sổ độc lập
            box.setWindowTitle(title)
            box.setText(body)
            if detail:
                box.setInformativeText(detail)
            box.setIcon(QMessageBox.Information)
            box.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            box.setModal(False)
            box.finished.connect(lambda _=None, b=box: self._popups.remove(b)
                                 if b in self._popups else None)
            self._popups.append(box)
            box.show()
            box.raise_()
        except Exception:
            pass

    def on_done(self, msg):
        self.append_log(msg)
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        # Báo XONG TOÀN BỘ ra ngoài tool + popup tổng kết (dù có đang thu nhỏ).
        stopped = msg.startswith("Đã dừng")
        n = getattr(self.worker, "done_count", 0) if self.worker else 0
        out_dir = getattr(self.worker, "result_dir", "") if self.worker else ""
        if stopped:
            title, body = "⏹ Đã dừng", "Đã dừng theo yêu cầu."
        else:
            title = "🎉 Xong tất cả!"
            body = (f"Đã hoàn tất {n} video." if n else "Đã hoàn tất công việc.")
        self.notify_outside(title, body, out_dir, popup_fallback=False)
        self.show_popup(title, body, out_dir)

    def on_file_done(self, name, path):
        """Báo KHI XONG 1 video (không chặn xử lý các video còn lại)."""
        title, body = "✅ Xong 1 video", f"Đã xử lý xong: {name}"
        # popup_fallback: nếu người dùng đã tick "kèm popup" thì tự bung ở dưới,
        # khỏi bung 2 lần khi thông báo hệ thống lỗi.
        want_popup = self.cb_popup.isChecked()
        self.notify_outside(title, body, path, popup_fallback=not want_popup)
        if want_popup:
            self.show_popup(title, body, path)

    def test_notification(self):
        """Nút 'Thử thông báo': kiểm tra máy có hiện thông báo ngoài tool không."""
        self.append_log("Đang gửi thông báo thử… (thu nhỏ tool ra sẽ thấy ở góc màn hình)")
        ok = False
        try:
            ok = self._notifier.notify(
                "🔔 Thử thông báo",
                "Thông báo hoạt động! Khi xong mỗi video bạn sẽ thấy báo như này.",
                "TNT — Tách & Xoá phụ đề video")
        except Exception as e:
            self.append_log(f"Lỗi gửi thông báo: {e}")
        self.flash_taskbar()
        if ok:
            self.append_log(
                "Đã gửi thông báo. KHÔNG thấy gì? -> bật thông báo cho ứng dụng trong "
                "cài đặt hệ điều hành (Windows: Settings → Notifications, tắt Focus "
                "assist; macOS: Cài đặt → Thông báo), hoặc tick 'Kèm popup mỗi khi "
                "xong 1 video'.")
        else:
            self.append_log(
                "Máy không gửi được thông báo hệ thống -> tool sẽ dùng POPUP thay thế.")
            self.show_popup("🔔 Thử thông báo",
                            "Máy không hiện được thông báo hệ thống.",
                            "Tool sẽ báo bằng popup như cửa sổ này.")

    def on_error(self, msg):
        self.append_log("LỖI: " + msg)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        # Báo lỗi ra ngoài trước (thu nhỏ vẫn thấy), rồi mới mở hộp thoại chi tiết.
        self.notify_outside("❌ Lỗi — đã dừng", msg.splitlines()[0][:180],
                            popup_fallback=False)
        QMessageBox.critical(self, "Lỗi", msg)

    def closeEvent(self, event):
        try:
            self._notifier.shutdown()
        except Exception:
            pass
        for b in list(self._popups):
            try:
                b.close()
            except Exception:
                pass
        super().closeEvent(event)


def main():
    check_license("TNT_VideoSubtitle")   # BẢO MẬT LICENSE — kiểm trước khi mở app.
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
