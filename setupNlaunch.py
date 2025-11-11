# --- setupNlaunch.py ---
# Run this in Colab:  !python setupNlaunch.py
# Make sure: .token.zip exists in your GitHub repo (with token.txt inside)

import os, subprocess, shlex, time, re, requests, threading, pyzipper
from flask import Flask, Response, request
from getpass import getpass

# ----------------------------
# 1️⃣ Download & decrypt .token.zip
# ----------------------------
ZIP_URL = "https://github.com/archlinuxwithniri/tempchatapp/raw/main/.token.zip"
ZIP_PATH = "/content/.token.zip"
TOKEN_TXT = "/content/token.txt"

print("⬇️ Downloading encrypted .token.zip ...")
r = requests.get(ZIP_URL)
if r.status_code != 200:
    raise SystemExit(f"❌ Failed to download zip file: HTTP {r.status_code}")
with open(ZIP_PATH, "wb") as f:
    f.write(r.content)
print("✅ Download complete.")

password = getpass("🔑 Enter password to decrypt .token.zip: ")

def try_extract(zip_class, pwd):
    try:
        with zip_class(ZIP_PATH) as zf:
            zf.pwd = pwd.encode('utf-8')
            zf.extractall("/content")
        return True
    except Exception:
        return False

ok = try_extract(pyzipper.AESZipFile, password) or try_extract(pyzipper.ZipFile, password)
if not ok:
    raise SystemExit("❌ Wrong password or unsupported ZIP encryption format.")

if not os.path.exists(TOKEN_TXT):
    raise SystemExit("❌ token.txt not found after extraction!")

with open(TOKEN_TXT, "r", encoding="utf-8") as f:
    GITHUB_TOKEN = f.read().strip()

os.remove(TOKEN_TXT)
os.remove(ZIP_PATH)
print("🔐 Token successfully loaded and ready to use!")

# ----------------------------
# 2️⃣ Setup Flask Chat + Tunnel
# ----------------------------
!pip install flask cloudflared requests -q

USERNAME = "archlinuxwithniri"
EMAIL = "archlinuxwithniri@gmail.com"
REPO_NAME = "tempchatapp"
UPDATE_SCRIPT_PATH = "/content/update_github_status.py"
RAW_PY_URL = f"https://raw.githubusercontent.com/{USERNAME}/{REPO_NAME}/main/update_github_status.py"
GITHUB_HTML = f"https://raw.githubusercontent.com/{USERNAME}/{REPO_NAME}/main/index.html"
CHAT_FILE = "chat.txt"
PORT = 8000

# --- Download update script ---
print("📥 Downloading update_github_status.py...")
try:
    r = requests.get(RAW_PY_URL, timeout=10)
    r.raise_for_status()
    with open(UPDATE_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(r.text)
    print("✅ update_github_status.py downloaded.")
except Exception as e:
    print("❌ Failed to download update script:", e)

# --- Flask app setup ---
app = Flask(__name__)

@app.route("/")
def index():
    try:
        html = requests.get(GITHUB_HTML, timeout=5).text
    except Exception as e:
        html = f"<h3>Failed to fetch HTML: {e}</h3>"
    return Response(html, mimetype="text/html")

@app.route("/post", methods=["POST"])
def post():
    msg = request.get_json(force=True).get("msg", "").strip()
    if msg:
        with open(CHAT_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    return {"status": "ok"}

@app.route("/messages")
def messages():
    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="text/plain")
    except FileNotFoundError:
        return Response("", mimetype="text/plain")

def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()
time.sleep(2)

# --- Start Cloudflared ---
print("🚀 Starting Cloudflared tunnel...")
logfile = "/content/cloudflared.log"
cmd = f"/usr/local/bin/cloudflared tunnel --url http://localhost:{PORT} --no-autoupdate"
proc = subprocess.Popen(shlex.split(cmd), stdout=open(logfile, "w"), stderr=subprocess.STDOUT)

def find_public_url(timeout=30):
    for _ in range(timeout):
        time.sleep(1)
        if not os.path.exists(logfile):
            continue
        txt = open(logfile, "r", encoding="utf-8", errors="ignore").read()
        match = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", txt)
        if match:
            return match.group(0)
    return None

# --- Wait for tunnel URL ---
url = find_public_url()
if not url:
    print("⚠️ Could not find public URL. Check /content/cloudflared.log")
else:
    print(f"🌍 Public URL: {url}")

    # Mark online
    if GITHUB_TOKEN:
        print("🔵 Updating README to Online...")
        subprocess.run([
            "python", UPDATE_SCRIPT_PATH,
            GITHUB_TOKEN, USERNAME, EMAIL, REPO_NAME, url, "true"
        ], check=False)
        print("✅ README updated: Online.")
    else:
        print("⚠️ Missing token, skipping online update.")

print("⏳ Tunnel active. Keep this cell running. Stop to end session.")

# --- When stopped ---
try:
    proc.wait()
except KeyboardInterrupt:
    print("\n🟥 Interrupted by user.")
finally:
    try:
        if GITHUB_TOKEN:
            print("🔴 Updating README to Offline...")
            subprocess.run([
                "python", UPDATE_SCRIPT_PATH,
                GITHUB_TOKEN, USERNAME, EMAIL, REPO_NAME, "none", "false"
            ], check=False)
            print("✅ README updated: Offline.")
    except Exception as e:
        print("❌ Failed to update README to Offline:", e)

    try:
        proc.kill()
    except Exception:
        pass

print("🏁 Session ended.")
