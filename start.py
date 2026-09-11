#!/usr/bin/env python3
"""Phoenix Protocol — Cross-Platform Developer & Demo Launcher.

Starts the Flask backend and Vite frontend services in parallel,
monitors readiness endpoints, prints clear URLs, and manages clean
child-process termination on shutdown.

Usage:
    python start.py [--no-browser] [--port-backend 5000] [--port-frontend 5173]
"""

import argparse
import atexit
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def check_prerequisites(backend_dir: Path, frontend_dir: Path) -> str:
    """Verify that Python and Node/npm runtimes and dependencies exist."""
    # 1. Check Flask importability in current Python environment
    try:
        import flask  # noqa: F401
    except ImportError:
        print("[ERROR] Backend dependencies missing: Flask is not installed.", file=sys.stderr)
        print("Run the following command to install required backend packages:", file=sys.stderr)
        print(f"    {sys.executable} -m pip install -r backend/requirements.txt", file=sys.stderr)
        sys.exit(1)

    # 2. Check Node / npm executable
    npm_path = None
    if sys.platform == "win32":
        npm_path = shutil.which("npm.cmd") or shutil.which("npm")
    else:
        npm_path = shutil.which("npm")

    if not npm_path:
        print("[ERROR] Node.js package manager (npm) not found in PATH.", file=sys.stderr)
        print("Please install Node.js (https://nodejs.org/) to run the Phoenix Protocol frontend.", file=sys.stderr)
        sys.exit(1)

    # 3. Check frontend/node_modules
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("[ERROR] Frontend dependencies missing: 'frontend/node_modules' not found.", file=sys.stderr)
        print("Run the following command to install required frontend packages:", file=sys.stderr)
        print("    npm --prefix frontend install", file=sys.stderr)
        sys.exit(1)

    return npm_path


def wait_for_url(url: str, timeout_sec: float = 25.0, poll_interval: float = 0.4) -> bool:
    """Poll an HTTP URL until it returns a 2xx/3xx response or timeout expires."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "PhoenixProtocol-Launcher/1.0"},
            )
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if 200 <= response.status < 400:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionResetError, OSError):
            pass
        time.sleep(poll_interval)
    return False


def terminate_process(proc: subprocess.Popen) -> None:
    """Safely terminate a child process and its process tree."""
    if proc is None or proc.poll() is not None:
        return

    try:
        if sys.platform == "win32":
            # On Windows, taskkill /F /T kills the entire process tree (including npm sub-processes)
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Phoenix Protocol — Unified Cross-Platform Launcher"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Prevent automatic opening of the frontend in the default web browser.",
    )
    parser.add_argument(
        "--port-backend",
        type=int,
        default=5000,
        help="Port for the Flask API backend (default: 5000).",
    )
    parser.add_argument(
        "--port-frontend",
        type=int,
        default=5173,
        help="Port for the Vite frontend (default: 5173).",
    )
    args = parser.parse_args()

    print("Phoenix Protocol")
    print("----------------")
    print("Verifying runtime prerequisites...")

    npm_path = check_prerequisites(BACKEND_DIR, FRONTEND_DIR)

    backend_url = f"http://localhost:{args.port_backend}"
    backend_health_url = f"http://127.0.0.1:{args.port_backend}/health"
    frontend_url = f"http://localhost:{args.port_frontend}"
    frontend_check_url = f"http://127.0.0.1:{args.port_frontend}/"

    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"

    backend_cmd = [
        sys.executable,
        "-m",
        "flask",
        "--app",
        "app.api:create_app()",
        "run",
        "--port",
        str(args.port_backend),
        "--host",
        "127.0.0.1",
    ]

    frontend_cmd = [
        npm_path,
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port_frontend),
    ]

    # Use shell=True on Windows for npm execution if needed
    is_windows = sys.platform == "win32"

    backend_proc = None
    frontend_proc = None

    def cleanup_all():
        terminate_process(backend_proc)
        terminate_process(frontend_proc)

    atexit.register(cleanup_all)

    try:
        # Start Backend
        print(f"Starting backend on port {args.port_backend}...")
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(BACKEND_DIR),
            env=backend_env,
        )

        if not wait_for_url(backend_health_url, timeout_sec=15.0):
            if backend_proc.poll() is not None:
                print(
                    f"[ERROR] Backend failed to start (exit code {backend_proc.returncode}).",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[ERROR] Backend did not respond at {backend_health_url} within timeout.",
                    file=sys.stderr,
                )
            sys.exit(1)

        print(f"Backend ready:  {backend_url}")

        # Start Frontend
        print(f"Starting frontend on port {args.port_frontend}...")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            shell=is_windows,
        )

        if not wait_for_url(frontend_check_url, timeout_sec=20.0):
            if frontend_proc.poll() is not None:
                print(
                    f"[ERROR] Frontend failed to start (exit code {frontend_proc.returncode}).",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[ERROR] Frontend did not respond at {frontend_check_url} within timeout.",
                    file=sys.stderr,
                )
            sys.exit(1)

        print(f"Frontend ready: {frontend_url}")
        print()
        print("Phoenix Protocol is ready.")
        print("Press Ctrl+C to stop all services.")

        if not args.no_browser:
            try:
                webbrowser.open(frontend_url)
            except Exception:
                pass

        # Keep alive and forward signals
        while True:
            # If any process terminated prematurely, exit
            if backend_proc.poll() is not None:
                print(f"\n[INFO] Backend stopped (code {backend_proc.returncode}). Shutting down...")
                break
            if frontend_proc.poll() is not None:
                print(f"\n[INFO] Frontend stopped (code {frontend_proc.returncode}). Shutting down...")
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping Phoenix Protocol services...")
    finally:
        cleanup_all()
        print("[INFO] All services stopped.")


if __name__ == "__main__":
    main()
