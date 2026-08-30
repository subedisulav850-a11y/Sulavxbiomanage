# api/index.py
from flask import Flask, request, jsonify, make_response
import requests
import binascii
import jwt
import urllib3
import base64
import json
import random
import re
import sys
import os
import time
from urllib.parse import urlparse, parse_qs, unquote
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# Add parent directory to path for imports (for Vercel)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Encryption Keys (Same)
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# ---------- Country/Region Configuration ----------
COUNTRIES = {
    "BD": {"code": "BD", "name": "Bangladesh", "language": "bn"},
    "IN": {"code": "IN", "name": "India", "language": "hi"},
    "ME": {"code": "ME", "name": "Middle East", "language": "ar"},
    "PK": {"code": "PK", "name": "Pakistan", "language": "ur"},
    "RU": {"code": "RU", "name": "Russia", "language": "ru"},
    "BR": {"code": "BR", "name": "Brazil", "language": "pt"},
    "ID": {"code": "ID", "name": "Indonesia", "language": "id"},
    "MY": {"code": "MY", "name": "Malaysia", "language": "ms"},
    "PH": {"code": "PH", "name": "Philippines", "language": "tl"},
    "SG": {"code": "SG", "name": "Singapore", "language": "en"},
    "TH": {"code": "TH", "name": "Thailand", "language": "th"},
    "VN": {"code": "VN", "name": "Vietnam", "language": "vi"},
    "EG": {"code": "EG", "name": "Egypt", "language": "ar"},
    "SA": {"code": "SA", "name": "Saudi Arabia", "language": "ar"},
    "TR": {"code": "TR", "name": "Turkey", "language": "tr"},
    "US": {"code": "US", "name": "United States", "language": "en"},
    "GB": {"code": "GB", "name": "United Kingdom", "language": "en"},
    "DE": {"code": "DE", "name": "Germany", "language": "de"},
    "FR": {"code": "FR", "name": "France", "language": "fr"},
    "ES": {"code": "ES", "name": "Spain", "language": "es"},
}

# ---------- Network Providers by Region ----------
NETWORK_PROVIDERS = {
    "BD": ["Grameenphone", "Robi", "Banglalink", "Teletalk"],
    "IN": ["Airtel", "Jio", "Vi", "BSNL"],
    "PK": ["Jazz", "Zong", "Telenor", "Ufone"],
    "ME": ["du", "Etisalat", "STC", "Zain"],
    "RU": ["MTS", "Beeline", "Megafon", "Tele2"],
    "BR": ["Vivo", "Claro", "TIM", "Oi"],
    "ID": ["Telkomsel", "Indosat", "XL Axiata", "Tri"],
    "MY": ["Celcom", "Maxis", "Digi", "U Mobile"],
    "PH": ["Smart", "Globe", "Dito", "Sun"],
    "SG": ["Singtel", "StarHub", "M1", "TPG"],
    "TH": ["AIS", "TrueMove", "DTAC", "TOT"],
    "VN": ["Viettel", "Vinaphone", "Mobifone", "Vietnamobile"],
    "US": ["Verizon", "AT&T", "T-Mobile", "Sprint"],
    "GB": ["EE", "Vodafone", "O2", "Three"],
    "DE": ["Deutsche Telekom", "Vodafone", "O2"],
    "FR": ["Orange", "SFR", "Bouygues", "Free"],
    "ES": ["Movistar", "Vodafone", "Orange", "Yoigo"],
}

# ---------- Device Database ----------
DEVICES = [
    {"model": "SM-G998B", "android": "13", "api": "33", "cpu": "ARMv8 | 2800 | 8", "gpu": "Mali-G78", "res": ["1440", "1080"], "dpi": "480", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "realme C31", "android": "12", "api": "31", "cpu": "ARMv8 | 2000 | 8", "gpu": "Mali-G52", "res": ["720", "1600"], "dpi": "320", "ram": "4096", "build": "SQ3A.220705.003"},
    {"model": "Mi 11", "android": "12", "api": "32", "cpu": "ARMv8 | 2500 | 8", "gpu": "Adreno 650", "res": ["1080", "2400"], "dpi": "395", "ram": "6144", "build": "SQ3A.220705.003"},
    {"model": "OnePlus 9", "android": "13", "api": "33", "cpu": "ARMv8 | 2900 | 8", "gpu": "Adreno 660", "res": ["1080", "2400"], "dpi": "420", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "VIVO V21", "android": "12", "api": "31", "cpu": "ARMv8 | 2400 | 8", "gpu": "Mali-G57", "res": ["1080", "2400"], "dpi": "400", "ram": "8192", "build": "SP1A.210812.016"},
    {"model": "OPPO Reno6", "android": "11", "api": "30", "cpu": "ARMv8 | 2200 | 8", "gpu": "Mali-G52", "res": ["1080", "2400"], "dpi": "410", "ram": "6144", "build": "RP1A.200720.011"},
    {"model": "Pixel 6", "android": "13", "api": "33", "cpu": "ARMv8 | 2800 | 8", "gpu": "Mali-G78", "res": ["1080", "2400"], "dpi": "440", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "TECNO Spark 8", "android": "11", "api": "30", "cpu": "ARMv8 | 1800 | 8", "gpu": "Mali-G52", "res": ["720", "1640"], "dpi": "320", "ram": "4096", "build": "RP1A.200720.011"},
    {"model": "Infinix Hot 12", "android": "11", "api": "30", "cpu": "ARMv8 | 1800 | 8", "gpu": "Mali-G52", "res": ["720", "1600"], "dpi": "320", "ram": "4096", "build": "RP1A.200720.011"},
    {"model": "Nokia G21", "android": "12", "api": "31", "cpu": "ARMv8 | 1800 | 8", "gpu": "Adreno 610", "res": ["720", "1600"], "dpi": "300", "ram": "4096", "build": "SP1A.210812.016"},
    {"model": "Moto G31", "android": "12", "api": "31", "cpu": "ARMv8 | 2000 | 8", "gpu": "Adreno 610", "res": ["720", "1600"], "dpi": "320", "ram": "4096", "build": "SP1A.210812.016"},
    {"model": "Galaxy A53", "android": "13", "api": "33", "cpu": "ARMv8 | 2400 | 8", "gpu": "Mali-G52", "res": ["1080", "2400"], "dpi": "380", "ram": "6144", "build": "TP1A.220624.014"},
    {"model": "Xiaomi 12", "android": "13", "api": "33", "cpu": "ARMv8 | 3000 | 8", "gpu": "Adreno 730", "res": ["1080", "2400"], "dpi": "430", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "Poco X4", "android": "12", "api": "31", "cpu": "ARMv8 | 2200 | 8", "gpu": "Adreno 618", "res": ["1080", "2400"], "dpi": "400", "ram": "6144", "build": "SQ3A.220705.003"},
]

def get_random_device():
    device = random.choice(DEVICES)
    android_versions = ["11", "12", "13", "14"]
    api_levels = {"11": "30", "12": "31", "13": "33", "14": "34"}
    android = random.choice(android_versions)
    api = api_levels[android]
    return {
        "model": device["model"],
        "android": android,
        "api": api,
        "cpu": device["cpu"],
        "gpu": device["gpu"],
        "width": device["res"][0],
        "height": device["res"][1],
        "dpi": device["dpi"],
        "ram": device["ram"],
        "build": f"TP1A.220624.{random.randint(100,999)}" if android == "13" else f"SQ3A.220705.{random.randint(100,999)}"
    }

def get_network_provider(region_code):
    providers = NETWORK_PROVIDERS.get(region_code, ["Verizon", "AT&T", "T-Mobile", "Sprint"])
    return random.choice(providers)

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
def encrypt_data(data_bytes):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded)

def get_name_region_from_reward(access_token):
    try:
        uid_url = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"
        uid_headers = {
            "authority": "prod-api.reward.ff.garena.com",
            "method": "GET",
            "path": "/redemption/api/auth/inspect_token/",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "access-token": access_token,
            "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 Chrome/124.0.0.0"
        }
        uid_res = requests.get(uid_url, headers=uid_headers, verify=False, timeout=20)
        uid_data = uid_res.json()
        return uid_data.get("uid"), uid_data.get("name"), uid_data.get("region")
    except Exception as e:
        return None, None, None

def get_openid_from_shop2game(uid):
    if not uid: return None
    try:
        openid_url = "https://topup.pk/api/auth/player_id_login"
        openid_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-MM,en-US;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Origin": "https://topup.pk",
            "Referer": "https://topup.pk/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "X-Requested-With": "mark.via.gp",
        }
        payload = {"app_id": 100067, "login_id": str(uid)}
        res = requests.post(openid_url, headers=openid_headers, json=payload, verify=False, timeout=20)
        data = res.json()
        return data.get("open_id")
    except Exception as e:
        return None

SECRET_KEY = b"1e5898ccb8dfdd921f9bdea848768b64a201"

def decode_nickname(encoded: str) -> str:
    try:
        raw = base64.b64decode(encoded)
        dec = bytearray()
        for i, b in enumerate(raw):
            dec.append(b ^ SECRET_KEY[i % len(SECRET_KEY)])
        return dec.decode('utf-8', errors='replace')
    except Exception:
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
    except Exception as e:
        return None, None, None

def perform_major_login(access_token, open_id, region="US"):
    platforms = [8, 3, 4, 6]
    for platform_type in platforms:
        try:
            device = get_random_device()
            network_provider = get_network_provider(region)
            
            game_data = my_pb2.GameData()
            game_data.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.121.0"
            game_data.os_info = f"Android OS {device['android']} / API-{device['api']} ({device['build']})"
            game_data.device_type = "Handheld"
            game_data.network_provider = network_provider
            game_data.connection_type = random.choice(["WIFI", "MOBILE", "5G", "4G"])
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
                "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {device['android']}; {device['model']} Build/{device['build']})",
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
                except Exception:
                    pass
        except Exception as e:
            continue
    return None

def perform_guest_login(uid, password, region="US"):
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
        'User-Agent': f"GarenaMSDK/4.0.19P9({device['model']} ;Android {device['android']};{region.lower()};{region.lower()};)",
        'Connection': "Keep-Alive"
    }
    try:
        resp = requests.post(OAUTH_URL, data=payload, headers=headers, timeout=20, verify=False)
        data = resp.json()
        if 'access_token' in data:
            return data['access_token'], data.get('open_id')
    except Exception as e:
        pass
    return None, None

def upload_bio_request(jwt_token, bio_text, region="US"):
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
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {device['android']}; {device['model']} Build/{device['build']})",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {jwt_token}"
        }

        resp = requests.post(FREEFIRE_UPDATE_URL, headers=headers, data=encrypted, timeout=30, verify=False)

        status_text = "Unknown"
        if resp.status_code == 200: 
            status_text = "✅ Success"
        elif resp.status_code == 401: 
            status_text = "❌ Unauthorized (Invalid JWT)"
        elif resp.status_code == 403: 
            status_text = "❌ Forbidden"
        elif resp.status_code == 500: 
            status_text = "❌ Server Error"
        else: 
            status_text = f"⚠️ Status {resp.status_code}"

        raw_hex = binascii.hexlify(resp.content).decode('utf-8')

        return {
            "status": status_text,
            "code": resp.status_code,
            "bio": bio_text,
            "server_response": raw_hex,
            "country": region
        }
    except Exception as e:
        return {"status": f"Error: {str(e)}", "code": 500, "bio": bio_text, "server_response": "N/A", "country": region}


# ---------- Token/JWT Helpers ----------
def clean_access_token(token):
    """Normalize a token extracted from a callback URL/body."""
    if not token:
        return None
    token = unquote(str(token)).strip()
    token = token.split("&", 1)[0].split("?", 1)[0]
    token = re.sub(r"\\u[0-9a-fA-F]{4}", "", token)
    return token.strip()

def eat_access_token(eat_token):
    """
    Exchange an explicitly supplied eat-token through the callback endpoint.
    Redirects are inspected without automatically following them.
    """
    if not eat_token:
        return None

    url = "https://api-otrss.garena.com/support/callback/"
    try:
        resp = requests.get(
            url,
            params={"access_token": eat_token},
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=False,
            timeout=10,
            verify=False,
        )

        candidates = []

        location = resp.headers.get("Location")
        if location:
            candidates.append(location)

        try:
            candidates.append(resp.text)
        except Exception:
            pass

        for text in candidates:
            match = re.search(r"access_token=([^&\s\"']+)", text)
            if match:
                return clean_access_token(match.group(1))

            try:
                parsed = urlparse(text)
                value = parse_qs(parsed.query).get("access_token", [None])[0]
                if value:
                    return clean_access_token(value)
            except Exception:
                pass

        # Some deployments return the supplied token as the usable token.
        if resp.ok and eat_token:
            return clean_access_token(eat_token)
    except requests.RequestException:
        pass

    return None

def jwt_from_access_token(access_token):
    """Create the game JWT from a supplied access token."""
    access_token = clean_access_token(access_token)
    if not access_token:
        return None, None, None, None

    uid, name, region = get_name_region_from_reward(access_token)
    if not uid:
        return None, None, None, None

    open_id = get_openid_from_shop2game(uid)
    if not open_id:
        return None, None, None, None

    jwt_token = perform_major_login(access_token, open_id, region or "US")
    if not jwt_token:
        return None, None, None, None

    return jwt_token, uid, name, region

def token_response(jwt_token, uid=None, name=None, region=None, method=None):
    """Consistent JSON response for token endpoints."""
    return jsonify({
        "status": "success",
        "login_method": method,
        "uid": str(uid) if uid is not None else None,
        "name": name,
        "region": region,
        "jwt": jwt_token,
        "version": FREEFIRE_VERSION,
    })

# ---------- Routes ----------
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "api": "Long Bio API (OB54) - Multi Country Support",
        "credit": "sulavji",
        "telegram": "@sulavxapis",
        "version": "OB54",
        "status": "running on Vercel ✅",
        "supported_countries": list(COUNTRIES.keys()),
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
            },
            "/eat-access=<eat_token>": "Exchange an explicitly supplied eat-token and return a generated JWT",
            "/token?uid=<uid>&password=<password>": "Generate a JWT from supplied account credentials",
            "/token?access=<access_token>": "Generate a JWT from a supplied access token"
        }
    })


@app.route("/eat-access=<eat_token>", methods=["GET"])
def eat_access_route(eat_token):
    if not eat_token:
        return jsonify({"status": "error", "code": 400, "error": "Missing eat token"}), 400

    access_token = eat_access_token(eat_token)
    if not access_token:
        return jsonify({"status": "error", "code": 401, "error": "Could not exchange eat token"}), 401

    jwt_token, uid, name, region = jwt_from_access_token(access_token)
    if not jwt_token:
        return jsonify({"status": "error", "code": 401, "error": "JWT generation failed"}), 401

    return token_response(jwt_token, uid, name, region, "eat-access")


@app.route("/token", methods=["GET", "POST"])
def token_route():
    uid = request.args.get("uid") or request.form.get("uid")
    password = request.args.get("password") or request.form.get("password")
    access_token = (
        request.args.get("access")
        or request.form.get("access")
        or request.args.get("access_token")
        or request.form.get("access_token")
    )

    # UID/password mode
    if uid and password:
        access_token, open_id = perform_guest_login(uid, password)
        if not access_token or not open_id:
            return jsonify({"status": "error", "code": 401, "error": "Guest login failed"}), 401

        jwt_token = perform_major_login(access_token, open_id)
        if not jwt_token:
            return jsonify({"status": "error", "code": 401, "error": "JWT generation failed"}), 401

        j_uid, name, region = decode_jwt_info(jwt_token)
        return token_response(jwt_token, j_uid or uid, name, region, "uid-password")

    # Access-token mode
    if access_token:
        jwt_token, j_uid, name, region = jwt_from_access_token(access_token)
        if not jwt_token:
            return jsonify({"status": "error", "code": 401, "error": "Invalid access token or JWT generation failed"}), 401

        return token_response(jwt_token, j_uid, name, region, "access")

    return jsonify({
        "status": "error",
        "code": 400,
        "error": "Provide uid+password or access"
    }), 400


@app.route("/bio_upload", methods=["GET", "POST"])
def combined_bio_upload():
    # Get parameters (NO country parameter needed)
    bio = request.args.get("bio") or request.form.get("bio")
    jwt_token = request.args.get("jwt") or request.form.get("jwt")
    uid = request.args.get("uid") or request.form.get("uid")
    password = request.args.get("pass") or request.form.get("pass")
    access_token = request.args.get("access") or request.form.get("access") or request.args.get("access_token")
    
    # Auto detect or random country (ইউজারকে দিতে হবে না)
    country_code = random.choice(list(COUNTRIES.keys()))
    
    # Validate bio
    if not bio:
        return jsonify({"status": "❌ Error", "code": 400, "error": "Missing 'bio' parameter"}), 400
    
    country_info = COUNTRIES.get(country_code, COUNTRIES["US"])
    
    final_jwt = None
    login_method = "Direct JWT"
    final_open_id = None
    final_access_token = None
    final_uid = None
    final_name = None
    final_region = None

    # Try JWT first
    if jwt_token:
        final_jwt = jwt_token
        j_uid, j_name, j_region = decode_jwt_info(jwt_token)
        final_uid = j_uid
        final_name = j_name
        final_region = j_region
        
    # Try UID/Password
    elif uid and password:
        login_method = f"UID/Pass Login ({country_code})"
        acc_token, login_openid = perform_guest_login(uid, password, country_code)
        if acc_token and login_openid:
            final_access_token = acc_token
            final_open_id = login_openid
            final_jwt = perform_major_login(final_access_token, final_open_id, country_code)
            if final_jwt:
                j_uid, j_name, j_region = decode_jwt_info(final_jwt)
                final_uid = j_uid
                final_name = j_name
                final_region = j_region
            else:
                return jsonify({
                    "status": "❌ JWT Generation Failed", 
                    "code": 500
                }), 500
        else:
            return jsonify({
                "status": "❌ Guest Login Failed", 
                "code": 401
            }), 401

    # Try Access Token
    elif access_token:
        login_method = f"Access Token Login ({country_code})"
        final_access_token = access_token
        f_uid, f_name, f_region = get_name_region_from_reward(access_token)
        final_uid = f_uid
        final_name = f_name
        final_region = f_region

        if not final_uid:
            return jsonify({
                "status": "❌ Invalid Access Token", 
                "code": 400
            }), 400

        final_open_id = get_openid_from_shop2game(final_uid)
        if final_open_id:
            final_jwt = perform_major_login(access_token, final_open_id, country_code)
        else:
            return jsonify({
                "status": "❌ Shop2Game OpenID Fetch Failed", 
                "code": 400
            }), 400
    
    else:
        return jsonify({
            "status": "❌ Error", 
            "code": 400, 
            "error": "Provide JWT, or UID/Pass, or Access Token"
        }), 400

    if not final_jwt:
        return jsonify({
            "status": "❌ JWT Generation Failed", 
            "code": 500
        }), 500

    # Upload bio
    result = upload_bio_request(final_jwt, bio, country_code)
    
    # Prepare response
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
        "country": country_info["name"],
        "country_code": country_code,
        "open_id": final_open_id,
        "access_token": final_access_token,
        "server_response": result["server_response"],
        "generated_jwt": final_jwt,
        "version": "OB54"
    }

    response = make_response(jsonify(response_data))
    response.headers["Content-Type"] = "application/json"
    return response

# ========== VERCEL HANDLER ==========
app = app

def handler(request, context):
    return app(request, context)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)