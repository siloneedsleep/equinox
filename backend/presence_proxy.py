import asyncio
import aiohttp
import json
import time

class ProxyPresenceManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.active_sessions = {}

    async def get_user_status(self, user_id: int):
        raw_status = await self.redis.hget("custom_statuses", str(user_id))
        return json.loads(raw_status) if raw_status else None

    async def get_user_token(self, user_id: int):
        for state in ["luminous", "tenebris"]:
            raw_oauth = await self.redis.hget(f"oauth:{user_id}", state)
            if raw_oauth:
                return json.loads(raw_oauth).get("access_token")
        return None

    async def maintain_presence(self, user_id: int):
        token = await self.get_user_token(user_id)
        status_data = await self.get_user_status(user_id)
        
        if not token or not status_data:
            return

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.gateway_url) as ws:
                self.active_sessions[user_id] = ws
                
                identify_payload = {
                    "op": 2,
                    "d": {
                        "token": token,
                        "properties": {
                            "os": "linux",
                            "browser": "EquinoxProxy",
                            "device": "EquinoxCloud"
                        }
                    }
                }
                await ws.send_json(identify_payload)

                presence_payload = {
                    "op": 3,
                    "d": {
                        "since": int(time.time() * 1000),
                        "activities": [status_data],
                        "status": "online",
                        "afk": False
                    }
                }
                await ws.send_json(presence_payload)

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("op") == 10:
                            interval = data["d"]["heartbeat_interval"] / 1000
                            asyncio.create_task(self.heartbeat(ws, interval))

    async def heartbeat(self, ws, interval: float):
        while not ws.closed:
            await asyncio.sleep(interval)
            if not ws.closed:
                await ws.send_json({"op": 1, "d": None})

    async def sync_loop(self):
        print("[Proxy Presence] Khởi động động cơ đồng bộ Gateway...")
        while True:
            keys = await self.redis.keys("livestatus:active:*")
            active_users = [int(k.split(":")[-1]) for k in keys]
            
            for user_id in active_users:
                if user_id not in self.active_sessions or self.active_sessions[user_id].closed:
                    asyncio.create_task(self.maintain_presence(user_id))
                    
            for user_id in list(self.active_sessions.keys()):
                if user_id not in active_users:
                    ws = self.active_sessions.pop(user_id)
                    if not ws.closed:
                        await ws.close()
                        
            await asyncio.sleep(60)
