# 🌸 Navillera — A Modern GUI for [gallery-dl](https://github.com/mikf/gallery-dl)

Navillera is a lightweight **PySide6** desktop front-end for `gallery-dl`, the powerful media downloader.
Download images or videos from supported sites with ease — no terminal needed.

![Navillera Screenshot](docs/screenshot.png)

---

## ✨ Features

- 📦 **Auto-fetch / update** the latest `gallery-dl` binary from GitHub (Windows/macOS/Linux)
- 🍪 **Cookies picker + delete** (Netscape/Chrome/Firefox JSON formats)
- 🎛️ **Advanced (collapsible)**: media **Filter** (Images / Videos / Both), **Retries**, **HTTP timeout**, **Sleep**
- 📃 **Paste multiple URLs** or **load from `.txt`** (drag-and-drop supported)
- 🚀 **Batch mode**: runs many URLs in a single process (auto-splits to avoid Windows 32k cmd limit)

---

## 🧰 Requirements

- **Python 3.10+**
- **PySide6**

### Install (virtual environment — no global pip)

#### Windows (PowerShell)

```powershell
# From the project folder
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install PySide6
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install PySide6
```

_(Prefer isolation? You can also use `pipx run` or `uv` if you like.)_

---

## ▶️ Run

```bash
# In the virtual environment
python navillera.py
```

First run: click **Fetch / Update** to download the `gallery-dl` binary, then paste URLs and hit **Run**.

> **Output folder**: If none is chosen, Navillera defaults to `~/Downloads/gallery-dl` (auto-created).

---

## ⚙️ Settings Overview

- **User-Agent**
  - ✅ Default: `--user-agent browser`
  - ✏️ Uncheck to provide a custom UA
- **Cookies**
  - Pick a `.txt`/`.json` file; **Delete** removes it from disk
- **Advanced ▸**
  - **Filter**: Images → `extension in ('jpg','jpeg','png')`; Videos → `('mp4','webm')`; Both → no filter
  - **Retries**: `--retries`
  - **HTTP timeout (s)**: `--http-timeout`
  - **Sleep (s)**: `--sleep-request`

---

## ⌨️ Shortcuts

- **Ctrl/⌘ + R**: Run
- **Ctrl/⌘ + O**: Load `.txt`
- **Ctrl/⌘ + L**: Clear Log

---

## 🏗️ Build (optional)

### Windows (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name Navillera --icon navillera.ico navillera.py
```

### macOS

```bash
pip install pyinstaller
pyinstaller --windowed --onefile --name Navillera --icon navillera.ico navillera.py
```

> Put the fetched `gallery-dl` binary in a `bin/` folder next to the executable if you want to bundle it.

---

## 📜 License

This GUI is MIT-licensed. `gallery-dl` belongs to its respective authors.
