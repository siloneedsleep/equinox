import random
import time
import json
from typing import Dict, Any

class EconomyEngine:
    def __init__(self, db):
        self.db = db

    async def open_star_pouch(self, user_id: int, current_persona: str) -> dict:
        # Thuật toán sinh số ngẫu nhiên từ 100 đến 100,000,000 Star
        amount = random.randint(100, 100000000)

        # Luminous: Tiền sạch (Aequor) | Tenebris: Tiền bẩn (Aequis)
        currency_type = "aequor" if current_persona == "Luminous" else "aequis"
        
        await self.db.update_currency(user_id, currency_type, amount)
        
        return {
            "amount": amount,
            "currency": currency_type,
            "persona": current_persona
        }

    async def launder_money(self, user_id: int, amount: int) -> dict:
        balance = await self.db.get_balance(user_id)
        current_dirty = balance["aequis"]

        if current_dirty < amount:
            return {"success": False, "reason": "Số dư Aequis không đủ để rửa."}

        # Tính phế ngẫu nhiên từ 15% – 25%
        fee_percent = random.randint(15, 25)
        fee_amount = int(amount * (fee_percent / 100))
        clean_amount = amount - fee_amount

        # Thực hiện trừ tiền bẩn, cộng tiền sạch và nộp quỹ gia đình
        await self.db.update_currency(user_id, "aequis", -amount)
        await self.db.update_currency(user_id, "aequor", clean_amount)
        await self.db.update_currency("system_family_fund", "aequor", fee_amount)

        return {
            "success": True,
            "clean_received": clean_amount,
            "fee_paid": fee_amount,
            "fee_percent": fee_percent
        }

    async def create_trade_session(self, user1_id: int, user2_id: int) -> str:
        # Session an toàn sống trong 5 phút
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
        # Logic ám sát
        balance = await self.db.get_balance(victim_id)
        victim_aequor = balance["aequor"]

        # Cướp 30% tài sản sạch
        stolen_amount = int(victim_aequor * 0.3)

        # Check di chúc
        spouse_id = await self.db.get_will(victim_id)
        will_triggered = False
        remaining_to_spouse = 0

        if spouse_id:
            will_triggered = True
            remaining_to_spouse = victim_aequor - stolen_amount
            # Chuyển 70% còn lại cho người phối ngẫu
            await self.db.update_currency(spouse_id, "aequor", remaining_to_spouse)
            await self.db.update_currency(victim_id, "aequor", -victim_aequor)
        else:
            # Nếu không có di chúc, 70% bị đóng băng (trừ sạch ví nạn nhân)
            await self.db.update_currency(victim_id, "aequor", -victim_aequor)

        # Thưởng cho sát thủ
        await self.db.update_currency(assassin_id, "aequis", stolen_amount)

        # Trích quỹ đen treo thưởng Bounty (Ví dụ 10% số tiền cướp được)
        bounty_amount = int(stolen_amount * 0.1)
        await self.db.redis.hincrby("bounties", str(assassin_id), bounty_amount)

        return {
            "stolen": stolen_amount,
            "will_triggered": will_triggered,
            "spouse_id": spouse_id,
            "bounty_posted": bounty_amount
        }
