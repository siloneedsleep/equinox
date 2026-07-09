import asyncio
import pytz
import json
from datetime import datetime


class PersonaScheduler:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.tz = pytz.timezone("Asia/Ho_Chi_Minh")
        self.is_running = False

    async def start(self):
        self.is_running = True
        asyncio.create_task(self.schedule_loop())

    async def stop(self):
        self.is_running = False

    def get_current_shift(self) -> str:
        now = datetime.now(self.tz)
        if 6 <= now.hour < 18:
            return "luminous"
        return "tenebris"

    async def schedule_loop(self):
        """
        Background loop optimized for atomic transitions.
        Wakes up periodically, checks if the shift has changed compared to KeyDB.
        """
        while self.is_running:
            try:
                expected_shift = self.get_current_shift()
                current_shift = await self.redis.get("equinox_active_persona")

                if current_shift != expected_shift:
                    # Atomic write
                    await self.redis.set("equinox_active_persona", expected_shift)
                    print(f"[Scheduler] 🔄 Chuyển giao ca trực sang: {expected_shift.upper()}")

                    # Fire Pub/Sub Event so Bot instances immediately transition
                    await self.redis.publish("equinox_system", json.dumps({
                        "event": "shift_change",
                        "active_persona": expected_shift
                    }))
            except Exception as e:
                print(f"[Scheduler] Lỗi vòng lặp: {e}")

            # Align sleep roughly to the top of the next minute to avoid constant spinning,
            # but keep it responsive enough. Sleep for 30s is perfectly fine for this.
            await asyncio.sleep(30)
