import discord
from discord.ext import commands
from discord import app_commands
from backend.database import KeyDBClient
from config.settings import OWNER_ID

class UpdateNoteModal(discord.ui.Modal, title="Cập Nhật Ghi Chú Hệ Thống"):
    note_input = discord.ui.TextInput(
        label="Nội dung ghi chú mới",
        style=discord.TextStyle.long,
        placeholder="Nhập ghi chú cho Luminous/Tenebris...",
        max_length=500
    )

    def __init__(self, db: KeyDBClient):
        super().__init__()
        self.db = db

    async def on_submit(self, interaction: discord.Interaction):
        await self.db.redis.set("system:bot_note", self.note_input.value)
        await interaction.response.send_message("✅ Đã cập nhật ghi chú thành công!", ephemeral=True)

class OwnerDashboardView(discord.ui.View):
    def __init__(self, db: KeyDBClient):
        super().__init__(timeout=None)
        self.db = db

    @discord.ui.button(label="Restart Cụm Economy", style=discord.ButtonStyle.danger, row=0)
    async def restart_economy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.db.publish_event("quangia:command", "restart_wispbyte")
        await interaction.response.send_message("Đã gửi lệnh ép Restart cụm Wispbyte!", ephemeral=True)

    @discord.ui.button(label="Đổi Ca Bot Tay", style=discord.ButtonStyle.primary, row=0)
    async def shift_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.db.publish_event("quangia:command", "shift_persona")
        await interaction.response.send_message("Đã gửi lệnh ép hoán đổi Luminous/Tenebris!", ephemeral=True)

    @discord.ui.button(label="Chỉnh sửa Note", style=discord.ButtonStyle.secondary, row=1)
    async def edit_note(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UpdateNoteModal(self.db))

    @discord.ui.button(label="Pause Proxy", style=discord.ButtonStyle.secondary, row=1)
    async def pause_proxy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.db.publish_event("presence:sync:events", "pause")
        await interaction.response.send_message("Đã tạm dừng Proxy Status.", ephemeral=True)

class QuanGiaCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = KeyDBClient()

    # LỆNH OWNER TỐI CAO
    @commands.hybrid_command(name="owner", description="Mở bảng điều khiển trạm chỉ huy Equinox")
    async def owner_dashboard(self, ctx: commands.Context):
        if ctx.author.id != OWNER_ID:
            return await ctx.send("🚫 Bạn không có quyền truy cập Bảng điều khiển tối cao.", ephemeral=True)

        note = await self.db.redis.get("system:bot_note") or "Không có ghi chú nào."
        
        embed = discord.Embed(title="🪐 QUẢN GIA EQUINOX — TRẠM ĐIỀU KHIỂN", color=discord.Color.dark_embed())
        embed.add_field(name="Trạng Thái Host", value="🟢 Render (Quản Gia)\n🟢 Wispbyte (Economy)", inline=False)
        embed.add_field(name="Ghi chú hệ thống", value=f"```\n{note}\n```", inline=False)
        
        await ctx.send(embed=embed, view=OwnerDashboardView(self.db), ephemeral=True)

    # LỆNH BYPASS (MIỄN TRỪ)
    @commands.hybrid_command(name="bypass", description="Miễn trừ kỷ luật cho ID/Ping chỉ định")
    async def bypass(self, ctx: commands.Context, target_id: str):
        if ctx.author.id != OWNER_ID:
            return await ctx.send("🚫 Lệnh từ chối.", ephemeral=True)
            
        target_id_clean = target_id.strip("<@!&>")
        await self.db.redis.sadd("guangia:bypass_list", target_id_clean)
        await ctx.send(f"✅ Đã thêm {target_id} vào danh sách miễn trừ Bypass.", ephemeral=True)

    # LỆNH SETUP ROLE
    @commands.hybrid_command(name="role_bot_setup", description="Thiết lập quyền kế thừa cho Role")
    @app_commands.describe(level="Cấp độ từ 0 đến 3", role="Role được gán", command_ids="Danh sách ID lệnh (cách nhau bằng phẩy)")
    async def role_bot_setup(self, ctx: commands.Context, level: int, role: discord.Role, command_ids: str):
        if ctx.author.id != OWNER_ID:
            return await ctx.send("🚫 Lệnh từ chối.", ephemeral=True)
            
        await self.db.redis.hset(f"role_inheritance:level_{level}", role.id, command_ids)
        await ctx.send(f"✅ Đã cấu hình {role.mention} ở Level {level} với các lệnh: {command_ids}", ephemeral=True)

    # LỆNH HELP (Dạng Text Tường Minh - Hybrid)
    @commands.hybrid_command(name="help", description="Hiển thị cẩm nang vận hành Quản Gia Equinox")
    async def text_help(self, ctx: commands.Context):
        embed = discord.Embed(title="🪐 CẨM NANG VẬN HÀNH QUẢN GIA EQUINOX", color=discord.Color.blue())
        embed.description = "**Prefix hệ thống:** `q!`\n\n**🛡️ Nhóm Quản Trị (Level 3, 4)**\n`/owner` - Bảng điều khiển tối cao\n`/role_bot_setup` - Cấu hình quyền kế thừa\n`/bypass` - Danh sách miễn trừ\n\n**🖥️ Nhóm Treo Máy (Level 2+)**\n`/status add` - Đổi đèn Status\n`/livestatus` - Kích hoạt WebSocket 24/7\n`/voice247` - Treo Bot phòng Voice\n\n**🚨 Nhóm An Ninh (Level 1+)**\n`/mrbeast` - Đặt vùng tử địa chống Raider"
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QuanGiaCore(bot))
