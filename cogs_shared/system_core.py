import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from backend.database import EquinoxDatabase

class SystemCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    system_group = app_commands.Group(name="system", description="Lệnh quản trị hệ thống (Độc quyền Owner)")
    api_group = app_commands.Group(parent=system_group, name="api", description="Quản trị xoay tua API Key")
    key_group = app_commands.Group(parent=system_group, name="key", description="Quản trị Premium Key")

    async def check_owner(self, interaction: discord.Interaction) -> bool:
        owner_id = int(os.environ.get("OWNER_ID", 0))
        if interaction.user.id != owner_id:
            await interaction.response.send_message("❌ Từ chối truy cập. Kẻ ngoại đạo không có quyền chạm vào Nút Bấm Hạt Nhân.", ephemeral=True)
            return False
        return True

    @key_group.command(name="add", description="Tạo mã Premium Key mới")
    async def sys_add_key(self, interaction: discord.Interaction, duration_days: int):
        if not await self.check_owner(interaction): return
        token = await self.db.create_premium_key(duration_days)
        embed = discord.Embed(title="🔑 TẠO KEY THÀNH CÔNG", color=0x00FF00)
        embed.add_field(name="Mã Key", value=f"`{token}`", inline=False)
        embed.add_field(name="Thời hạn", value=f"{duration_days} ngày", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @key_group.command(name="list", description="Xem danh sách toàn bộ Premium Key")
    async def sys_key_list(self, interaction: discord.Interaction):
        if not await self.check_owner(interaction): return
        raw_keys = await self.bot.redis.hgetall("premium_keys")
        
        active_keys, available_keys = [], []
        for token, data_str in raw_keys.items():
            data = json.loads(data_str)
            if data["status"] == "available":
                available_keys.append(f"`{token}` ({data['duration']} ngày)")
            else:
                user_id = data["used_by"]
                expire_date = f"<t:{data['activated_at'] + data['duration'] * 86400}:R>"
                active_keys.append(f"`{token}` - <@{user_id}> - {expire_date}")

        embed = discord.Embed(title="📊 BẢNG THEO DÕI PREMIUM KEY", color=self.bot.theme_color)
        av_text = "\n".join(available_keys) if available_keys else "Không có key trống."
        ac_text = "\n".join(active_keys) if active_keys else "Không có key đang chạy."
        embed.add_field(name="🟢 Key Trống (Available)", value=av_text[:1024], inline=False)
        embed.add_field(name="🔴 Key Đang Hoạt Động (Used)", value=ac_text[:1024], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @key_group.command(name="delete", description="Xóa/Thu hồi Premium Key")
    async def sys_delete_key(self, interaction: discord.Interaction, token: str):
        if not await self.check_owner(interaction): return
        if not await self.bot.redis.hexists("premium_keys", token):
            await interaction.response.send_message("❌ Key không tồn tại trên hệ thống.", ephemeral=True)
            return
        await self.bot.redis.hdel("premium_keys", token)
        embed = discord.Embed(description=f"✅ Đã cưỡng chế thu hồi key `{token}` khỏi hệ thống.", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @api_group.command(name="add", description="Nạp API Key Google Gemini vào hệ thống")
    async def api_add(self, interaction: discord.Interaction, token_id: str, key_content: str):
        if not await self.check_owner(interaction): return
        payload = {"key_content": key_content, "status": "active", "fail_count": 0, "cooldown_until": 0}
        await self.bot.redis.hset("api_keys", token_id, json.dumps(payload))
        await interaction.response.send_message(f"✅ Đã nạp API Key `{token_id}` vào bể xoay tua thành công.", ephemeral=True)

    @api_group.command(name="list", description="Dashboard theo dõi sức khỏe API Key")
    async def api_list(self, interaction: discord.Interaction):
        if not await self.check_owner(interaction): return
        keys = await self.bot.redis.hgetall("api_keys")
        embed = discord.Embed(title="🌐 DASHBOARD SỨC KHỎE API", color=self.bot.theme_color)
        for token_id, data_str in keys.items():
            data = json.loads(data_str)
            status_emoji = "🟢" if data["status"] == "active" else "🟡" if data["status"] == "cooldown" else "🔴"
            details = f"Trạng thái: {status_emoji} {data['status'].upper()}\nLỗi liên tiếp: {data['fail_count']}"
            embed.add_field(name=f"Key: {token_id}", value=details, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @api_group.command(name="remove", description="Xóa API Key khỏi hệ thống")
    async def api_remove(self, interaction: discord.Interaction, token_id: str):
        if not await self.check_owner(interaction): return
        await self.bot.redis.hdel("api_keys", token_id)
        await interaction.response.send_message(f"✅ Đã xóa API Key `{token_id}` khỏi hệ thống.", ephemeral=True)

    @app_commands.command(name="redeem", description="Kích hoạt Premium Key của bạn")
    async def redeem_key(self, interaction: discord.Interaction, token: str):
        success = await self.db.redeem_premium_key(interaction.user.id, token)
        if success:
            embed = discord.Embed(title="🎉 KÍCH HOẠT THÀNH CÔNG", color=0x00FF00)
            embed.description = "Tài khoản của bạn đã được nâng cấp. Bạn đã mở khóa toàn bộ đặc quyền VIP."
        else:
            embed = discord.Embed(title="❌ KÍCH HOẠT THẤT BẠI", color=0xFF0000)
            embed.description = "Key không hợp lệ, đã được sử dụng hoặc đã hết hạn."
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SystemCore(bot))
