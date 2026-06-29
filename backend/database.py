import json
import time
import uuid
from typing import Optional, List, Dict

class EquinoxDatabase:
    def __init__(self, redis_client):
        self.redis = redis_client

    # --- HỆ THỐNG PHÂN CẤP (LEVELS) ---
    async def get_user_level(self, user_id: int) -> int:
        level = await self.redis.hget(f"user:{user_id}", "level")
        return int(level) if level else 0

    async def set_user_level(self, user_id: int, level: int):
        await self.redis.hset(f"user:{user_id}", "level", level)

    # --- HỆ THỐNG PREMIUM KEYS ---
    async def create_premium_key(self, duration_days: int) -> str:
        # Nếu duration_days = -1 thì là Vĩnh viễn
        token = f"EQNX-VIP-{duration_days if duration_days > 0 else 'PERM'}D-{str(uuid.uuid4())[:8].upper()}"
        payload = {
            "duration": duration_days,
            "created_at": int(time.time()),
            "status": "available",
            "used_by": None
        }
        await self.redis.hset("premium_keys", token, json.dumps(payload))
        return token

    async def redeem_premium_key(self, user_id: int, token: str) -> bool:
        raw_data = await self.redis.hget("premium_keys", token)
        if not raw_data:
            return False
        
        key_data = json.loads(raw_data)
        if key_data["status"] != "available":
            return False
            
        key_data["status"] = "used"
        key_data["used_by"] = user_id
        key_data["activated_at"] = int(time.time())
        
        await self.redis.hset("premium_keys", token, json.dumps(key_data))
        
        # Cập nhật thời hạn cho User
        if key_data["duration"] == -1: # Vĩnh viễn
            new_expire = 2147483647 # Năm 2038 hoặc dùng flag đặc biệt
        else:
            current_expire = await self.redis.hget(f"user:{user_id}", "premium_until")
            base_time = int(current_expire) if current_expire and int(current_expire) > time.time() else int(time.time())
            new_expire = base_time + (key_data["duration"] * 86400)
        
        await self.redis.hset(f"user:{user_id}", "premium_until", new_expire)
        return True

    async def has_premium(self, user_id: int) -> bool:
        expire_time = await self.redis.hget(f"user:{user_id}", "premium_until")
        if not expire_time:
            return False
        return int(time.time()) < int(expire_time)

    # --- HỆ THỐNG KINH TẾ (ECONOMY) ---
    async def get_balance(self, user_id: int) -> Dict[str, int]:
        aequor = await self.redis.hget(f"user:{user_id}:economy", "aequor")
        aequis = await self.redis.hget(f"user:{user_id}:economy", "aequis")
        return {
            "aequor": int(aequor) if aequor else 0,
            "aequis": int(aequis) if aequis else 0
        }

    async def update_currency(self, user_id: str or int, currency_type: str, amount: int) -> int:
        # Hỗ trợ cả system_family_fund
        is_numeric = str(user_id).isdigit()
        key = f"user:{user_id}:economy" if isinstance(user_id, int) or is_numeric else f"system:{user_id}"
        return await self.redis.hincrby(key, currency_type, amount)

    # --- HỆ THỐNG TÚI ĐỒ (BAG) ---
    async def add_item_to_bag(self, user_id: int, item_type: str, item_data: dict):
        item_id = str(uuid.uuid4())
        payload = {
            "id": item_id,
            "type": item_type,
            "data": item_data,
            "acquired_at": int(time.time()),
            "is_equipped": False
        }
        await self.redis.hset(f"bag:{user_id}", item_id, json.dumps(payload))
        return item_id

    async def get_bag(self, user_id: int) -> Dict[str, dict]:
        items = await self.redis.hgetall(f"bag:{user_id}")
        return {k: json.loads(v) for k, v in items.items()}

    async def remove_item_from_bag(self, user_id: int, item_id: str):
        await self.redis.hdel(f"bag:{user_id}", item_id)

    # --- HỆ THỐNG PROFILE & PRESENCE ---
    async def save_custom_status(self, user_id: int, status_payload: dict):
        await self.redis.hset("custom_statuses", str(user_id), json.dumps(status_payload))

    async def get_custom_status(self, user_id: int) -> Optional[dict]:
        data = await self.redis.hget("custom_statuses", str(user_id))
        return json.loads(data) if data else None

    async def toggle_livestatus(self, user_id: int, state: bool):
        if state:
            await self.redis.set(f"livestatus:active:{user_id}", "1")
        else:
            await self.redis.delete(f"livestatus:active:{user_id}")

    # --- HỆ THỐNG DI CHÚC (WILLS) ---
    async def set_will(self, user_id: int, spouse_id: int):
        await self.redis.hset("underground_wills", str(user_id), str(spouse_id))

    async def get_will(self, user_id: int) -> Optional[int]:
        spouse_id = await self.redis.hget("underground_wills", str(user_id))
        return int(spouse_id) if spouse_id else None
