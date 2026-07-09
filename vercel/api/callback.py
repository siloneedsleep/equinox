from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import time
import redis
from urllib.parse import urlparse, parse_qs

# Cấu hình từ Vercel Environment Variables
LUMINOUS_CLIENT_ID = os.environ.get("LUMINOUS_CLIENT_ID")
LUMINOUS_CLIENT_SECRET = os.environ.get("LUMINOUS_CLIENT_SECRET")
TENEBRIS_CLIENT_ID = os.environ.get("TENEBRIS_CLIENT_ID")
TENEBRIS_CLIENT_SECRET = os.environ.get("TENEBRIS_CLIENT_SECRET")
OAUTH2_REDIRECT_URI = os.environ.get("OAUTH2_REDIRECT_URI")
REDIS_URI = os.environ.get("REDIS_URI")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        code = query.get("code", [None])[0]
        state = query.get("state", ["luminous"])[0]

        if not code:
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"❌ Lỗi: Thiếu mã code. (Path: {self.path})".encode())
            return

        # Phân loại Bot
        if state == "luminous":
            cid, secret = LUMINOUS_CLIENT_ID, LUMINOUS_CLIENT_SECRET
        else:
            cid, secret = TENEBRIS_CLIENT_ID, TENEBRIS_CLIENT_SECRET

        # 1. Trao đổi Token
        try:
            token_resp = requests.post(
                "https://discord.com/api/v10/oauth2/token",
                data={
                    "client_id": cid,
                    "client_secret": secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": OAUTH2_REDIRECT_URI
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_data = token_resp.json()

            if token_resp.status_code != 200:
                raise Exception(f"Discord Token Error: {token_data}")

            # 2. Lấy User Info
            user_resp = requests.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_data = user_resp.json()
            user_id = user_data["id"]

            # 3. Lưu vào Redis
            r = redis.from_url(REDIS_URI, decode_responses=True)
            r.hset(f"oauth:{user_id}", state, json.dumps({
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "scopes": token_data.get("scope"),
                "at": int(time.time())
            }))

            # 4. Trả về giao diện thành công
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = f"""
            <html>
                <body style="background:#2b2d31;color:white;text-align:center;font-family:sans-serif;padding-top:50px;">
                    <h1 style="color:#2ecc71;">🎉 THÀNH CÔNG!</h1>
                    <p>Đã ủy quyền <b>{state.upper()}</b> hoàn tất.</p>
                    <p style="color:#a3a6aa;">Bạn có thể đóng trang này và quay lại Discord.</p>
                </body>
            </html>
            """
            self.wfile.write(html.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"❌ Lỗi hệ thống: {str(e)}".encode())
