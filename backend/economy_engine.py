import json
from backend.database import KeyDBClient

class EconomyEngine:
    def __init__(self):
        self.db = KeyDBClient()

    async def launder_money(self, user_id: str, amount: int) -> dict:
        """Rửa tiền bằng Redis Transaction (MULTI/EXEC) chống Race Condition (Trùng lặp giao dịch)"""
        aequis_key = f"wallet:aequis:{user_id}"
        aequor_key = f"wallet:aequor:{user_id}"
        family_fund_key = "wallet:family_fund"

        # Phí rửa tiền 20%
        fee = int(amount * 0.20)
        clean_amount = amount - fee

        async with self.db.redis.pipeline(transaction=True) as pipe:
            try:
                # Theo dõi số dư tiền bẩn khóa giao dịch
                await pipe.watch(aequis_key)
                current_aequis = int(await pipe.get(aequis_key) or 0)
                
                if current_aequis < amount:
                    await pipe.unwatch()
                    return {"status": "error", "message": "Bạn không có đủ tiền bẩn (Aequis) để rửa!"}

                # Thực thi Atomic nguyên khối
                pipe.multi()
                pipe.decrby(aequis_key, amount)
                pipe.incrby(aequor_key, clean_amount)
                pipe.incrby(family_fund_key, fee)
                await pipe.execute()
                
                return {"status": "success", "clean_amount": clean_amount, "fee": fee}
            except Exception as e:
                return {"status": "error", "message": "Giao dịch quá tải, vui lòng thử lại sau."}

    async def execute_assassination(self, killer_id: str, victim_id: str) -> dict:
        """Xử lý ám sát và tự động kích hoạt Di Chúc Ngầm (Fail-safe Wills)"""
        victim_aequor_key = f"wallet:aequor:{victim_id}"
        killer_aequor_key = f"wallet:aequor:{killer_id}"

        async with self.db.redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(victim_aequor_key)
                victim_balance = int(await pipe.get(victim_aequor_key) or 0)
                
                if victim_balance <= 0:
                    await pipe.unwatch()
                    return {"status": "error", "message": "Mục tiêu quá nghèo, không có tài sản sạch để cướp."}

                pipe.multi()
                
                # Sát thủ cướp 30% tài sản
                stolen_amount = int(victim_balance * 0.3)
                pipe.decrby(victim_aequor_key, stolen_amount)
                pipe.incrby(killer_aequor_key, stolen_amount)

                # KÍCH HOẠT DI CHÚC NGẦM: Chuyển 70% còn lại cho vợ/chồng nếu có
                spouse_id = await self.db.redis.get(f"couple:{victim_id}")
                if spouse_id:
                    remaining_amount = victim_balance - stolen_amount
                    spouse_aequor_key = f"wallet:aequor:{spouse_id}"
                    
                    # Dịch chuyển tài sản an toàn
                    pipe.decrby(victim_aequor_key, remaining_amount)
                    pipe.incrby(spouse_aequor_key, remaining_amount)
                    
                await pipe.execute()
                
                return {
                    "status": "success", 
                    "stolen": stolen_amount, 
                    "will_activated": bool(spouse_id),
                    "spouse_id": spouse_id
                }
            except Exception as e:
                return {"status": "error", "message": "Giao dịch không thành công do tắc nghẽn."}
