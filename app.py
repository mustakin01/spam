from flask import Flask, request, jsonify, render_template_string
import urllib.parse
import requests
import json
import time
import threading
from queue import Queue
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

# Region-wise base URLs
REGION_URLS = {
    "bd": "https://clientbp.ggpolarbear.com/RequestAddingFriend",
    "ind": "https://client.ind.freefiremobile.com/RequestAddingFriend"
}

REGION_TOKENS = {
    "bd": "token_bd.json",
    "ind": "token_ind.json"
}

# Task queue
task_queue = Queue()

def load_tokens(token_file):
    try:
        with open(token_file, "r") as f:
            data = json.load(f)
        return [item["token"] for item in data]
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return []

def send_friend_request(uid, token, url, results):
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB54",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "16",
        'User-Agent': "ART/2.2.0 (Linux; U; Android 14; SAMSUNG_S25 Build/UP1A.240905.001)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            results["success"] += 1
        else:
            results["failed"] += 1
    except Exception as e:
        print(f"Request error: {e}")
        results["failed"] += 1

# Worker to process tasks sequentially
def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        uid = task['uid']
        region = task['region']
        results = {"success": 0, "failed": 0}

        url = REGION_URLS[region]
        tokens = load_tokens(REGION_TOKENS[region])

        for token in tokens[:110]:
            send_friend_request(uid, token, url, results)
            time.sleep(0)  # 2-second delay per request

        task['results'] = results
        task['done'] = True
        task_queue.task_done()

# Start background worker thread
threading.Thread(target=worker, daemon=True).start()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Free Fire - Salman Friend Request Sender</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
    .container { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border-radius: 20px; padding: 40px; width: 100%; max-width: 520px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
    h1 { color: #fff; text-align: center; font-size: 24px; margin-bottom: 8px; }
    .subtitle { color: rgba(255,255,255,0.5); text-align: center; font-size: 13px; margin-bottom: 30px; }
    .form-group { margin-bottom: 20px; }
    label { display: block; color: rgba(255,255,255,0.7); font-size: 14px; margin-bottom: 6px; font-weight: 500; }
    input, select { width: 100%; padding: 12px 16px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; color: #fff; font-size: 15px; outline: none; transition: 0.2s; }
    input:focus, select:focus { border-color: #6c63ff; box-shadow: 0 0 0 3px rgba(108,99,255,0.2); }
    select option { background: #302b63; color: #fff; }
    button { width: 100%; padding: 14px; background: linear-gradient(135deg, #6c63ff, #e040fb); border: none; border-radius: 10px; color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; transition: 0.2s; margin-top: 8px; }
    button:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(108,99,255,0.4); }
    button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    .result { margin-top: 25px; padding: 20px; border-radius: 12px; display: none; }
    .result.success { display: block; background: rgba(0,255,100,0.1); border: 1px solid rgba(0,255,100,0.2); }
    .result.error { display: block; background: rgba(255,50,50,0.1); border: 1px solid rgba(255,50,50,0.2); }
    .result .stat { display: flex; justify-content: space-between; padding: 8px 0; color: #fff; font-size: 14px; }
    .result .stat:not(:last-child) { border-bottom: 1px solid rgba(255,255,255,0.06); }
    .stat-label { color: rgba(255,255,255,0.6); }
    .stat-value { font-weight: 600; }
    .stat-value.green { color: #4caf50; }
    .stat-value.red { color: #f44336; }
    .stat-value.gold { color: #ffc107; }
    .loading { text-align: center; color: rgba(255,255,255,0.6); display: none; margin-top: 20px; }
    .loading.active { display: block; }
    .spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #6c63ff; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 10px auto; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 Salman Friend Request Sender</h1>
    <p class="subtitle">Free Fire - Send bulk friend requests</p>
    <form id="requestForm">
      <div class="form-group">
        <label for="uid">Target UID</label>
        <input type="text" id="uid" name="uid" placeholder="Enter Free Fire UID" required>
      </div>
      <div class="form-group">
        <label for="region">Region</label>
        <select id="region" name="region">
          <option value="bd">Bangladesh (BD)</option>
          <option value="ind">India (IND)</option>
        </select>
      </div>
      <button type="submit" id="submitBtn">Send Requests</button>
    </form>
    <div class="loading" id="loading">
      <div class="spinner"></div>
      <p>Sending requests... please wait</p>
    </div>
    <div class="result" id="result"></div>
  </div>
  <script>
    const form = document.getElementById('requestForm');
    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    const resultDiv = document.getElementById('result');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const uid = document.getElementById('uid').value.trim();
      const region = document.getElementById('region').value;

      resultDiv.style.display = 'none';
      resultDiv.className = 'result';
      loading.classList.add('active');
      submitBtn.disabled = true;

      try {
        const res = await fetch(`/send_requests?uid=${encodeURIComponent(uid)}&region=${region}`);
        const data = await res.json();

        loading.classList.remove('active');
        submitBtn.disabled = false;

        if (data.error) {
          resultDiv.className = 'result error';
          resultDiv.innerHTML = `<div class="stat"><span class="stat-label">Error</span><span class="stat-value red">${data.error}</span></div>`;
        } else {
          resultDiv.className = 'result success';
          resultDiv.innerHTML = `
            <div class="stat"><span class="stat-label">Player Name</span><span class="stat-value gold">${data.player_name}</span></div>
            <div class="stat"><span class="stat-label">UID</span><span class="stat-value">${data.uid}</span></div>
            <div class="stat"><span class="stat-label">Region</span><span class="stat-value">${data.region.toUpperCase()}</span></div>
            <div class="stat"><span class="stat-label">✅ Success</span><span class="stat-value green">${data.success}</span></div>
            <div class="stat"><span class="stat-label">❌ Failed</span><span class="stat-value red">${data.failed}</span></div>
            <div class="stat"><span class="stat-label">Status</span><span class="stat-value gold">${data.status === 1 ? 'Completed' : 'No requests sent'}</span></div>
          `;
        }
      } catch (err) {
        loading.classList.remove('active');
        submitBtn.disabled = false;
        resultDiv.className = 'result error';
        resultDiv.innerHTML = `<div class="stat"><span class="stat-label">Error</span><span class="stat-value red">Failed to send request</span></div>`;
      }
    });
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route("/send_requests", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")
    region = request.args.get("region", "bd").lower()

    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400
    if region not in REGION_URLS:
        return jsonify({"error": "Invalid region. Use 'bd' or 'ind'."}), 400

    # Player info
    try:
        info = requests.get(f"https://info-bot-api.vercel.app/player-info?uid={uid}").json()
        player_name = info.get("basicInfo", {}).get("nickname", "Unknown")
    except:
        player_name = "Unknown"

    # Add task to queue
    task = {"uid": uid, "region": region, "done": False}
    task_queue.put(task)

    # Wait until task is done
    while not task.get('done', False):
        time.sleep(0.5)

    results = task['results']
    status = 1 if results["success"] > 0 else 2

    return jsonify({
        "region": region,
        "uid": uid,
        "player_name": player_name,
        "success": results["success"],
        "failed": results["failed"],
        "status": status
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=False)
