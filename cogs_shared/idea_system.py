import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from backend.database import EquinoxDatabase
from config.settings import OWNER_ID

class IdeaReviewModal(discord.ui.Modal, title="Chỉnh Sửa Ý Tưởng"):
    content = discord.ui.TextInput(label="Nội dung ý tưởng", style=discord.TextStyle.paragraph)
    def __init__(self, db, idea_id, old_content):
        super().__init__()
        self.db = db
        self.idea_id = idea_id
        self.content.default = old_content
    async def on_submit(self, interaction: discord.Interaction):
        await self.db.update_idea(self.idea_id, {"content": self.content.value})
        await interaction.response.send_message(f"✅ Đã cập nhật ý tưởng `{self.idea_id}`", ephemeral=True)

class IdeaMagicView(discord.ui.View):
    def __init__(self, bot, ideas):
        super().__init__(timeout=300)
        self.bot = bot
        self.ideas = ideas
        self.selected_ideas = []

        options = [discord.SelectOption(label="LẤY TẤT CẢ Ý TƯỞNG", value="all", emoji="🌟")]
        for idea in ideas[:24]: # Discord limit 25 options
            label = idea['content'][:50] + "..." if len(idea['content']) > 50 else idea['content']
            options.append(discord.SelectOption(label=label, value=idea['id'], description=f"ID: {idea['id']}"))

        self.select = discord.ui.Select(placeholder="Chọn ý tưởng để thực hiện...", options=options, min_values=1, max_values=len(options))
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        if "all" in self.select.values:
            self.selected_ideas = self.ideas
        else:
            self.selected_ideas = [i for i in self.ideas if i['id'] in self.select.values]

        embed = discord.Embed(title="📝 XÁC NHẬN THỰC HIỆN Ý TƯỞNG", color=0xF1C40F)
        text = "\n".join([f"• `{i['id']}`: {i['content'][:100]}" for i in self.selected_ideas])
        embed.description = f"Bạn đã chọn **{len(self.selected_ideas)}** ý tưởng.\n\n{text}"

        view = discord.ui.View()
        btn_start = discord.ui.Button(label="Bắt đầu thực hiện", style=discord.ButtonStyle.success, emoji="🚀")
        btn_start.callback = self.start_execution
        btn_cancel = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.danger)
        btn_cancel.callback = lambda i: i.response.edit_message(content="❌ Đã hủy thao tác.", embed=None, view=None)

        view.add_item(btn_start)
        view.add_item(btn_cancel)
        await interaction.response.edit_message(embed=embed, view=view)

    async def start_execution(self, interaction: discord.Interaction):
        total = len(self.selected_ideas)
        embed = discord.Embed(title="🛠️ JULES ĐANG THI CÔNG...", color=0x3498DB)
        await interaction.response.edit_message(embed=embed, view=None)

        jules_cog = self.bot.get_cog("JulesControl")

        for i, idea in enumerate(self.selected_ideas, 1):
            progress = i / total
            bar = "🟩" * int(progress * 10) + "⬜" * (10 - int(progress * 10))
            embed.description = f"Đang xử lý: **{idea['content'][:100]}**\n\nTiến độ: [{bar}] **{i}/{total}**"
            await interaction.edit_original_response(embed=embed)

            # Triệu hồi Jules Brain thực thi
            if jules_cog:
                prompt = f"Thực thi ý tưởng phát triển sau cho Equinox Network V2: {idea['content']}"
                await jules_cog.jules_brain_process(prompt)
            else:
                await asyncio.sleep(2)

            await self.db.update_idea(idea['id'], {"status": "completed"})

        embed.title = "✅ HOÀN TẤT THI CÔNG"
        embed.description = f"Jules đã thực hiện xong **{total}** ý tưởng. Hệ thống đã được cập nhật."
        embed.color = 0x2ECC71
        await interaction.edit_original_response(embed=embed)

class IdeaSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    @app_commands.command(name="log", description="[Owner] Thiết lập kênh Log ý tưởng")
    async def set_log(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.user.id != OWNER_ID: return
        await self.db.set_log_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(f"✅ Đã gắn kênh log: {channel.mention}", ephemeral=True)

    @app_commands.command(name="idea", description="Gửi ý tưởng phát triển cho Equinox Network")
    async def send_idea(self, interaction: discord.Interaction, content: str):
        idea_id = await self.db.add_idea(interaction.user.id, content)

        embed = discord.Embed(title="💡 Ý TƯỞNG MỚI", color=0x9B59B6)
        embed.add_field(name="ID", value=f"`{idea_id}`", inline=True)
        embed.add_field(name="Người gửi", value=interaction.user.mention, inline=True)
        embed.add_field(name="Nội dung", value=content, inline=False)

        log_cid = await self.db.get_log_channel(interaction.guild_id)
        if log_cid:
            channel = self.bot.get_channel(log_cid)
            if channel: await channel.send(embed=embed)

        await interaction.response.send_message(f"✅ Cảm ơn! Ý tưởng của bạn đã được ghi nhận (Mã: `{idea_id}`).", ephemeral=True)

    @app_commands.command(name="xemxet", description="[Owner] Duyệt hoặc sửa ý tưởng")
    async def review_idea(self, interaction: discord.Interaction, idea_id: str, action: str):
        if interaction.user.id != OWNER_ID: return
        # action: "accept", "reject", "edit"
        idea = await self.db.get_idea(idea_id)
        if not idea: return await interaction.response.send_message("❌ Không tìm thấy ID.", ephemeral=True)

        if action == "accept":
            await self.db.update_idea(idea_id, {"status": "accepted"})
            await interaction.response.send_message(f"✅ Đã DUYỆT ý tưởng `{idea_id}`")
        elif action == "reject":
            await self.db.update_idea(idea_id, {"status": "rejected"})
            await interaction.response.send_message(f"❌ Đã TỪ CHỐI ý tưởng `{idea_id}`")
        elif action == "edit":
            await interaction.response.send_modal(IdeaReviewModal(self.db, idea_id, idea['content']))

    @app_commands.command(name="magic", description="[Owner] Triệu hồi Jules thực thi ý tưởng")
    async def magic(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID: return
        accepted_ideas = await self.db.get_accepted_ideas()
        if not accepted_ideas:
            return await interaction.response.send_message("📭 Không có ý tưởng nào đang chờ thực hiện.", ephemeral=True)

        embed = discord.Embed(title="🪄 EQUINOX MAGIC INTERFACE", description="Chọn các ý tưởng bạn muốn Jules thực hiện ngay bây giờ.", color=0x9B59B6)
        await interaction.response.send_message(embed=embed, view=IdeaMagicView(self.bot, accepted_ideas), ephemeral=True)

async def setup(bot):
    await bot.add_cog(IdeaSystem(bot))
