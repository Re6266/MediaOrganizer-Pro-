"""Start the local Streamlit app from the user's Windows desktop session."""
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "预览主页.py"),
         "--server.headless", "true", "--server.address", "127.0.0.1",
         "--server.port", str(port), "--browser.gatherUsageStats", "false"],
        cwd=str(ROOT), creationflags=flags,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            with urllib.request.urlopen(url + "/_stcore/health", timeout=0.5) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, "程序启动失败，请检查 Python 和项目依赖。", "MediaOrganizer Pro", 0x10)


if __name__ == "__main__":
    main()
