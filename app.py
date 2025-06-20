import time
import os
import json
import threading
import subprocess
from flask import Flask, request, jsonify, render_template
from PIL import Image

app = Flask(__name__)
SIZE = 100
DEFAULT_COLORS = ["#fff", "#f00", "#00f", "#0f0", "#000"]
CANVAS_FILE = "canvas.json"
CANVAS_PNG = "canvas.png"
SAVE_INTERVAL = 300  # 5分

canvas = [[DEFAULT_COLORS[0] for _ in range(SIZE)] for _ in range(SIZE)]
updates = []

def save_canvas():
    with open(CANVAS_FILE, "w", encoding="utf-8") as f:
        json.dump(canvas, f)
    save_canvas_as_png(CANVAS_PNG)

def save_canvas_as_png(filename="canvas.png"):
    img = Image.new('RGB', (SIZE, SIZE), color="#fff")
    pixels = img.load()
    for y in range(SIZE):
        for x in range(SIZE):
            color = canvas[y][x].lstrip('#')
            if len(color) == 3:
                color = ''.join([c*2 for c in color])
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            pixels[x, y] = rgb
    img.save(filename)

def load_canvas():
    global canvas
    # 1. PNGから復元を試みる
    if os.path.exists(CANVAS_PNG):
        try:
            img = Image.open(CANVAS_PNG).convert("RGB")
            if img.size == (SIZE, SIZE):
                for y in range(SIZE):
                    for x in range(SIZE):
                        rgb = img.getpixel((x, y))
                        canvas[y][x] = '#{:02x}{:02x}{:02x}'.format(*rgb)
                return
        except Exception as e:
            print("Failed to load from PNG:", e)
    # 2. PNGがなければJSONから復元
    try:
        with open(CANVAS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, list) and all(isinstance(row, list) for row in loaded):
                canvas[:] = loaded
    except Exception:
        pass

def git_push_canvas():
    try:
        gh_token = os.environ.get('GH_TOKEN')
        repo_url = "https://github.com/fly1014gk/places.git"
        if gh_token and repo_url:
            push_url = repo_url.replace("https://", f"https://{gh_token}@")
            subprocess.run(["git", "config", "--global", "user.email", "renderbot@example.com"], check=True)
            subprocess.run(["git", "config", "--global", "user.name", "renderbot"], check=True)
            subprocess.run(["git", "add", CANVAS_FILE], check=True)
            subprocess.run(["git", "add", CANVAS_PNG], check=True)
            subprocess.run(["git", "commit", "-m", "Periodic update canvas.json & canvas.png"], check=False)
            subprocess.run(["git", "fetch", push_url], check=True)
            subprocess.run(["git", "checkout", "main"], check=True)
            subprocess.run(["git", "pull", "--rebase", push_url, "main"], check=True)
            subprocess.run(["git", "push", push_url, "main"], check=True)
    except Exception as e:
        print("Git push failed:", e)

def save_and_push_periodically():
    save_canvas()
    git_push_canvas()  # サーバー起動直後にもpush
    while True:
        time.sleep(SAVE_INTERVAL)
        save_canvas()
        git_push_canvas()

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
    return jsonify(success=True, timestamp=ts)

@app.route('/diff')
def get_diff():
    since = int(request.args.get('since', 0))
    diff = [u for u in updates if u['timestamp'] > since]
    return jsonify(diff)

if __name__ == '__main__':
    load_canvas()
    t = threading.Thread(target=save_and_push_periodically, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
