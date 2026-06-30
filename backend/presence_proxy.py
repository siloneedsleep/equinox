import asyncio
import aiohttp
import json
import time
from backend.database import EquinoxDatabase

class ProxyPresenceManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.active_sessions = {} # {user_id: ws_connection}
        self.db = EquinoxDatabase(redis_client)

    async def get_user_token(self, user_id: int):
        # Lấy token từ OAuth2 đã lưu
        for state in ["luminous", "tenebris"]:
            raw_oauth = await self.redis.hget(f"oauth:{user_id}", state)
            if raw_oauth:
                data = json.loads(raw_oauth)
                return data.get("access_token")
        return None

    async def maintain_presence(self, user_id: int):
        token = await self.get_user_token(user_id)
        status_data = await self.db.get_custom_status(user_id)
        
        if not token or not status_data:
            print(f"[Presence] Thiếu dữ liệu cho User {user_id}. Hủy kết nối.")
            await self.db.toggle_livestatus(user_id, False)
            return

        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect(self.gateway_url) as ws:
                    self.active_sessions[user_id] = ws

                    # 1. Identify
                    identify_payload = {
                        "op": 2,
                        "d": {
                            "token": token,
                            "capabilities": 16381,
                            "properties": {
                                "os": "Windows",
                                "browser": "Chrome",
                                "device": ""
                            },
                            "presence": {
                                "status": "online",
                                "since": 0,
                                "activities": [],
                                "afk": False
                            }
                        }
                    }
                    await ws.send_json(identify_payload)

                    # 2. Update Presence ngay lập tức
                    # Format activity cho Gateway
                    gateway_activity = {
                        "name": status_data.get("name", "Equinox"),
                        "type": status_data.get("type", 0),
                        "details": status_data.get("details"),
                        "state": status_data.get("state"),
                        "assets": {
                            "large_image": status_data.get("large_image"),
                            "large_text": status_data.get("large_text")
                        }
                    }

                    if "buttons" in status_data:
                        # Gateway không trực tiếp nhận buttons dạng thô này qua Presence Update (op 3)
                        # mà thường qua Rich Presence API phức tạp hơn. Tuy nhiên ta cứ nạp vào.
                        gateway_activity["buttons"] = [b["label"] for b in status_data["buttons"]]

                    presence_payload = {
                        "op": 3,
                        "d": {
                            "since": int(time.time() * 1000),
                            "activities": [gateway_activity],
                            "status": "online",
                            "afk": False
                        }
                    }
                    await ws.send_json(presence_payload)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("op") == 10: # Hello
                                interval = data["d"]["heartbeat_interval"] / 1000
                                asyncio.create_task(self.heartbeat(ws, interval))
                            elif data.get("op") == 7: # Reconnect
                                break
                        elif msg.type in [aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR]:
                            break
            except Exception as e:
                print(f"[Presence] Lỗi WS cho User {user_id}: {e}")
            finally:
                self.active_sessions.pop(user_id, None)

    async def heartbeat(self, ws, interval: float):
        while not ws.closed:
            await asyncio.sleep(interval)
            if not ws.closed:
                await ws.send_json({"op": 1, "d": None})

    async def sync_loop(self):
        print("[Proxy Presence] Đang quét danh sách treo profile...")
        while True:
            try:
                # Tìm các user đã bật livestatus
                keys = await self.redis.keys("livestatus:active:*")
                active_users = [int(k.split(":")[-1]) for k in keys]

                for user_id in active_users:
                    if user_id not in self.active_sessions:
                        asyncio.create_task(self.maintain_presence(user_id))

                # Cleanup sessions đã tắt
                for user_id in list(self.active_sessions.keys()):
                    if user_id not in active_users:
                        ws = self.active_sessions.get(user_id)
                        if ws and not ws.closed:
                            await ws.close()
            except Exception as e:
                print(f"[Presence Sync Loop] Error: {e}")

            await asyncio.sleep(30)
