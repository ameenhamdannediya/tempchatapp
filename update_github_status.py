#!/usr/bin/env python3
"""
Usage:
  python update_github_status.py <GITHUB_TOKEN> "<PUBLIC_URL>" "<MESSAGE>"

This script clones (or updates) the repo archlinuxwithniri/tempchatapp,
replaces or adds a "### Status:" line in README.md with the given message and URL,
commits and pushes using the provided token.
"""
import sys
import os
import subprocess
from datetime import datetime

# ----- Repo configuration (edit if you change repo) -----
REPO_OWNER = "archlinuxwithniri"
REPO_NAME = "tempchatapp"
# --------------------------------------------------------

def run(cmd, cwd=None):
    print("RUN:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)

def ensure_repo_cloned(token):
    repo_url = f"https://{REPO_OWNER}:{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    local_dir = "/content/tempchatapp_repo"
    if not os.path.exists(local_dir):
        print("Cloning repo...")
        run(["git", "clone", "--depth", "1", repo_url, local_dir])
    else:
        # update remote origin with tokened URL and pull
        try:
            run(["git", "remote", "set-url", "origin", repo_url], cwd=local_dir)
            run(["git", "fetch", "origin", "--depth", "1"], cwd=local_dir)
            run(["git", "reset", "--hard", "origin/main"], cwd=local_dir)
        except Exception as e:
            print("Warning updating existing repo:", e)
    return local_dir

def update_readme_file(local_dir, public_url, message):
    readme_path = os.path.join(local_dir, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_block = f"### Status: {message}\n\n🔗 **URL:** {public_url}\n🕒 Updated: {timestamp}\n\n"

    # Replace existing "### Status:" line (and its block) if present
    if "### Status:" in content:
        # remove current status block (everything from ### Status: to the next blank line after URL/timestamp)
        import re
        # replace the first header and following paragraph block
        content = re.sub(r"### Status:.*?(?:\n\s*\n|\Z)", status_block, content, flags=re.S)
    else:
        # prepend the status block
        content = status_block + content

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

def commit_and_push(local_dir, message):
    try:
        run(["git", "add", "README.md"], cwd=local_dir)
        run(["git", "commit", "-m", f"Update status: {message}"], cwd=local_dir)
        run(["git", "push", "origin", "HEAD:main"], cwd=local_dir)
        print("✅ Pushed README update.")
    except subprocess.CalledProcessError as e:
        print("Git push failed (maybe no changes or auth issue):", e)

def main():
    if len(sys.argv) < 4:
        print("Usage: python update_github_status.py <GITHUB_TOKEN> <PUBLIC_URL> <MESSAGE>")
        sys.exit(1)

    token = sys.argv[1].strip()
    public_url = sys.argv[2].strip()
    message = sys.argv[3].strip()

    if not token:
        print("Error: token is empty.")
        sys.exit(1)

    local_dir = ensure_repo_cloned(token)
    update_readme_file(local_dir, public_url, message)
    commit_and_push(local_dir, message)

if __name__ == "__main__":
    main()

