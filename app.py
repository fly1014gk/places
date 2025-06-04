import os
import json
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

EVENTS_FILE = "events.json"

def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_events(events):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False)

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
