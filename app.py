from flask import Flask, request, jsonify, render_template
import time
import os
import json
import threading
import subprocess

app = Flask(__name__)
SIZE = 100
DEFAULT_COLORS = ["#fff", "#f00", "#00f", "#0f0", "#000"]
CANVAS_FILE = "canvas.json"
SAVE_INTERVAL = 300  # 5分 = 300秒

canvas = [[DEFAULT_COLORS[0] for _ in range(SIZE)] for _ in range(SIZE)]
updates = []

def save_canvas():
    with open(CANVAS_FILE, "w", encoding="utf-8") as f:
        json.dump(canvas, f)
    git_push_canvas()

def load_canvas():
    global canvas
    try:
        with open(CANVAS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, list) and all(isinstance(row, list) for row in loaded):
                canvas[:] = loaded
    except Exception:
        pass

def save_canvas_periodically():
    while True:
        time.sleep(SAVE_INTERVAL)
        save_canvas()

def git_push_canvas():
    try:
        # Git user設定（初回のみ・毎回でもOK）
        subprocess.run(["git", "config", "--global", "user.email", "renderbot@example.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "renderbot"], check=True)
        # git add & commit
        subprocess.run(["git", "add", CANVAS_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update canvas.json"], check=True)
        # push（パスワードにトークンを埋め込む）
        gh_token = os.environ.get('GH_TOKEN')
        repo_url = os.environ.get('REPO_URL')  # 例: https://github.com/yourname/yourrepo.git
        if gh_token and repo_url:
            # https://<token>@github.com/user/repo.git 形式
            push_url = repo_url.replace("https://", f"https://{gh_token}@")
            subprocess.run(["git", "push", push_url, "main"], check=True)
    except Exception as e:
        print("Git push failed:", e)

@app.route('/')
def index():
    return render_template('index.html', canvas=canvas, size=SIZE, default_colors=DEFAULT_COLORS)

@app.route('/canvas')
def get_canvas():
    return jsonify(canvas=canvas)

@app.route('/draw', methods=['POST'])
def draw():
    data = request.get_json()
    x, y, color = data['x'], data['y'], data['color']
    ts = int(time.time())
    if 0 <= x < SIZE and 0 <= y < SIZE:
        canvas[y][x] = color
        updates.append({"x": x, "y": y, "color": color, "timestamp": ts})
        save_canvas()  # 描画ごとに保存＆push
    return jsonify(success=True, timestamp=ts)

@app.route('/diff')
def get_diff():
    since = int(request.args.get('since', 0))
    diff = [u for u in updates if u['timestamp'] > since]
    return jsonify(diff)

if __name__ == '__main__':
    load_canvas()
    t = threading.Thread(target=save_canvas_periodically, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
