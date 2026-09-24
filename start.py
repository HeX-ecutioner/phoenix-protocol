#!/usr/bin/env python3
"""Phoenix Protocol — Cross-Platform Developer & Demo Launcher.

Starts the Flask backend and Vite frontend services in parallel,
monitors readiness endpoints, prints clear URLs, and manages clean
child-process termination on shutdown.

Automatically detects port conflicts (e.g. if an older server is already
running on 5173 or 5001) and selects a fresh, available port so services
never collide with pre-existing applications.

Usage:
    python start.py [--no-browser] [--port-backend 5001] [--port-frontend 5173]
"""

import argparse
import atexit
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from typing import Optional
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


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is in use or actively listening."""
    # 1. Connect test (is any server actively listening and accepting connections?)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            if s.connect_ex((host, port)) == 0:
                return True
    except OSError:
        pass

    # 2. Bind test (can we bind without error?)
    for bind_host in [host, "0.0.0.0"]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((bind_host, port))
        except OSError:
            return True

    return False


def find_available_port(preferred_port: int, max_attempts: int = 100, host: str = "127.0.0.1") -> int:
    """Find the first available free port starting from preferred_port."""
    for port in range(preferred_port, preferred_port + max_attempts):
        if not is_port_in_use(port, host):
            return port
    raise RuntimeError(
        f"Could not find an available free port in range {preferred_port}-{preferred_port + max_attempts}"
    )


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


def terminate_process(proc: Optional[subprocess.Popen], is_windows: bool = False) -> None:
    """Safely terminate a child process and its process tree."""
    if proc is None or proc.poll() is not None:
        return

    try:
        if is_windows:
            # On Windows, taskkill /F /T kills the entire process tree
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
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
        default=5001,
        help="Port for the Flask API backend (default: 5001).",
    )
    parser.add_argument(
        "--port-frontend",
        type=int,
        default=5173,
        help="Port for the Vite frontend (default: 5173).",
    )
    parser.add_argument(
        "--strict-ports",
        action="store_true",
        help="Exit immediately if requested ports are in use instead of allocating fresh ports.",
    )
    args = parser.parse_args()

    print("Phoenix Protocol")
    print("----------------")
    print("Verifying runtime prerequisites...")

    npm_path = check_prerequisites(BACKEND_DIR, FRONTEND_DIR)

    # ------------------------------------------------------------------------
    # Port Conflict Detection & Fresh Port Allocation
    # ------------------------------------------------------------------------
    backend_port = args.port_backend
    if is_port_in_use(backend_port):
        if args.strict_ports:
            print(f"[ERROR] Backend port {backend_port} is already in use.", file=sys.stderr)
            sys.exit(1)
        backend_port = find_available_port(backend_port + 1)
        print(
            f"[INFO] Backend port {args.port_backend} is already in use by another process. "
            f"Allocating fresh port: {backend_port}."
        )

    frontend_port = args.port_frontend
    if is_port_in_use(frontend_port):
        if args.strict_ports:
            print(f"[ERROR] Frontend port {frontend_port} is already in use.", file=sys.stderr)
            sys.exit(1)
        frontend_port = find_available_port(frontend_port + 1)
        print(
            f"[INFO] Frontend port {args.port_frontend} is already in use by another application. "
            f"Allocating fresh port: {frontend_port} to prevent collision."
        )

    backend_url = f"http://localhost:{backend_port}"
    backend_health_url = f"http://127.0.0.1:{backend_port}/health"
    frontend_url = f"http://localhost:{frontend_port}"
    frontend_check_url = f"http://127.0.0.1:{frontend_port}/"

    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"
    # Allow CORS from chosen frontend origin as well as default local origins
    backend_env["CORS_ALLOWED_ORIGINS"] = (
        f"{frontend_url},http://127.0.0.1:{frontend_port},"
        f"http://localhost:5173,http://127.0.0.1:5173"
    )

    backend_cmd = [
        sys.executable,
        "-m",
        "flask",
        "--app",
        "app.api:create_app()",
        "run",
        "--port",
        str(backend_port),
        "--host",
        "0.0.0.0",
    ]

    frontend_env = os.environ.copy()
    frontend_env["VITE_API_BASE_URL"] = backend_url

    frontend_cmd = [
        npm_path,
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        str(frontend_port),
        "--strictPort",
    ]

    is_windows = sys.platform == "win32"

    backend_proc: Optional[subprocess.Popen] = None
    frontend_proc: Optional[subprocess.Popen] = None

    def cleanup_all():
        terminate_process(backend_proc, is_windows=is_windows)
        terminate_process(frontend_proc, is_windows=is_windows)

    atexit.register(cleanup_all)

    def handle_signal(sig, frame):
        print("\n[INFO] Shutdown signal received. Stopping Phoenix Protocol services...")
        cleanup_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        # Start Backend
        print(f"Starting backend on port {backend_port}...")
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(BACKEND_DIR),
            env=backend_env,
            start_new_session=(not is_windows),
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
        print(f"Starting frontend on port {frontend_port}...")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            env=frontend_env,
            shell=is_windows,
            start_new_session=(not is_windows),
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
        print(f"Phoenix Protocol is ready.")
        print(f"  Backend URL:  {backend_url}")
        print(f"  Frontend URL: {frontend_url}")
        print("Press Ctrl+C to stop all services.")

        if not args.no_browser:
            try:
                print(f"[INFO] Opening {frontend_url} in browser...")
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
