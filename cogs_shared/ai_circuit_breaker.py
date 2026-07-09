import discord
from discord.ext import commands
import json

class CircuitBreaker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_system_event(self, data: dict):
        event_type = data.get("event")
        if event_type == "ai_rate_limit_429":
            failed_persona = data.get("failed_persona")
            channel_id = data.get("channel_id")
            user_id = data.get("user_id")
            user_message = data.get("user_message")

            # Chỉ bot đang CHƯA quá tải mới nhảy vào chửi/cứu
            if self.bot.persona != "Butler" and self.bot.persona != failed_persona:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.bot.fetch_channel(channel_id)
                    except:
                        return

                if failed_persona == "Luminous" and self.bot.persona == "Tenebris":
                    await channel.send("💀 **[Hệ thống can thiệp]** *Chậc... Có vẻ như cái đứa hoàng gia ẻo lả Luminous kia vừa bị hụt hơi cmnr (Lỗi 429 API). Lùi ra sau đi, Tenebris tao sẽ tiếp quản cái mớ lộn xộn này!*")
                elif failed_persona == "Tenebris" and self.bot.persona == "Luminous":
                    await channel.send("✨ **[Hệ thống can thiệp]** *Xin thứ lỗi cho sự thô lỗ của Tenebris, có vẻ hắn đã kiệt sức vì thiếu kỷ luật (Lỗi 429 API). Luminous tôi sẽ thanh lịch tiếp quản cuộc trò chuyện này.*")

                # Tiếp quản request và trả lời luôn cho mượt
                if user_id and user_message:
                    ai_cog = self.bot.get_cog("AIChat")
                    if ai_cog:
                        async with channel.typing():
                            reply = await ai_cog.ai.generate_response(
                                user_id=user_id,
                                user_message=user_message,
                                persona=self.bot.persona,
                                channel_id=channel_id
                            )
                        await channel.send(f"<@{user_id}> {reply}")

async def setup(bot):
    await bot.add_cog(CircuitBreaker(bot))
