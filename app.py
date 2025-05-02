import os
from flask import Flask, jsonify
import requests
import base64
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Render!"

@app.route('/scrape')
def scrape():
    try:
        jobs = fetch_engineering_jobs()
        content = format_jobs_to_markdown(jobs)
        push_to_github(content)
        return jsonify({"status": "success", "jobs_found": len(jobs)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# === Scraper ===
def fetch_engineering_jobs():
    url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"

    headers = {
        "Accept": "application/json,application/xml",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
        "Origin": "https://nvidia.wd5.myworkdayjobs.com"
    }

    payload = {
        "appliedFacets": {},
        "limit": 100,
        "offset": 0,
        "searchText": ""
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    jobs = []
    for job in data.get("jobPostings", []):
        title = job.get("title", "")
        if "engineer" in title.lower():  # Filter by keyword
            location = job.get("locationsText", "N/A")
            link = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite" + job["externalPath"]
            jobs.append(f"- **{title}** ({location})\n  {link}")

    return jobs


def format_jobs_to_markdown(jobs):
    header = f"# NVIDIA Engineering Jobs\n\nUpdated: {datetime.now().isoformat()}\n\n"
    return header + "\n\n".join(jobs)

# === GitHub Push ===
def push_to_github(content):
    GITHUB_TOKEN = os.environ.get("GITHUB_PAT")  # safer than hardcoding
    REPO_OWNER = "MarwanAliii"
    REPO_NAME = "Obsidian-note-sync"
    FILE_PATH = "nvidia_jobs.md"
    BRANCH = "main"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    
    # Check for existing file to get SHA
    sha = None
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        sha = resp.json().get("sha")
    
    data = {
        "message": f"Update NVIDIA job list - {datetime.now().isoformat()}",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha
    
    put_resp = requests.put(url, headers=headers, json=data)
    put_resp.raise_for_status()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
