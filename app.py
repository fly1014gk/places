from flask import Flask, request, jsonify, send_from_directory
import time

app = Flask(__name__)
SIZE = 400
canvas = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
updates = []

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/canvas')
def get_canvas():
    return jsonify(canvas=canvas)

@app.route('/draw', methods=['POST'])
def draw():
    data = request.json
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
    app.run(host='0.0.0.0', port=10000)
