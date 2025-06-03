from flask import Flask, request, jsonify, render_template
import time
import os
import json

app = Flask(__name__)
SIZE = 100
DEFAULT_COLORS = ["#fff", "#f00", "#00f", "#0f0", "#000"]
CANVAS_FILE = "canvas.json"
canvas = [[DEFAULT_COLORS[0] for _ in range(SIZE)] for _ in range(SIZE)]
updates = []

def save_canvas():
    with open(CANVAS_FILE, "w", encoding="utf-8") as f:
        json.dump(canvas, f)

def load_canvas():
    global canvas
    try:
        with open(CANVAS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, list) and all(isinstance(row, list) for row in loaded):
                canvas[:] = loaded
    except Exception:
        pass

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
        save_canvas()
    return jsonify(success=True, timestamp=ts)

@app.route('/diff')
def get_diff():
    since = int(request.args.get('since', 0))
    diff = [u for u in updates if u['timestamp'] > since]
    return jsonify(diff)

if __name__ == '__main__':
    load_canvas()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
