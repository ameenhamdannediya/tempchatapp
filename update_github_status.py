#!/usr/bin/env python3
"""
Usage:
  python update_github_status.py <GITHUB_TOKEN> "<PUBLIC_URL>" "<MESSAGE>"

This script edits the README.md in the repo archlinuxwithniri/tempchatapp
and adds or updates a single line like:

🚀 **Live Site:** [https://example.trycloudflare.com] (🟢 Online)

When stopped, it removes that line but keeps the rest of the README intact.
"""

import sys, os, subprocess, re

# -------- CONFIG --------
REPO_OWNER = "archlinuxwithniri"
REPO_NAME = "tempchatapp"
LOCAL_DIR = "/content/tempchatapp_repo"
# ------------------------

def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ensure_repo(token):
    repo_url = f"https://{REPO_OWNER}:{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    if not os.path.exists(LOCAL_DIR):
        run(["git", "clone", "--depth", "1", repo_url, LOCAL_DIR])
    else:
        run(["git", "remote", "set-url", "origin", repo_url], cwd=LOCAL_DIR)
        run(["git", "fetch", "origin", "--depth", "1"], cwd=LOCAL_DIR)
        run(["git", "reset", "--hard", "origin/main"], cwd=LOCAL_DIR)
    return LOCAL_DIR

def update_readme(token, url, msg):
    repo_dir = ensure_repo(token)
    readme_path = os.path.join(repo_dir, "README.md")

    # Read current content (create if missing)
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    # Remove old live line
    content = re.sub(r"^🚀 \*\*Live Site:\*\*.*$\n?", "", content, flags=re.MULTILINE)

    if url.strip():
        new_line = f"🚀 **Live Site:** [{url}] ({msg})\n"
        content = new_line + content  # add on top

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    run(["git", "add", "README.md"], cwd=repo_dir)
    run(["git", "commit", "-m", f"Update live link: {msg}"], cwd=repo_dir)
    run(["git", "push", "origin", "HEAD:main"], cwd=repo_dir)
    print("✅ README updated successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python update_github_status.py <TOKEN> <URL> <MESSAGE>")
        sys.exit(1)

    token, url, msg = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        update_readme(token, url, msg)
    except Exception as e:
        print("❌ Error:", e)
