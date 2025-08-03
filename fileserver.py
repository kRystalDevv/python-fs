import os
import random
import socket
import subprocess
import signal
import sys
import atexit
from flask import Flask, send_from_directory, request, abort, render_template_string

# ---------- Port selection --------------------------------------------------
COMMON_PORTS = {
    20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 995,
    3306, 5432, 6379, 8080, 27017, 5000, 8000, 9000
}
PORT_RANGE = (15000, 30000)  # high, rarely‑used ports

def is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0

def pick_port() -> int:
    while True:
        p = random.randint(*PORT_RANGE)
        if p not in COMMON_PORTS and is_free(p):
            return p

PORT = pick_port()

# ---------- Directory setup --------------------------------------------------
FILES_DIR = os.path.join(os.getcwd(), "files")
os.makedirs(FILES_DIR, exist_ok=True)

# ---------- Blacklist handling ----------------------------------------------
BLACKLIST_FILE = "blacklist.txt"
if not os.path.exists(BLACKLIST_FILE):
    open(BLACKLIST_FILE, "a").close()  # create empty file

def load_blacklist() -> set[str]:
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_blacklist(ips: set[str]):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        for ip in sorted(ips):
            f.write(ip + "\n")

blacklist = load_blacklist()

# ---------- Flask app --------------------------------------------------------
app = Flask(__name__)
ACCESS_LOG = "access.log"


def log_access(ip: str, path: str):
    with open(ACCESS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{ip} | {path}\n")


@app.before_request
def block_blacklisted():
    ip = request.remote_addr
    if ip in blacklist and not request.path.startswith("/admin"):
        abort(403)


@app.after_request
def after(response):
    log_access(request.remote_addr, request.path)
    return response


@app.route("/")
def index():
    files = sorted(os.listdir(FILES_DIR))
    tpl = """
    <!doctype html>
    <html>
    <head>
        <meta charset=\"utf-8\">
        <title>File Share</title>
        <style>
            body{font-family:system-ui, sans-serif;max-width:600px;margin:2rem auto;padding:0 1rem;}
            a{color:#0366d6;text-decoration:none;}
            .file{margin:.5rem 0;}
            .file:hover a{text-decoration:underline;}
        </style>
    </head>
    <body>
        <h2>Available files</h2>
        {% if files %}
            {% for f in files %}
                <div class=\"file\"><a href=\"{{ url_for('download', filename=f) }}\">{{ f }}</a></div>
            {% endfor %}
        {% else %}
            <p><em>Drop files into the 'files' folder to share them.</em></p>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(tpl, files=files)


@app.route("/files/<path:filename>")
def download(filename):
    return send_from_directory(FILES_DIR, filename, as_attachment=True)


# --------------- Admin (localhost-only) -------------------------------------

def local_only():
    if request.remote_addr not in {"127.0.0.1", "::1"}:
        abort(403)


@app.route("/admin/logs")
def get_logs():
    local_only()
    return send_from_directory(".", ACCESS_LOG, as_attachment=True)


@app.route("/admin/blacklist")
def manage_blacklist():
    local_only()
    action = request.args.get("action", "add")
    ip = request.args.get("ip")
    global blacklist
    if ip:
        if action == "remove":
            blacklist.discard(ip)
        else:
            blacklist.add(ip)
        save_blacklist(blacklist)
    return {"blacklist": sorted(blacklist)}

# ---------- Cloudflare tunnel helper ----------------------------------------

def start_cloudflared(port: int) -> subprocess.Popen:
    """Start a quick tunnel and print the public URL when ready."""
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    def _cleanup():
        try:
            proc.terminate()
        except Exception:
            pass
    atexit.register(_cleanup)

    for line in proc.stdout:
        if "https://" in line and "trycloudflare.com" in line:
            print("\n[INFO] Public URL:", line.strip())
            break
    return proc

# ---------- Main ------------------------------------------------------------
if __name__ == "__main__":
    print(f"[INFO] Serving folder: {FILES_DIR}")
    print("[INFO] Access log:", os.path.abspath(ACCESS_LOG))
    print("[INFO]  Blacklist file:", os.path.abspath(BLACKLIST_FILE))
    print("[INFO]  Starting on a random port (not common)...")

    cf_proc = start_cloudflared(PORT)

    print(f"[INFO] Local:  http://127.0.0.1:{PORT}")
    print("(Press Ctrl+C to stop)")

    try:
        app.run(host="127.0.0.1", port=PORT, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        cf_proc.terminate()
        print("\n[INFO] Server stopped.")