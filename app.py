import os
import base64
import asyncio
import requests
import threading
from datetime import datetime
from flask import Flask, jsonify
from webscraper import scrape_rivian, lne

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Render!"

@app.route('/scrape')
def scrape():
    def farm_job():
        rivian_url = "https://careers.rivian.com/careers-home/jobs"
        
        try:
            jobs = asyncio.run(lne(rivian_url, scrape_rivian))
            push_to_github(jobs)
            print(f"✅ Scrape complete. {len(jobs)} jobs pushed to GitHub.")
        except Exception as e:
            print(f"❌ Scrape failed: {e}")
    
    threading.Thread(target=farm_job).start()
    return jsonify({"status": "scrape started"})

        

# === GitHub Push ===
def push_to_github(content):
    GITHUB_TOKEN = os.environ.get("GITHUB_PAT")  # safer than hardcoding
    REPO_OWNER = "MarwanAliii"
    REPO_NAME = "Obsidian-note-sync"
    FILE_PATH = "rivian_jobs.md"
    BRANCH = "main"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    
    # Check for existing file to get SHA
    sha = None
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        sha = resp.json().get("sha")
    
    data = {
        "message": f"Updated Rivian job list - {datetime.now().isoformat()}",
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
