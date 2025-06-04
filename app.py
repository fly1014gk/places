import os
import json
import subprocess
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_FILE = os.path.join(BASE_DIR, "events.json")

# 環境変数からGitHubトークンとリポジトリURLを取得
GH_TOKEN = os.environ.get('GH_TOKEN')
REPO_URL = os.environ.get('REPO_URL')

def save_events(events):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    try:
        # コミット用のユーザー設定
        subprocess.run(["git", "config", "user.name", "fly1014gk"], check=True, cwd=BASE_DIR)
        subprocess.run(["git", "config", "user.email", "yt.fly.channel@gmail.com"], check=True, cwd=BASE_DIR)
        subprocess.run(["git", "add", EVENTS_FILE], check=True, cwd=BASE_DIR)
        subprocess.run(["git", "commit", "-m", "Update events.json"], check=True, cwd=BASE_DIR)
        if GH_TOKEN and REPO_URL:
            # mainブランチにpush
            url_with_token = REPO_URL.replace("https://", f"https://{GH_TOKEN}@")
            subprocess.run(["git", "push", url_with_token, "main"], check=True, cwd=BASE_DIR)
        else:
            print("GH_TOKENまたはREPO_URLが未設定です")
    except subprocess.CalledProcessError as e:
        print(f"Git push failed: {e}")

def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events', methods=['GET'])
def api_get_events():
    return jsonify(load_events())

@app.route('/api/events', methods=['POST'])
def api_add_event():
    events = load_events()
    data = request.json
    data['id'] = max([e.get('id', 0) for e in events], default=0) + 1
    if "icon" not in data:
        data["icon"] = [["#fff"]*20 for _ in range(20)]
    if "participants" not in data:
        data["participants"] = []
    events.append(data)
    save_events(events)
    return jsonify({"ok": True})

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def api_edit_event(event_id):
    events = load_events()
    for e in events:
        if e['id'] == event_id:
            # merge participants instead of overwrite if both exist
            if "participants" in request.json and "participants" in e:
                plist = request.json.get("participants")
                if isinstance(plist, list):
                    e["participants"] = plist
                else:
                    e["participants"] = []
            e.update({k:v for k,v in request.json.items() if k!="participants"})
            break
    save_events(events)
    return jsonify({"ok": True})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def api_delete_event(event_id):
    events = load_events()
    events = [e for e in events if e['id'] != event_id]
    save_events(events)
    return jsonify({"ok": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
