import os
import subprocess
import re

# ---------- Function 1: Clone or pull the repo ----------
def clone_repo(token, username, repo_name):
    repo_dir = f"/content/{repo_name}_repo"
    repo_url = f"https://{token}@github.com/{username}/{repo_name}.git"

    if not os.path.exists(repo_dir):
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
    else:
        subprocess.run(["git", "-C", repo_dir, "pull"], check=True)

    return repo_dir


# ---------- Function 2: Edit the README ----------
def edit_readme(repo_dir, url, online=True):
    readme_path = os.path.join(repo_dir, "README.md")

    if not os.path.exists(readme_path):
        print("No README.md found, creating a new one.")
        open(readme_path, "w").close()

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove previous online/offline status lines
    content = re.sub(r"🟢.*|🔴.*", "", content).strip()

    # Append new status line
    if online:
        status_line = f"\n\n🟢 Currently Online — {url}\n"
    else:
        status_line = f"\n\n🔴 Currently Offline\n"

    content += status_line

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------- Function 3: Commit and push ----------
def push_changes(repo_dir, username, email, message="Update live status"):
    subprocess.run(["git", "-C", repo_dir, "config", "user.name", username], check=True)
    subprocess.run(["git", "-C", repo_dir, "config", "user.email", email], check=True)

    subprocess.run(["git", "-C", repo_dir, "add", "."], check=True)

    # Try committing; skip if nothing changed
    commit = subprocess.run(
        ["git", "-C", repo_dir, "commit", "-m", message],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if "nothing to commit" in commit.stderr.lower():
        print("No changes to commit.")
        return

    subprocess.run(["git", "-C", repo_dir, "push"], check=True)
    print("✅ Changes pushed successfully.")


# ---------- Function 4: Full pipeline ----------
def update_github_status(token, username, email, repo_name, url, online=True):
    repo_dir = clone_repo(token, username, repo_name)
    edit_readme(repo_dir, url, online)
    push_changes(repo_dir, username, email,
                 message="Update live status: " + ("Online" if online else "Offline"))


# ---------- CLI Entry Point ----------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 7:
        print("Usage: python update_github_status.py <token> <username> <email> <repo_name> <url> <online>")
        sys.exit(1)

    token, username, email, repo_name, url, online_flag = sys.argv[1:7]
    online = online_flag.lower() in ["1", "true", "yes", "online"]

    update_github_status(token, username, email, repo_name, url, online)
