#!/usr/bin/env python3
"""
Usage:
  python update_github_status.py <GITHUB_TOKEN> "<PUBLIC_URL>" "<MESSAGE>" "<GIT_NAME>" "<GIT_EMAIL>"

Example:
  python update_github_status.py ABC123 "https://dummy.trycloudflare.com" "🟢 Currently Online" "Ameen" "ameen@example.com"
"""

import sys, os, subprocess

REPO_OWNER = "archlinuxwithniri"
REPO_NAME = "tempchatapp"
LOCAL_DIR = "/content/tempchatapp_repo"

def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)

def ensure_repo(token):
    repo_url = f"https://{REPO_OWNER}:{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    if not os.path.exists(LOCAL_DIR):
        run(["git", "clone", "--depth", "1", repo_url, LOCAL_DIR])
    else:
        run(["git", "remote", "set-url", "origin", repo_url], cwd=LOCAL_DIR)
        run(["git", "fetch", "origin", "--depth", "1"], cwd=LOCAL_DIR)
        run(["git", "reset", "--hard", "origin/main"], cwd=LOCAL_DIR)
    return LOCAL_DIR

def push_updated_readme(token, url, msg, git_name, git_email):
    repo_dir = ensure_repo(token)
    readme_path = os.path.join(repo_dir, "README.md")

    # Copy local version into repo
    if os.path.exists("README.md"):
        run(["cp", "README.md", readme_path])

    # Set Git user identity (local only)
    run(["git", "config", "user.name", git_name], cwd=repo_dir)
    run(["git", "config", "user.email", git_email], cwd=repo_dir)

    # Commit and push
    run(["git", "add", "README.md"], cwd=repo_dir)
    run(["git", "commit", "-m", f"Update live status: {msg}"], cwd=repo_dir)
    run(["git", "push", "origin", "HEAD:main"], cwd=repo_dir)
    print("✅ README pushed successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python update_github_status.py <TOKEN> <URL> <MESSAGE> <GIT_NAME> <GIT_EMAIL>")
        sys.exit(1)

    token, url, msg, git_name, git_email = sys.argv[1:6]
    push_updated_readme(token, url, msg, git_name, git_email)
