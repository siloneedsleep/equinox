import aiohttp
from aiohttp import web
import json
import time
from config.settings import (
    LUMINOUS_CLIENT_ID, LUMINOUS_CLIENT_SECRET,
    TENEBRIS_CLIENT_ID, TENEBRIS_CLIENT_SECRET,
    OAUTH2_REDIRECT_URI, PORT
)

class EquinoxWebServer:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.app = web.Application()
        self.app.add_routes([
            web.get('/callback', self.oauth_callback),
            web.get('/health', self.health_check)
        ])

    async def health_check(self, request):
        return web.Response(text="Ecosystem Online", status=200)

    async def oauth_callback(self, request):
        code = request.query.get("code")
        state = request.query.get("state", "luminous") # Mặc định luminous nếu lỗi state

        if not code:
            return web.Response(text="❌ Lỗi: Thiếu code xác thực.", status=400)

        if state == "luminous":
            cid, secret = LUMINOUS_CLIENT_ID, LUMINOUS_CLIENT_SECRET
        else:
            cid, secret = TENEBRIS_CLIENT_ID, TENEBRIS_CLIENT_SECRET

        data = {
            "client_id": cid,
            "client_secret": secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH2_REDIRECT_URI
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://discord.com/api/v10/oauth2/token", data=data) as resp:
                if resp.status != 200:
                    return web.Response(text=f"❌ Lỗi Token: {await resp.text()}", status=400)
                tk = await resp.json()

            async with session.get("https://discord.com/api/v10/users/@me", headers={"Authorization": f"Bearer {tk['access_token']}"}) as u_resp:
                if u_resp.status != 200:
                    return web.Response(text="❌ Lỗi định danh.", status=400)
                user = await u_resp.json()
                uid = user['id']

        await self.redis.hset(f"oauth:{uid}", state, json.dumps({
            "access_token": tk["access_token"],
            "refresh_token": tk.get("refresh_token"),
            "scopes": tk.get("scope"),
            "at": int(time.time())
        }))

        return web.Response(text=f"<h1>🎉 Thành Công!</h1><p>Đã ủy quyền {state.capitalize()}. Quay lại Discord.</p>", content_type="text/html")

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        # Bind to 0.0.0.0 là bắt buộc để các dịch vụ Cloud như Render có thể routing HTTPS
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        print(f"[Web Server] Đã kích hoạt tại Port {PORT}. Sẵn sàng nhận Callback HTTPS.")
