import time
import os
import json
import threading
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# --- Mini r/place 用 ---
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
    # PNG保存は省略可（必要ならPillowで実装）

def load_canvas():
    global canvas
    try:
        with open(CANVAS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, list) and all(isinstance(row, list) for row in loaded):
                canvas[:] = loaded
    except Exception:
        pass

def save_and_push_periodically():
    while True:
        time.sleep(SAVE_INTERVAL)
        save_canvas()
        # git pushなど自動化したい場合はここで呼ぶ

@app.route('/')
def index():
    return render_template(
        'index.html',
        size=SIZE,
        default_colors=DEFAULT_COLORS
    )

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

# --- イベント表 + アイコンエディタ 用 ---
EVENTS_FILE = "events.json"

def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_events(events):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False)

@app.route('/api/events', methods=['GET'])
def api_get_events():
    return jsonify(load_events())

@app.route('/api/events', methods=['POST'])
def api_add_event():
    events = load_events()
    data = request.json
    data['id'] = max([e.get('id', 0) for e in events], default=0) + 1
    if "icon" not in data:
        # 空白アイコン(20x20 #fff)
        data["icon"] = [["#fff"]*20 for _ in range(20)]
    events.append(data)
    save_events(events)
    return jsonify({"ok": True})

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def api_edit_event(event_id):
    events = load_events()
    for e in events:
        if e['id'] == event_id:
            e.update(request.json)
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
    load_canvas()
    t = threading.Thread(target=save_and_push_periodically, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
