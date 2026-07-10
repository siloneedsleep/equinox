import json
import redis.asyncio as redis
from config.settings import REDIS_URI

class KeyDBClient:
    def __init__(self):
        # Kết nối tới Redis Cloud / KeyDB dùng chung cho cả 2 Host
        self.redis = redis.from_url(REDIS_URI, decode_responses=True)

    async def get_couple_data(self, user_id: str):
        data = await self.redis.get(f"couple:{user_id}")
        return json.loads(data) if data else None

    async def set_couple_data(self, user_id: str, data: dict):
        await self.redis.set(f"couple:{user_id}", json.dumps(data))

    async def publish_event(self, channel: str, message: str):
        """Bắn tín hiệu Pub/Sub để đồng bộ giữa Render và Wispbyte"""
        await self.redis.publish(channel, message)

    async def subscribe_channel(self, channel: str):
        """Đăng ký lắng nghe tín hiệu Pub/Sub"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def sync_oauth_session(self, user_id: str, token_data: dict):
        """Lưu nhanh dữ liệu Token OAuth2 vào Redis (Dành cho FastAPI)"""
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(f"oauth:{user_id}", json.dumps(token_data))
            # Session hết hạn sau 1 giờ nếu user không thiết lập lệnh status
            pipe.expire(f"oauth:{user_id}", 3600)
            await pipe.execute()
            
    async def close(self):
        await self.redis.aclose()
