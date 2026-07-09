import random
import time
import json
import redis.asyncio as redis

class EconomyEngine:
    def __init__(self, db):
        self.db = db

    async def open_star_pouch(self, user_id: int, current_persona: str) -> dict:
        amount = random.randint(100, 100000000)
        currency_type = "aequor" if current_persona == "Luminous" else "aequis"
        await self.db.update_currency(user_id, currency_type, amount)
        
        return {
            "amount": amount,
            "currency": currency_type,
            "persona": current_persona
        }

    async def launder_money(self, user_id: int, amount: int) -> dict:
        fee_percent = random.randint(15, 25)
        fee_amount = int(amount * (fee_percent / 100))
        clean_amount = amount - fee_amount

        # STRICT ATOMIC REDIS TRANSACTION using proper HASH keys from database.py
        try:
            async with self.db.redis.pipeline(transaction=True) as pipe:
                while True:
                    try:
                        # WATCH the user's economy hash
                        await pipe.watch(f"user:{user_id}:economy")
                        current_dirty_bytes = await pipe.hget(f"user:{user_id}:economy", "aequis")
                        current_dirty = int(current_dirty_bytes) if current_dirty_bytes else 0

                        if current_dirty < amount:
                            await pipe.unwatch()
                            return {"success": False, "reason": "Số dư Aequis không đủ để rửa."}

                        pipe.multi()
                        # Deduct dirty
                        pipe.hincrby(f"user:{user_id}:economy", "aequis", -amount)
                        # Add clean
                        pipe.hincrby(f"user:{user_id}:economy", "aequor", clean_amount)
                        # Add to family fund (system namespace)
                        pipe.hincrby("system:system_family_fund", "aequor", fee_amount)
                        await pipe.execute()
                        break
                    except redis.WatchError:
                        # Value changed during watch, retry
                        continue
        except Exception as e:
            return {"success": False, "reason": f"Lỗi giao dịch: {e}"}

        return {
            "success": True,
            "clean_received": clean_amount,
            "fee_paid": fee_amount,
            "fee_percent": fee_percent
        }

    async def create_trade_session(self, user1_id: int, user2_id: int) -> str:
        session_id = f"trade:{user1_id}:{user2_id}:{int(time.time())}"
        payload = {
            "user1": {"id": user1_id, "offer": {"aequor": 0, "aequis": 0, "items": []}, "confirmed": False},
            "user2": {"id": user2_id, "offer": {"aequor": 0, "aequis": 0, "items": []}, "confirmed": False},
            "status": "pending",
            "created_at": int(time.time())
        }
        await self.db.redis.setex(f"session:{session_id}", 300, json.dumps(payload))
        return session_id

    async def process_assassination(self, assassin_id: int, victim_id: int) -> dict:
        spouse_id = await self.db.get_will(victim_id)
        will_triggered = False
        remaining_to_spouse = 0
        stolen_amount = 0
        bounty_amount = 0

        # STRICT ATOMIC REDIS TRANSACTION
        try:
            async with self.db.redis.pipeline(transaction=True) as pipe:
                while True:
                    try:
                        await pipe.watch(f"user:{victim_id}:economy")
                        victim_aequor_bytes = await pipe.hget(f"user:{victim_id}:economy", "aequor")
                        victim_aequor = int(victim_aequor_bytes) if victim_aequor_bytes else 0

                        if victim_aequor <= 0:
                            await pipe.unwatch()
                            return {"success": False, "reason": "Nạn nhân không có tài sản sạch để cướp."}

                        stolen_amount = int(victim_aequor * 0.3)
                        pipe.multi()

                        if spouse_id:
                            will_triggered = True
                            remaining_to_spouse = victim_aequor - stolen_amount
                            pipe.hincrby(f"user:{spouse_id}:economy", "aequor", remaining_to_spouse)
                            pipe.hincrby(f"user:{victim_id}:economy", "aequor", -victim_aequor)
                        else:
                            pipe.hincrby(f"user:{victim_id}:economy", "aequor", -victim_aequor)

                        pipe.hincrby(f"user:{assassin_id}:economy", "aequis", stolen_amount)

                        bounty_amount = int(stolen_amount * 0.1)
                        pipe.hincrby("bounties", str(assassin_id), bounty_amount)

                        await pipe.execute()
                        break
                    except redis.WatchError:
                        continue
        except Exception as e:
             return {"success": False, "reason": f"Lỗi giao dịch: {e}"}

        return {
            "success": True,
            "stolen": stolen_amount,
            "will_triggered": will_triggered,
            "spouse_id": spouse_id,
            "bounty_posted": bounty_amount
        }
