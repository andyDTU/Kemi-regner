from __future__ import annotations

import time
import socket
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    app_file = project_root / "app.py"

    if not app_file.exists():
        print(f"Kunne ikke finde app-fil: {app_file}")
        return 1

    # Prefer localhost-only binding. Try requested port 8501, then fall back to next free ports.
    preferred_port = 8501

    def _port_is_free(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False

    port = None
    for p in range(preferred_port, preferred_port + 10):
        if _port_is_free(p):
            port = p
            break
    if port is None:
        print("No free port found in range 8501-8510.")
        return 1

    server_url = f"http://127.0.0.1:{port}"

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]

    try:
        print(f"Starting Streamlit on {server_url}")
        subprocess.Popen(command, cwd=project_root)

        for _ in range(50):
            try:
                with urllib.request.urlopen(server_url, timeout=1):
                    break
            except Exception:
                time.sleep(0.2)
        else:
            print(f"Streamlit did not become ready at {server_url}.")
            return 1

        webbrowser.open_new(server_url)
        return 0
    except KeyboardInterrupt:
        print("\nApp stoppet af bruger.")
        return 0
    except FileNotFoundError:
        print("Python/Streamlit kunne ikke startes. Tjek dit miljø.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
