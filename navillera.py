import os
import sys
import platform
import shutil
import stat
import urllib.request
import json
import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QProcess, QTimer, QSettings, QUrl
from PySide6.QtGui import QKeySequence, QShortcut, QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPlainTextEdit,
    QPushButton, QLabel, QFileDialog, QLineEdit, QMessageBox, QGroupBox, QCheckBox,
    QSpinBox, QFormLayout, QComboBox
)

APP_NAME = "Navillera"

# -------------------------
# Paths & Downloads
# -------------------------

def app_bin_dir() -> Path:
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "bin"
    return Path.cwd() / "bin"

def user_downloads_dir() -> Path:
    home = Path.home()
    dl = home / "Downloads"
    return dl if dl.exists() else home

def detect_asset_candidates():
    sysname = platform.system().lower()
    if sysname == "windows":
        return [
            ("https://github.com/mikf/gallery-dl/releases/latest/download/gallery-dl.exe", "gallery-dl.exe"),
            ("https://github.com/gdl-org/builds/releases/latest/download/gallery-dl_windows_x64.exe", "gallery-dl.exe"),
        ]
    elif sysname == "darwin":
        return [
            ("https://github.com/gdl-org/builds/releases/latest/download/gallery-dl_macos_universal", "gallery-dl"),
            ("https://github.com/mikf/gallery-dl/releases/latest/download/gallery-dl.bin", "gallery-dl"),
        ]
    else:
        return [
            ("https://github.com/gdl-org/builds/releases/latest/download/gallery-dl_linux", "gallery-dl"),
            ("https://github.com/mikf/gallery-dl/releases/latest/download/gallery-dl.bin", "gallery-dl"),
        ]

def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url: str, dest: Path, expected_sha256: str | None = None, timeout: int = 20):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp")
    req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME} (PySide6)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as f:
        shutil.copyfileobj(resp, f)
    if expected_sha256:
        got = sha256sum(tmp)
        if got.lower() != expected_sha256.lower():
            try: tmp.unlink()
            finally: raise ValueError(f"Checksum mismatch (got {got[:12]}...)")
    tmp.replace(dest)

def make_executable(path: Path):
    if sys.platform.startswith("win"):
        return
    mode = os.stat(path).st_mode
    os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# -------------------------
# Version helpers
# -------------------------

_re_ver = re.compile(r"(?i)\b(\d+\.\d+(?:\.\d+)*)\b")

def parse_version(text: str) -> str | None:
    m = _re_ver.search(text or "")
    return m.group(1) if m else None

def get_local_version(bin_path: Path) -> str | None:
    if not bin_path.exists():
        return None
    try:
        import subprocess
        out = subprocess.check_output([str(bin_path), "--version"], text=True, timeout=8)
        return parse_version(out)
    except Exception:
        return None

def get_latest_version_tag() -> str | None:
    url = "https://api.github.com/repos/mikf/gallery-dl/releases/latest"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"{APP_NAME} (PySide6)", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
            tag = data.get("tag_name") or ""
            return tag[1:] if tag.startswith("v") else tag
    except Exception:
        return None

def is_newer(ver_local: str, ver_remote: str) -> bool:
    def parts(v: str):
        main = v.split("-", 1)[0]
        return [int(x) for x in main.split(".") if x.isdigit()]
    try:
        return parts(ver_remote) > parts(ver_local)
    except Exception:
        return False

# -------------------------
# Styling (Catppuccin Mocha QSS)
# -------------------------

def apply_styles(app):
    app.setStyle("Fusion")
    base      = "#1e1e2e"
    mantle    = "#181825"
    crust     = "#11111b"
    text      = "#cdd6f4"
    subtext0  = "#a6adc8"
    overlay0  = "#6c7086"
    surface0  = "#313244"
    surface1  = "#45475a"
    surface2  = "#585b70"
    blue      = "#89b4fa"
    red       = "#f38ba8"
    green     = "#a6e3a1"
    lavender  = "#b4befe"

    qss = f"""
    QWidget {{ background: {base}; color: {text}; font-family: "Segoe UI","Inter","Cantarell",sans-serif; font-size: 14px; }}
    QLabel#titleLabel {{ font-size: 20px; font-weight: 800; color: {lavender}; }}
    QLabel#infoLabel {{ color: {subtext0}; font-size: 13px; }}
    QLabel#sectionLabel {{ color: {subtext0}; font-weight: 600; margin-top: 2px; margin-bottom: 4px; }}
    QGroupBox {{ border: 1px solid {surface1}; border-radius: 12px; background: {mantle}; margin-top: 10px; padding: 10px 12px 12px 12px; }}
    QGroupBox::title {{ subcontrol-origin: margin; padding: 0 6px; color: {subtext0}; background: transparent; }}
    QLineEdit, QPlainTextEdit, QTextEdit {{ background: {crust}; border: 1px solid {surface1}; border-radius: 10px; padding: 8px 10px; selection-background-color: {blue}; selection-color: #0b0b0b; }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{ border: 1px solid {blue}; outline: none; }}
    QTextEdit#logView, QPlainTextEdit#urlsEdit {{ background: {mantle}; border-color: {surface0}; font-family: "Cascadia Code","Consolas",monospace; font-size: 12px; }}
    QPushButton {{ background-color: {surface1}; color: {text}; border: 1px solid {surface2}; border-radius: 10px; padding: 8px 14px; font-weight: 600; }}
    QPushButton:hover {{ background-color: {surface2}; border-color: {overlay0}; }}
    QPushButton:pressed {{ background-color: {surface0}; }}
    QPushButton:disabled {{ color: {overlay0}; background-color: {surface0}; border-color: {surface0}; }}
    QPushButton#primaryBtn {{ background-color: {blue}; border: 1px solid {blue}; color: #0b0b0b; }}
    QPushButton#primaryBtn:hover {{ background-color: {green}; border-color: {green}; }}
    QPushButton#dangerBtn {{ background-color: {red}; border: 1px solid {red}; color: #0b0b0b; }}
    QLabel.chip {{ padding: 4px 8px; border-radius: 8px; background: {surface1}; }}
    """
    app.setStyleSheet(qss)

# -------------------------
# Main App
# -------------------------

class Navillera(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — gallery-dl GUI")
        self.resize(860, 660)

        self.settings = QSettings(APP_NAME, "gallery-dl")

        self.proc: QProcess | None = None
        self.queue: list[str] = []
        self.bin_path: Path = app_bin_dir() / ("gallery-dl.exe" if sys.platform.startswith("win") else "gallery-dl")

        # Stats
        self._totals = {"downloaded": 0, "skipped": 0, "failed": 0}

        # Batch tracking
        self._batch_started_at: float = 0.0
        self._batch_urls: list[str] = []
        self._batch_index: int = -1
        self._batches: list[list[str]] = []

        # Live helpers
        self._seen_paths: set[str] = set()
        self._error_lines: int = 0

        # Update throttle (persisted)
        self._last_update_check = float(self.settings.value("last_update_check_ts", 0.0))

        self._build_ui()
        self._load_settings()

        QTimer.singleShot(250, self.show_version_if_present)
        QTimer.singleShot(700, self.maybe_check_update)

        self.setAcceptDrops(True)
        self._install_shortcuts()

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        self.version_line = QLineEdit()
        self.version_line.setReadOnly(True)
        self.version_line.setPlaceholderText("gallery-dl version…")
        header.addWidget(self.version_line, 0)

        # Short description
        info = QLabel("1) Fetch/Update  2) Paste URLs  3) (Optional) settings  4) Run")
        info.setObjectName("infoLabel")
        info.setWordWrap(True)

        # Toolbar
        toolbar = QHBoxLayout()
        self.fetch_btn = QPushButton("Fetch / Update")
        self.fetch_btn.setObjectName("primaryBtn")
        self.fetch_btn.clicked.connect(self.fetch_binary)

        self.load_txt_btn = QPushButton("Load .txt")
        self.load_txt_btn.clicked.connect(self.load_txt)

        self.test_btn = QPushButton("Test URL")
        self.test_btn.setToolTip("Dry run (-g): resolve media URLs only — no files saved")
        self.test_btn.clicked.connect(self.test_url)

        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)

        self.run_btn = QPushButton("Run")
        self.run_btn.setObjectName("primaryBtn")
        self.run_btn.clicked.connect(self.start_run)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_run)

        toolbar.addWidget(self.fetch_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.load_txt_btn)
        toolbar.addWidget(self.test_btn)
        toolbar.addWidget(self.clear_log_btn)
        toolbar.addWidget(self.run_btn)
        toolbar.addWidget(self.stop_btn)

        # Summary bar
        summary = QHBoxLayout()
        summary.setSpacing(10)
        self.sum_downloaded = QLabel("✅ Downloaded: 0")
        self.sum_downloaded.setProperty("class", "chip")
        self.sum_skipped = QLabel("⚠️ Skipped: 0")
        self.sum_skipped.setProperty("class", "chip")
        self.sum_failed = QLabel("❌ Failed: 0")
        self.sum_failed.setProperty("class", "chip")
        self.sum_progress = QLabel("▶️ 0 / 0")
        self.sum_progress.setProperty("class", "chip")
        summary.addWidget(self.sum_downloaded)
        summary.addWidget(self.sum_skipped)
        summary.addWidget(self.sum_failed)
        summary.addStretch()
        summary.addWidget(self.sum_progress)

        # Settings group
        settings = QGroupBox("Settings")
        s_layout = QVBoxLayout(settings)
        s_layout.setSpacing(8)

        # UA row
        ua_row = QHBoxLayout()
        self.ua_use_browser = QCheckBox("Use system browser UA")
        self.ua_use_browser.setChecked(True)
        self.ua_use_browser.setToolTip("When checked, uses: --user-agent browser")
        self.ua_edit = QLineEdit()
        self.ua_edit.setPlaceholderText('Custom UA (enabled when unchecked)')
        self.ua_edit.setEnabled(False)
        self.ua_use_browser.stateChanged.connect(lambda st: self.ua_edit.setEnabled(st != Qt.Checked))
        ua_row.addWidget(QLabel("User-Agent:"))
        ua_row.addWidget(self.ua_use_browser)
        ua_row.addWidget(self.ua_edit, 1)

        # Cookies row
        ck_row = QHBoxLayout()
        self.cookies_file_edit = QLineEdit()
        self.cookies_file_edit.setPlaceholderText("cookies.txt (Netscape or JSON)")
        ck_choose_btn = QPushButton("Choose…")
        ck_choose_btn.clicked.connect(self.pick_cookies_file)
        ck_delete_btn = QPushButton("Delete")
        ck_delete_btn.setObjectName("dangerBtn")
        ck_delete_btn.setToolTip("Delete the selected cookies file from disk")
        ck_delete_btn.clicked.connect(self.delete_selected_cookies_file)
        ck_row.addWidget(QLabel("Cookies:"))
        ck_row.addWidget(self.cookies_file_edit, 1)
        ck_row.addWidget(ck_choose_btn)
        ck_row.addWidget(ck_delete_btn)

        # Output row
        out_row = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setObjectName("pathEdit")
        self.output_dir_edit.setPlaceholderText("Output folder (default: ~/Downloads/gallery-dl)")
        out_btn = QPushButton("Browse…")
        out_btn.clicked.connect(self.pick_output_dir)
        out_row.addWidget(QLabel("Output:"))
        out_row.addWidget(self.output_dir_edit, 1)
        out_row.addWidget(out_btn)

        # Advanced (collapsible)
        self.adv_toggle_btn = QPushButton("Advanced ▸")
        self.adv_toggle_btn.setCheckable(True)
        self.adv_toggle_btn.setChecked(False)
        self.adv_toggle_btn.clicked.connect(self._toggle_advanced)

        self.adv_panel = QGroupBox()
        adv_outer = QVBoxLayout(self.adv_panel)
        adv_outer.setSpacing(10)
        self.adv_panel.setVisible(False)

        # Filter row (dropdown)
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Both", "Images", "Videos"])
        filter_row.addWidget(self.filter_combo, 1)

        # Network & timing form
        net_box = QGroupBox("Network & Timing")
        form = QFormLayout(net_box)
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 10)
        self.retries_spin.setValue(3)
        self.retries_spin.setToolTip("--retries")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setToolTip("--http-timeout (seconds)")
        self.sleep_spin = QSpinBox()
        self.sleep_spin.setRange(0, 10)
        self.sleep_spin.setValue(1)
        self.sleep_spin.setToolTip("--sleep-request (seconds between requests)")
        form.addRow("Retries:", self.retries_spin)
        form.addRow("HTTP timeout (s):", self.timeout_spin)
        form.addRow("Sleep (s):", self.sleep_spin)

        adv_outer.addLayout(filter_row)
        adv_outer.addWidget(net_box)

        # URLs + Log
        urls_label = QLabel("URLs")
        urls_label.setObjectName("sectionLabel")
        self.urls = QPlainTextEdit()
        self.urls.setObjectName("urlsEdit")
        self.urls.setPlaceholderText("Paste one URL per line. Tip: drag-and-drop .txt files or text here.")

        log_label = QLabel("Log")
        log_label.setObjectName("sectionLabel")
        self.log = QTextEdit()
        self.log.setObjectName("logView")
        self.log.setReadOnly(True)
        self.log.document().setMaximumBlockCount(10000)  # keep UI snappy on long runs

        # Assemble
        root.addLayout(header)
        root.addWidget(info)
        root.addLayout(toolbar)
        root.addLayout(summary)
        root.addWidget(settings)
        s_layout.addLayout(ua_row)
        s_layout.addLayout(ck_row)
        s_layout.addLayout(out_row)
        s_layout.addWidget(self.adv_toggle_btn, alignment=Qt.AlignLeft)
        s_layout.addWidget(self.adv_panel)
        root.addWidget(urls_label)
        root.addWidget(self.urls, 3)
        root.addWidget(log_label)
        root.addWidget(self.log, 3)

    # ---------- Utilities ----------
    def _toggle_advanced(self):
        expanded = self.adv_toggle_btn.isChecked()
        self.adv_panel.setVisible(expanded)
        self.adv_toggle_btn.setText("Advanced ▾" if expanded else "Advanced ▸")

    def _log(self, msg: str):
        self.log.append(msg)

    def clear_log(self):
        self.log.clear()

    def bin_present(self) -> bool:
        return self.bin_path.exists()

    def show_version_if_present(self):
        if self.bin_present():
            self._run_once(["--version"], capture_only=True)
        else:
            self.version_line.setText("Not installed")

    def _update_summary_labels(self, done: int, total: int):
        self.sum_downloaded.setText(f"✅ Downloaded: {self._totals['downloaded']}")
        self.sum_skipped.setText(f"⚠️ Skipped: {self._totals['skipped']}")
        self.sum_failed.setText(f"❌ Failed: {self._totals['failed']}")
        self.sum_progress.setText(f"▶️ {done} / {total}")

    # ---------- Settings persist ----------
    def _save_settings(self):
        s = self.settings
        s.setValue("ua_use_browser", self.ua_use_browser.isChecked())
        s.setValue("ua_edit", self.ua_edit.text())
        s.setValue("cookies", self.cookies_file_edit.text())
        s.setValue("outdir", self.output_dir_edit.text())
        s.setValue("filter_combo", self.filter_combo.currentText())
        s.setValue("retries", self.retries_spin.value())
        s.setValue("timeout", self.timeout_spin.value())
        s.setValue("sleep", self.sleep_spin.value())
        s.setValue("adv_open", self.adv_panel.isVisible())
        s.setValue("geom", self.saveGeometry())
        s.setValue("last_update_check_ts", self._last_update_check)

    def _load_settings(self):
        s = self.settings
        self.ua_use_browser.setChecked(s.value("ua_use_browser", True, bool))
        self.ua_edit.setText(s.value("ua_edit", ""))
        self.ua_edit.setEnabled(not self.ua_use_browser.isChecked())
        self.cookies_file_edit.setText(s.value("cookies", ""))
        self.output_dir_edit.setText(s.value("outdir", ""))
        val = s.value("filter_combo", "Both")
        idx = max(0, ["Both","Images","Videos"].index(val) if val in ["Both","Images","Videos"] else 0)
        self.filter_combo.setCurrentIndex(idx)
        self.retries_spin.setValue(int(s.value("retries", 3)))
        self.timeout_spin.setValue(int(s.value("timeout", 30)))
        self.sleep_spin.setValue(int(s.value("sleep", 1)))
        adv_open = s.value("adv_open", False, bool)
        self.adv_toggle_btn.setChecked(adv_open)
        self._toggle_advanced()
        g = s.value("geom")
        if g:
            self.restoreGeometry(g)
        self._update_summary_labels(0, 0)

    def closeEvent(self, e):
        self._save_settings()
        super().closeEvent(e)

    # ---------- Update logic ----------
    def maybe_check_update(self, force=False):
        now = time.time()
        # 6-hour throttle; persisted across runs
        if not force and (now - self._last_update_check) < 6 * 3600:
            return
        self._last_update_check = now
        self.settings.setValue("last_update_check_ts", self._last_update_check)

        local = get_local_version(self.bin_path)
        latest = get_latest_version_tag()
        if latest is None:
            self._log("Update check: could not reach GitHub (offline or rate-limited). Will try again later.")
            return

        if latest and local and is_newer(local, latest):
            btn = QMessageBox.question(
                self, "Update available",
                f"gallery-dl {local} is installed.\nA newer version {latest} is available.\n\nUpdate now?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if btn == QMessageBox.Yes:
                self.fetch_binary()
        elif latest and not local and self.bin_present():
            btn = QMessageBox.question(
                self, "Update check",
                f"A gallery-dl build is present but version is unknown.\nLatest upstream is {latest}.\n\nRedownload?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if btn == QMessageBox.Yes:
                self.fetch_binary()
        else:
            if local:
                self._log(f"gallery-dl {local} is up to date (latest: {latest}).")
            else:
                self._log(f"Latest gallery-dl upstream: {latest}")

    # ---------- Fetch / Update ----------
    def fetch_binary(self):
        latest = get_latest_version_tag()
        local = get_local_version(self.bin_path) if self.bin_present() else None
        if self.bin_present() and latest and local and not is_newer(local, latest):
            self._log(f"Binary already up to date (gallery-dl {local}). Skipping download.")
            self.version_line.setText(f"gallery-dl {local}")
            return

        dest_dir = app_bin_dir()
        dest_dir.mkdir(parents=True, exist_ok=True)

        ok = False
        err_msgs = []
        for url, fname in detect_asset_candidates():
            self._log(f"Trying: {url}")
            try:
                dest = dest_dir / fname
                download_file(url, dest, expected_sha256=None, timeout=25)
                make_executable(dest)
                self._log(f"Saved: {dest}")
                self.bin_path = dest
                ok = True
                break
            except Exception as e:
                msg = f"Download failed from {url}: {e}"
                err_msgs.append(msg)
                self._log(msg)

        if not ok:
            QMessageBox.critical(self, "Download failed", "Could not fetch gallery-dl.\n\n" + "\n".join(err_msgs))
        else:
            self._log("Fetch complete.")
            if platform.system().lower() == "darwin":
                self._log("macOS: If you see a quarantine warning, open Terminal and run:\n"
                          "xattr -d com.apple.quarantine \"{bin}\"\nThen re-run.".format(bin=str(self.bin_path)))
            self.show_version_if_present()

    def _run_once(self, args, capture_only=False):
        if not self.bin_present():
            return ""
        p = QProcess(self)
        p.setProgram(str(self.bin_path))
        p.setArguments(args)
        p.setProcessChannelMode(QProcess.MergedChannels)
        captured = []

        def _cap():
            captured.append(p.readAllStandardOutput().data().decode(errors="replace"))

        p.readyReadStandardOutput.connect(_cap)
        p.finished.connect(lambda: None)
        p.start()
        p.waitForFinished(20000)
        out = "".join(captured).strip()
        if "--version" in args and out:
            self.version_line.setText(out)
            self._log(out)
        return out

    # ---------- URL Handling ----------
    def _clean_urls(self, text: str) -> list[str]:
        lines = [ln.strip() for ln in text.splitlines()]
        out = []
        skipped = 0
        for ln in lines:
            if not ln:
                continue
            if ln.startswith("<") and ln.endswith(">"):
                ln = ln[1:-1].strip()
            p = urlparse(ln)
            if p.scheme in ("http", "https") and p.netloc:
                out.append(ln)
            else:
                skipped += 1
        if skipped:
            self._log(f"Skipped {skipped} non-URL line(s).")
        return out

    def load_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a .txt with URLs", "", "Text files (*.txt);;All files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                new_lines = [ln.strip() for ln in f.readlines()]
            existing = [ln.strip() for ln in self.urls.toPlainText().splitlines() if ln.strip()]
            merged = existing + [ln for ln in new_lines if ln and ln not in existing]
            self.urls.setPlainText("\n".join(merged))
            self._log(f"Loaded {len(new_lines)} URL(s) from {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file:\n{e}")

    # Drag & drop support
    def dragEnterEvent(self, e):
        md = e.mimeData()
        if md.hasUrls() or md.hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        md = e.mimeData()
        added = []
        for u in md.urls():
            try:
                if u.isLocalFile():
                    p = u.toLocalFile()
                    if p.lower().endswith(".txt"):
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            added += [ln.strip() for ln in f if ln.strip()]
            except Exception as ex:
                self._log(f"Failed to read dropped file: {ex}")
        if md.hasText():
            added += [ln.strip() for ln in md.text().splitlines() if ln.strip()]
        if added:
            existing = [ln.strip() for ln in self.urls.toPlainText().splitlines() if ln.strip()]
            dedup = existing + [ln for ln in added if ln not in existing]
            self.urls.setPlainText("\n".join(dedup))
            self._log(f"Added {len(added)} URL(s) via drag-and-drop.")

    # ---------- Cookies helpers ----------
    def pick_cookies_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose cookies file", "", "Cookies (*.txt *.cookies *.json);;All files (*)"
        )
        if path:
            self.cookies_file_edit.setText(path)

    def delete_selected_cookies_file(self):
        path = self.cookies_file_edit.text().strip()
        if not path:
            QMessageBox.information(self, "No file selected", "Select a cookies file to delete.")
            return
        p = Path(path)
        if not p.exists():
            QMessageBox.information(self, "Not found", "Selected cookies file does not exist.")
            return
        btn = QMessageBox.question(
            self, "Delete cookies file?",
            f"Delete this file?\n\n{p}\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if btn != QMessageBox.Yes:
            return
        try:
            p.unlink()
            self.cookies_file_edit.clear()
            self._log(f"Deleted cookies file: {p}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete file:\n{e}")

    def pick_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Choose parent folder", os.getcwd())
        if path:
            new_path = Path(path) / "gallery-dl"
            self.output_dir_edit.setText(str(new_path))

    # ---------- Build args ----------
    def _build_common_args(self):
        args = []

        # User-Agent
        if self.ua_use_browser.isChecked():
            args += ["--user-agent", "browser"]
        else:
            ua = self.ua_edit.text().strip()
            if not ua:
                QMessageBox.warning(self, "Custom UA empty",
                                    "You unchecked 'Use system browser UA' but didn't enter a custom UA.\n"
                                    "Re-enabling default UA for this run.")
                self.ua_use_browser.setChecked(True)
                args += ["--user-agent", "browser"]
            else:
                args += ["--user-agent", ua]

        # Cookies
        cookies_file = self.cookies_file_edit.text().strip()
        if cookies_file:
            args += ["--cookies", cookies_file]

        # Output directory
        out_dir = self.output_dir_edit.text().strip()
        if not out_dir:
            out_dir = str(user_downloads_dir() / "gallery-dl")
        args += ["-d", out_dir]

        # Filter (dropdown)
        flt = self.filter_combo.currentText()
        if flt == "Images":
            args += ["--filter", "extension in ('jpg','jpeg','png')"]
        elif flt == "Videos":
            args += ["--filter", "extension in ('mp4','webm')"]

        # Network & timing
        retries = self.retries_spin.value()
        if retries:
            args += ["--retries", str(retries)]
        timeout = self.timeout_spin.value()
        if timeout:
            args += ["--http-timeout", str(timeout)]
        sleep = self.sleep_spin.value()
        if sleep:
            args += ["--sleep-request", str(sleep)]

        return args

    # ---------- Run / Stop ----------
    def start_run(self):
        if not self.bin_present():
            QMessageBox.warning(self, "Binary missing", "Please click “Fetch / Update” first.")
            return

        self.maybe_check_update()

        urls_raw = self._clean_urls(self.urls.toPlainText())
        if not urls_raw:
            QMessageBox.information(self, "No URLs",
                "Add at least one http(s) URL (one per line), or drag a .txt list into the box.")
            return

        # de-duplicate while preserving order
        seen = set()
        urls = []
        for u in urls_raw:
            if u not in seen:
                urls.append(u)
                seen.add(u)
        if len(urls) != len(urls_raw):
            self._log(f"Removed {len(urls_raw) - len(urls)} duplicate URL(s).")

        if self.proc and self.proc.state() != QProcess.NotRunning:
            QMessageBox.information(self, "Running", "A job is already running.")
            return

        self.queue = urls
        self._totals = {"downloaded": 0, "skipped": 0, "failed": 0}
        self._seen_paths.clear()
        self._error_lines = 0
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Build safe batches to avoid Windows 32k command line limit
        self._batches = self._build_batches(urls, base_args_len=len(" ".join(self._build_common_args())))
        self._batch_index = -1

        # show 0/N immediately
        self._update_summary_labels(0, len(self.queue))

        self._log(f"Queued {len(self.queue)} URL(s) in {len(self._batches)} batch(es).")
        self._run_next_batch()

    def _build_batches(self, urls: list[str], base_args_len: int, max_cmd_len: int = 30000) -> list[list[str]]:
        batches = []
        cur = []
        cur_len = base_args_len
        for u in urls:
            add = len(u) + 1  # space
            if cur and (cur_len + add) > max_cmd_len:
                batches.append(cur)
                cur = [u]
                cur_len = base_args_len + len(u)
            else:
                cur.append(u)
                cur_len += add
        if cur:
            batches.append(cur)
        return batches

    def _run_next_batch(self):
        self._batch_index += 1
        total_batches = len(self._batches)
        if self._batch_index >= total_batches:
            self._log("All done.")
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self._update_summary_labels(len(self.queue), len(self.queue))
            return

        # prepare batch
        self._batch_urls = self._batches[self._batch_index]
        self._batch_started_at = time.time()
        self._seen_paths.clear()
        self._error_lines = 0

        # launch single process with [URLs...]
        args = self._build_common_args() + self._batch_urls
        self.proc = QProcess(self)
        self.proc.setProgram(str(self.bin_path))
        self.proc.setArguments(args)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read_output)
        self.proc.finished.connect(self._finished_batch)
        self._log(f"=== Batch {self._batch_index+1}/{total_batches} — {len(self._batch_urls)} URL(s) ===")
        self.proc.start()

    def stop_run(self):
        if self.proc and self.proc.state() != QProcess.NotRunning:
            self.proc.terminate()
            if not self.proc.waitForFinished(1500):
                self.proc.kill()
            self._log("Stopped by user.")
        self.queue = []
        self._batches = []
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._update_summary_labels(0, 0)

    def _read_output(self):
        if not self.proc:
            return
        data = self.proc.readAllStandardOutput().data().decode(errors="replace")
        if not data:
            return

        at_end = self.log.verticalScrollBar().value() == self.log.verticalScrollBar().maximum()
        self._log(data.rstrip("\n"))
        if at_end:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

        # --- Live classification ---
        file_re = re.compile(r"""
            (?:[A-Za-z]:\\[^:*?"<>|\r\n]+|/[^:*?"<>|\r\n]+)
            \.(?:jpe?g|png|gif|webp|mp4|webm|mkv|mov|avi)\b
        """, re.IGNORECASE | re.VERBOSE)

        for raw in data.splitlines():
            line = raw.strip()
            low = line.lower()

            # Count likely errors live
            if ("error:" in low) or ("http error" in low) or ("forbidden" in low) or ("not found" in low):
                self._error_lines += 1
                self._totals["failed"] += 1
                done_urls = sum(len(b) for b in self._batches[: self._batch_index])  # finished batches so far
                self._update_summary_labels(done_urls, len(self.queue))
                continue

            # Printed path -> downloaded or skipped (based on mtime vs batch start)
            m = file_re.search(line)
            if not m:
                continue
            path = m.group(0)
            if path in self._seen_paths:
                continue
            self._seen_paths.add(path)

            try:
                st = os.stat(path)
                if st.st_mtime < (self._batch_started_at + 0.5):
                    self._totals["skipped"] += 1
                else:
                    self._totals["downloaded"] += 1
            except FileNotFoundError:
                # Assume downloaded; if not, it won't get double-counted later anyway
                self._totals["downloaded"] += 1
            except Exception:
                self._totals["skipped"] += 1

            done_urls = sum(len(b) for b in self._batches[: self._batch_index])
            self._update_summary_labels(done_urls, len(self.queue))

    def _finished_batch(self):
        code = self.proc.exitCode() if self.proc else 0
        if code != 0:
            self._totals["failed"] += 1
            self._log(f"❌ Batch failed (exit code {code})")

        # mark progress by URL count in this batch
        done_urls = sum(len(b) for b in self._batches[: self._batch_index + 1])
        self._update_summary_labels(done_urls, len(self.queue))

        # reset for next batch
        self.proc = None
        self._seen_paths.clear()
        self._error_lines = 0

        self._log(f"✅ Batch {self._batch_index+1} done — totals: "
                  f"downloaded={self._totals['downloaded']} • skipped={self._totals['skipped']} • failed={self._totals['failed']}")
        self._run_next_batch()

    # ---------- Test URL (dry run) ----------
    def test_url(self):
        sel = self.urls.textCursor().selectedText().strip()
        candidate = sel or next((ln for ln in self.urls.toPlainText().splitlines() if ln.strip()), "")
        if not candidate:
            QMessageBox.information(self, "No URL", "Select or enter a URL to test.")
            return
        urls = self._clean_urls(candidate)
        if not urls:
            QMessageBox.information(self, "Invalid URL", "Please select a valid http(s) URL.")
            return
        self._log(f"Testing (dry-run) → {urls[0]}\n(Dry run only — no files will be saved.)")
        out = self._run_once(self._build_common_args() + ["-g", urls[0]], capture_only=True)
        self._log(out or "No output (site may need cookies/login or URL is not supported).")

    # ---------- Shortcuts ----------
    def _install_shortcuts(self):
        for seq in ("Ctrl+R", "Meta+R"):
            QShortcut(QKeySequence(seq), self).activated.connect(self.start_run)
        for seq in ("Ctrl+O", "Meta+O"):
            QShortcut(QKeySequence(seq), self).activated.connect(self.load_txt)
        for seq in ("Ctrl+L", "Meta+L"):
            QShortcut(QKeySequence(seq), self).activated.connect(self.clear_log)

# -------------------------
# Entry
# -------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_styles(app)
    w = Navillera()

    # Set window + taskbar icon
    icon_path = Path(__file__).parent / "navillera.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        w.setWindowIcon(QIcon(str(icon_path)))

    w.show()
    sys.exit(app.exec())
