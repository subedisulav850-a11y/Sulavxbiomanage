from flask import Flask, request, jsonify, make_response
import requests
import binascii
import urllib3
import base64
import json
import random
import sys
import os
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import my_pb2
    import output_pb2
except ImportError:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ---------- Constants (OB54 Updated) ----------
FREEFIRE_UPDATE_URL = "https://clientbp.ggpolarbear.com/UpdateSocialBasicInfo"
MAJOR_LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"
OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
FREEFIRE_VERSION = "OB54"

# Encryption Keys
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# ---------- Device Database ----------
DEVICES = [
    {"model": "SM-G998B", "android": "13", "api": "33", "cpu": "ARMv8 | 2800 | 8", "gpu": "Mali-G78", "res": ["1440", "1080"], "dpi": "480", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "realme C31", "android": "12", "api": "31", "cpu": "ARMv8 | 2000 | 8", "gpu": "Mali-G52", "res": ["720", "1600"], "dpi": "320", "ram": "4096", "build": "SQ3A.220705.003"},
    {"model": "Mi 11", "android": "12", "api": "32", "cpu": "ARMv8 | 2500 | 8", "gpu": "Adreno 650", "res": ["1080", "2400"], "dpi": "395", "ram": "6144", "build": "SQ3A.220705.003"},
    {"model": "OnePlus 9", "android": "13", "api": "33", "cpu": "ARMv8 | 2900 | 8", "gpu": "Adreno 660", "res": ["1080", "2400"], "dpi": "420", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "Pixel 6", "android": "13", "api": "33", "cpu": "ARMv8 | 2800 | 8", "gpu": "Mali-G78", "res": ["1080", "2400"], "dpi": "440", "ram": "8192", "build": "TP1A.220624.014"},
]

def get_random_device():
    device = random.choice(DEVICES)
    return {
        "model": device["model"],
        "android": device["android"],
        "api": device["api"],
        "cpu": device["cpu"],
        "gpu": device["gpu"],
        "width": device["res"][0],
        "height": device["res"][1],
        "dpi": device["dpi"],
        "ram": device["ram"],
        "build": device["build"]
    }

def encrypt_data(data_bytes):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded)

# ---------- Protobuf Setup ----------
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3'
)
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)
BioData = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

# ---------- Helper Functions ----------
def get_name_region_from_reward(access_token):
    try:
        uid_url = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"
        uid_headers = {
            "accept": "application/json, text/plain, */*",
            "access-token": access_token,
            "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36"
        }
        uid_res = requests.get(uid_url, headers=uid_headers, verify=False, timeout=15)
        uid_data = uid_res.json()
        return uid_data.get("uid"), uid_data.get("name"), uid_data.get("region")
    except:
        return None, None, None

# ========== FIXED: Multiple OpenID Methods ==========
def get_openid_method1(uid):
    """Method 1: Shop2Game API"""
    try:
        openid_url = "https://topup.pk/api/auth/player_id_login"
        openid_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
            "X-Requested-With": "mark.via.gp",
        }
        payload = {"app_id": 100067, "login_id": str(uid)}
        res = requests.post(openid_url, headers=openid_headers, json=payload, verify=False, timeout=15)
        return res.json().get("open_id")
    except:
        return None

def get_openid_method2(uid):
    """Method 2: Alternative API"""
    try:
        openid_url = "https://api.garena.com/auth/player_id_login"
        openid_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
        }
        payload = {"app_id": 100067, "login_id": str(uid)}
        res = requests.post(openid_url, headers=openid_headers, json=payload, verify=False, timeout=15)
        return res.json().get("open_id")
    except:
        return None

def get_openid_method3(uid):
    """Method 3: Use UID as OpenID (Fallback)"""
    try:
        if len(str(uid)) >= 10:
            return str(uid)
    except:
        pass
    return None

def get_openid_from_shop2game(uid):
    """Try multiple methods to get OpenID"""
    print(f"[🔍] Getting OpenID for UID: {uid}")
    
    # Method 1: Shop2Game
    open_id = get_openid_method1(uid)
    if open_id:
        print(f"[✅] OpenID found via Method 1: {open_id}")
        return open_id
    
    # Method 2: Alternative API
    open_id = get_openid_method2(uid)
    if open_id:
        print(f"[✅] OpenID found via Method 2: {open_id}")
        return open_id
    
    # Method 3: Fallback (UID as OpenID)
    open_id = get_openid_method3(uid)
    if open_id:
        print(f"[⚠️] Using UID as OpenID (Fallback): {open_id}")
        return open_id
    
    print("[❌] All OpenID methods failed!")
    return None

SECRET_KEY = b"1e5898ccb8dfdd921f9bdea848768b64a201"

def decode_nickname(encoded: str) -> str:
    try:
        raw = base64.b64decode(encoded)
        dec = bytearray()
        for i, b in enumerate(raw):
            dec.append(b ^ SECRET_KEY[i % len(SECRET_KEY)])
        return dec.decode('utf-8', errors='replace')
    except:
        return encoded

def decode_jwt_info(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None, None, None
        payload_b64 = parts[1]
        payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        uid = payload.get("account_id")
        region = payload.get("lock_region")
        nickname = payload.get("nickname")
        if isinstance(nickname, str):
            nickname = decode_nickname(nickname)
        return str(uid), nickname, region
    except:
        return None, None, None

def perform_major_login(access_token, open_id):
    platforms = [8, 3, 4, 6]
    for platform_type in platforms:
        try:
            device = get_random_device()
            game_data = my_pb2.GameData()
            game_data.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.121.0"
            game_data.os_info = f"Android OS {device['android']} / API-{device['api']} ({device['build']})"
            game_data.device_type = "Handheld"
            game_data.network_provider = "Verizon Wireless"
            game_data.connection_type = "WIFI"
            game_data.screen_width = int(device['width'])
            game_data.screen_height = int(device['height'])
            game_data.dpi = device['dpi']
            game_data.cpu_info = device['cpu']
            game_data.total_ram = int(device['ram'])
            game_data.gpu_name = device['gpu']
            game_data.gpu_version = "OpenGL ES 3.2"
            game_data.user_id = f"Google|{random.randint(1000000000000, 9999999999999)}"
            game_data.ip_address = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            game_data.language = "en"
            game_data.open_id = open_id
            game_data.access_token = access_token
            game_data.platform_type = platform_type
            game_data.field_99 = str(platform_type)
            game_data.field_100 = str(platform_type)
            game_data.device_form_factor = "Phone"
            game_data.device_model = device['model']

            serialized_data = game_data.SerializeToString()
            encrypted = encrypt_data(serialized_data)
            hex_encrypted = binascii.hexlify(encrypted).decode('utf-8')
            edata = bytes.fromhex(hex_encrypted)
            
            headers = {
                "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {device['android']}; {device['model']})",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/octet-stream",
                "Expect": "100-continue",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": FREEFIRE_VERSION
            }
            
            response = requests.post(MAJOR_LOGIN_URL, data=edata, headers=headers, verify=False, timeout=20)

            if response.status_code == 200:
                try:
                    example_msg = output_pb2.Garena_420()
                    example_msg.ParseFromString(response.content)
                    for field in example_msg.DESCRIPTOR.fields:
                        if field.name == "token":
                            return getattr(example_msg, field.name)
                except:
                    pass
        except:
            continue
    return None

def perform_guest_login(uid, password):
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    device = get_random_device()
    headers = {
        'User-Agent': f"GarenaMSDK/4.0.19P9({device['model']} ;Android {device['android']};en;US;)",
        'Connection': "Keep-Alive"
    }
    try:
        resp = requests.post(OAUTH_URL, data=payload, headers=headers, timeout=20, verify=False)
        data = resp.json()
        if 'access_token' in data:
            return data['access_token'], data.get('open_id')
    except:
        pass
    return None, None

def upload_bio_request(jwt_token, bio_text):
    try:
        data = BioData()
        data.field_2 = 17
        data.field_5.CopyFrom(EmptyMessage())
        data.field_6.CopyFrom(EmptyMessage())
        data.field_8 = bio_text
        data.field_9 = 1
        data.field_11.CopyFrom(EmptyMessage())
        data.field_12.CopyFrom(EmptyMessage())

        data_bytes = data.SerializeToString()
        encrypted = encrypt_data(data_bytes)

        device = get_random_device()
        headers = {
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FREEFIRE_VERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {device['android']}; {device['model']})",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {jwt_token}"
        }

        resp = requests.post(FREEFIRE_UPDATE_URL, headers=headers, data=encrypted, timeout=30, verify=False)

        if resp.status_code == 200:
            status_text = "✅ Success"
        elif resp.status_code == 401:
            status_text = "❌ Unauthorized (Invalid JWT)"
        else:
            status_text = f"⚠️ Status {resp.status_code}"

        return {
            "status": status_text,
            "code": resp.status_code,
            "bio": bio_text,
            "server_response": binascii.hexlify(resp.content).decode('utf-8')
        }
    except Exception as e:
        return {"status": f"Error: {str(e)}", "code": 500, "bio": bio_text, "server_response": "N/A"}

# ---------- Routes ----------
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "api": "Long Bio API (OB54)",
        "credit": "sulavji",
        "telegram": "@sulavji",
        "version": "OB54",
        "status": "running ✅",
        "endpoints": {
            "/bio_upload": {
                "method": "GET/POST",
                "params": {
                    "bio": "string (required)",
                    "jwt": "string (optional)",
                    "uid": "string (optional)",
                    "pass": "string (optional)",
                    "access": "string (optional)"
                }
            }
        }
    })

@app.route("/bio_upload", methods=["GET", "POST"])
def combined_bio_upload():
    bio = request.args.get("bio") or request.form.get("bio")
    jwt_token = request.args.get("jwt") or request.form.get("jwt")
    uid = request.args.get("uid") or request.form.get("uid")
    password = request.args.get("pass") or request.form.get("pass")
    access_token = request.args.get("access") or request.form.get("access") or request.args.get("access_token")

    if not bio:
        return jsonify({"status": "❌ Error", "code": 400, "error": "Missing 'bio' parameter"}), 400

    final_jwt = None
    login_method = "Direct JWT"
    final_open_id = None
    final_access_token = None
    final_uid = None
    final_name = None
    final_region = None

    # JWT
    if jwt_token:
        final_jwt = jwt_token
        j_uid, j_name, j_region = decode_jwt_info(jwt_token)
        final_uid = j_uid
        final_name = j_name
        final_region = j_region

    # UID + Password
    elif uid and password:
        login_method = "UID/Pass Login"
        acc_token, login_openid = perform_guest_login(uid, password)
        if acc_token and login_openid:
            final_access_token = acc_token
            final_open_id = login_openid
            final_jwt = perform_major_login(final_access_token, final_open_id)
            if final_jwt:
                j_uid, j_name, j_region = decode_jwt_info(final_jwt)
                final_uid = j_uid
                final_name = j_name
                final_region = j_region
            else:
                return jsonify({"status": "❌ JWT Generation Failed", "code": 500}), 500
        else:
            return jsonify({"status": "❌ Guest Login Failed", "code": 401}), 401

    # Access Token
    elif access_token:
        login_method = "Access Token Login"
        final_access_token = access_token
        
        # Check if it's already a JWT
        j_uid, j_name, j_region = decode_jwt_info(access_token)
        if j_uid:
            final_uid = j_uid
            final_name = j_name
            final_region = j_region
            final_jwt = access_token
            final_open_id = None
        else:
            # Try Reward API
            f_uid, f_name, f_region = get_name_region_from_reward(access_token)
            if f_uid:
                final_uid = f_uid
                final_name = f_name
                final_region = f_region
                final_open_id = get_openid_from_shop2game(final_uid)
                if final_open_id:
                    final_jwt = perform_major_login(access_token, final_open_id)
                else:
                    # If no OpenID, try with UID as OpenID
                    final_open_id = str(final_uid)
                    print(f"[⚠️] Using UID as OpenID: {final_open_id}")
                    final_jwt = perform_major_login(access_token, final_open_id)
                    if not final_jwt:
                        return jsonify({"status": "❌ Failed to get OpenID", "code": 400}), 400
            else:
                return jsonify({"status": "❌ Invalid Access Token", "code": 400}), 400
        
        if not final_jwt:
            return jsonify({"status": "❌ JWT Generation Failed", "code": 500}), 500

    else:
        return jsonify({"status": "❌ Error", "code": 400, "error": "Provide JWT, or UID/Pass, or Access Token"}), 400

    if not final_jwt:
        return jsonify({"status": "❌ JWT Generation Failed", "code": 500}), 500

    result = upload_bio_request(final_jwt, bio)

    response_data = {
        "Credit": "sulavji",
        "Join For More": "Telegram: @sulavxapis",
        "status": result["status"],
        "login_method": login_method,
        "code": result["code"],
        "bio": result["bio"],
        "uid": str(final_uid) if final_uid else None,
        "name": final_name,
        "region": final_region,
        "open_id": final_open_id,
        "access_token": final_access_token,
        "server_response": result["server_response"],
        "generated_jwt": final_jwt,
        "version": "OB54"
    }

    response = make_response(jsonify(response_data))
    response.headers["Content-Type"] = "application/json"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)