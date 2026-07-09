import discord
from discord.ext import commands
from ai_labs.persona_engine import AIEngine

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai = AIEngine(bot.redis)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Nếu bot được nhắc đến (mention)
        if self.bot.user in message.mentions:
            if self.bot.persona == "Butler": return # Butler ko chat

            clean_content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not clean_content: return

            async with message.channel.typing():
                # Truyền channel.id vào để kích hoạt Pub/Sub nếu dính lỗi 429
                reply = await self.ai.generate_response(
                    user_id=message.author.id,
                    user_message=clean_content,
                    persona=self.bot.persona,
                    channel_id=message.channel.id
                )

            await message.reply(reply)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
