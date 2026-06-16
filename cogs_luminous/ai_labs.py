import discord
from discord.ext import commands
from discord import app_commands
import random

from config.settings import COLORS
from database.redis_client import get_redis_connection

class AILabs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # 🤖 1. ĐÚC BẢN THỂ AI TƯ NHÂN
    # ==========================================
    @commands.hybrid_command(name="ai-create", description="Đúc bản thể AI tư nhân bằng tiền sạch")
    async def ai_create(self, ctx):
        r = await get_redis_connection()
        user_key = f"equinox:user:{ctx.author.id}"
        
        cost = 100000  # Giá đúc AI mặc định
        clean_bal = int(await r.hget(user_key, "balance_clean") or 0)
        
        if clean_bal < cost:
            return await ctx.send(f"🚫 Từ chối giao dịch! Bạn cần ít nhất **{cost:,} Star** sạch để khởi tạo máy chủ AI riêng.", ephemeral=True)
            
        await r.hincrby(user_key, "balance_clean", -cost)
        await r.hset(user_key, "has_ai", "TRUE")
        
        embed = discord.Embed(title="🤖 ĐÚC AI TƯ NHÂN THÀNH CÔNG", color=COLORS["luminous_main"])
        embed.description = f"Tuyệt vời <@{ctx.author.id}>! Bản thể AI hộ mệnh của bạn đã được khởi chạy bằng **{cost:,} Star** sạch.\n\nHãy dùng lệnh `/ai-chat` để bắt đầu trò chuyện với hệ tri thức vô tận của Thần Điện!"
        await ctx.send(embed=embed)

    # ==========================================
    # 💬 2. TRÒ CHUYỆN VỚI AI
    # ==========================================
    @commands.hybrid_command(name="ai-chat", description="Trò chuyện với AI tư nhân của bạn")
    @app_commands.describe(message="Nội dung câu hỏi dành cho AI")
    async def ai_chat(self, ctx, *, message: str):
        r = await get_redis_connection()
        user_key = f"equinox:user:{ctx.author.id}"
        
        has_ai = await r.hget(user_key, "has_ai")
        if has_ai != "TRUE":
            return await ctx.send("🚫 Bạn chưa sở hữu AI tư nhân. Hãy dùng lệnh `/ai-create` để mua hạn ngạch máy chủ trước nhé!", ephemeral=True)
            
        # Tạm lập trình Mock (Giả lập) gọi API - Ông có thể chèn API Google Gemini vào đây
        responses = [
            "Ánh sáng sẽ dẫn đường cho bạn. Theo như tôi phân tích thì...",
            "Đó là một câu hỏi rất thú vị. Dưới góc nhìn văn minh của Thần Điện...",
            "Tôi luôn ở đây để bảo hộ trí tuệ cho bạn. Giải pháp tối ưu nhất là..."
        ]
        
        embed = discord.Embed(title="🤖 TRẠM AI LABS THẦN ĐIỆN", color=COLORS["luminous_info"])
        embed.add_field(name="Cư dân hỏi:", value=f"> {message}", inline=False)
        embed.add_field(name="Thiên sứ AI:", value=random.choice(responses) + "\n\n*(Chức năng gọi API Gemini Pro đang được cấu hình...)*", inline=False)
        embed.set_footer(text="Hệ thống trí tuệ nhân tạo Equinox Network")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AILabs(bot))
