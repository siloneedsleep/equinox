import os
import json
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
from database.redis_client import get_redis_connection

# FIX LỖI 10: Validate early API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY không được set trong .env")
genai.configure(api_key=api_key)

class CelestialAIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    @app_commands.command(name="chat", description="Trò chuyện cùng Luminous / Tenebris AI")
    async def ai_chat(self, interaction: discord.Interaction, tin_nhan: str):
        await interaction.response.defer()
        r = await get_redis_connection()
        user_id = str(interaction.user.id)
        
        # FIX LỖI 6: Xóa .decode('utf-8') vì redis_client đã set decode_responses=True
        cycle = (await r.hget("equinox:system:config", "current_cycle")) or "DAY"

        if cycle == "DAY":
            system_instruction = "Bạn là Luminous. Dịu dàng, tích cực, xưng 'Em', gọi 'Sếp'."
            embed_color = 0xFFD700
        else:
            system_instruction = "Bạn là Tenebris. Cục súc, khịa, xưng 'Ta', gọi 'Ngươi'."
            embed_color = 0x4B0082

        try:
            response = await self.bot.loop.run_in_executor(
                None, lambda: self.model.generate_content(f"{system_instruction}\nUser: {tin_nhan}")
            )
            ai_reply = response.text
        except Exception as e:
            ai_reply = f"🚨 *Lỗi AI:* {e}"

        embed = discord.Embed(description=ai_reply, color=embed_color)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CelestialAIChat(bot))
