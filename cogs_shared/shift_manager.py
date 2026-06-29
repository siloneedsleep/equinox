import discord
from discord.ext import commands, tasks
import json
import datetime
import pytz
from config.settings import LUMINOUS_SHIFT_START, TENEBRIS_SHIFT_START

class ShiftManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        self.check_shift.start()

    def cog_unload(self):
        self.check_shift.cancel()

    @tasks.loop(minutes=1)
    async def check_shift(self):
        # Chỉ bot Luminous làm nhiệm vụ điều phối thời gian để tránh lặp tín hiệu
        if self.bot.persona != "Luminous":
            return

        now = datetime.datetime.now(self.timezone)
        current_time = now.strftime("%H:%M")

        target_persona = None
        if current_time == LUMINOUS_SHIFT_START:
            target_persona = "Luminous"
        elif current_time == TENEBRIS_SHIFT_START:
            target_persona = "Tenebris"

        if target_persona:
            payload = {
                "action": "shift_change",
                "active_persona": target_persona,
                "timestamp": now.isoformat()
            }
            await self.bot.redis.publish("equinox_system", json.dumps(payload))
            print(f"[Shift Manager] Đã bắn tín hiệu giao ca: {target_persona}")

    @check_shift.before_loop
    async def before_check_shift(self):
        await self.bot.wait_until_ready()
        # Xác định ca trực hiện tại ngay khi khởi động
        now = datetime.datetime.now(self.timezone)
        hour = now.hour

        current_persona = "Luminous" if 6 <= hour < 18 else "Tenebris"

        payload = {
            "action": "shift_change",
            "active_persona": current_persona,
            "timestamp": now.isoformat()
        }
        # Tự gửi cho chính mình và các bot khác qua Redis
        await self.bot.redis.publish("equinox_system", json.dumps(payload))

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))
