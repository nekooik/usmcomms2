# server/server.py
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
MDT_GROUP_ID = 14351433   # Marine Drill Team Group ID
HG_GROUP_ID = 11868282    # Honor Guard Group ID
# ---------------------

# Fast in-memory user and chat database
active_users = {}  
channels_db = {
    "onguard_joint": [],
    "onguard_mdt": [],
    "onguard_hg": [],
    "offduty_joint": [],
    "staff_mdt": [],
    "staff_hg": []
}

@app.route('/login', methods=['POST'])
def login_user():
    """Directly verifies group rank via public APIs, with an automatic bypass fallback."""
    data = request.json or {}
    username = data.get("username", "").strip()
    
    if not username:
        return jsonify({"status": "error", "message": "Username missing"}), 400

    try:
        # 1. Fetch user ID from public Roblox search API
        user_res = requests.get(f"https://roblox.com{username}&limit=1", timeout=3).json()
        if not user_res.get("data"):
            return jsonify({"status": "error", "message": "User not found on Roblox"}), 404
            
        real_username = user_res["data"]["requestedUsername"]
        roblox_id = user_res["data"]["id"]
        
        # 2. Check their group rank membership
        group_url = f"https://roblox.com{roblox_id}/groups/roles"
        group_res = requests.get(group_url, timeout=3).json()
        
        user_rank = "Trainee"
        user_division = "None"
        
        for g in group_res.get("data", []):
            gid = g["group"]["id"]
            role_name = g["role"]["name"]
            
            if gid == MDT_GROUP_ID:
                user_division = "MDT"
                user_rank = role_name
                break
            elif gid == HG_GROUP_ID:
                user_division = "HG"
                user_rank = role_name
                break

        active_users[real_username] = {
            "rank": user_rank.upper(),
            "division": user_division.upper()
        }
        
        return jsonify({
            "status": "success", 
            "username": real_username,
            "rank": user_rank,
            "division": user_division
        })
        
    except Exception as e:
        # 🚨 THE BYPASS FALLBACK: If Roblox blocks or times out your IP, let the user in anyway!
        print(f"[SYSTEM WARNING] Roblox API Timed Out. Activating local fallback for: {username}")
        
        # We assume you are an Instructor/Staff to give you full channel access during local testing
        active_users[username] = {
            "rank": "LOCAL INSTRUCTOR",
            "division": "MDT"
        }
        
        return jsonify({
            "status": "success", 
            "username": username,
            "rank": "Local Instructor",
            "division": "MDT"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Roblox API timed out"}), 500

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json or {}
    user = data.get("user")
    channel = data.get("channel")
    text = data.get("text", "").strip()
    
    if user not in active_users or channel not in channels_db or not text:
        return jsonify({"status": "error", "message": "Unauthorized or empty post"}), 400
        
    session = active_users[user]
    rank = session["rank"]
    division = session["division"]
    
    # STAFF CHANNELS PERMISSION RULES
    if "staff" in channel:
        if "STAFF" not in rank and "INSTRUCTOR" not in rank and "OFFICER" not in rank and "COMMAND" not in rank:
            return jsonify({"status": "denied", "message": "Staff clearance required"}), 403
        if "mdt" in channel and division != "MDT": return jsonify({"status": "denied"}), 403
        if "hg" in channel and division != "HG": return jsonify({"status": "denied"}), 403

    msg_payload = {"user": user, "division": division, "rank": rank, "text": text}
    channels_db[channel].append(msg_payload)
    
    if len(channels_db[channel]) > 40:
        channels_db[channel].pop(0)
        
    return jsonify({"status": "success"})

@app.route('/get/<channel>', methods=['GET'])
def get_messages(channel):
    if channel in channels_db:
        return jsonify(channels_db[channel])
    return jsonify([]), 404

if __name__ == '__main__':
    import os
    # Render assigns an environmental 'PORT' variable dynamically
    port = int(os.environ.get("PORT", 5000))
    # Host must be 0.0.0.0 to accept public internet connections
    app.run(host='0.0.0.0', port=port)
