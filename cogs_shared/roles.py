import discord
from discord.ext import commands
import json
from cogs_shared.embed_util import create_premium_embed

class PickRoleModal(discord.ui.Modal, title='Tạo Bảng Chọn Role'):
    options = discord.ui.TextInput(
        label='Cấu hình (Mỗi dòng 1 role)',
        style=discord.TextStyle.paragraph,
        placeholder='Ví dụ:\n🔴: @Gamer\n🔵: @Developer',
        required=True
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        raw_text = self.options.value
        lines = raw_text.split('\n')

        mapping = {}
        desc_lines = []

        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                emoji = parts[0].strip()
                role_str = parts[1].strip()

                # Cố gắng bóc tách Role ID (e.g. <@&123456789>)
                role_id_str = ''.join(filter(str.isdigit, role_str))
                if role_id_str:
                    mapping[emoji] = int(role_id_str)
                    desc_lines.append(f"{emoji} : {role_str}")

        if not mapping:
            await interaction.followup.send("❌ Sai định dạng! Vui lòng dùng format: `Emoji: @Role`")
            return

        embed = create_premium_embed(
            title="🏷️ BẢNG CHỌN ROLE TỰ ĐỘNG",
            description="Hãy nhấn vào các Emoji bên dưới để nhận Role tương ứng nhé:\n\n" + "\n".join(desc_lines),
            color=0x9b59b6
        )

        msg = await interaction.channel.send(embed=embed)
        for emoji in mapping.keys():
            try:
                await msg.add_reaction(emoji)
            except discord.HTTPException:
                pass # Emoji lỗi

        # Persist to KeyDB
        db_key = f"equinox_roles_{msg.id}"
        await self.bot.redis.set(db_key, json.dumps(mapping))

        await interaction.followup.send("✅ Khởi tạo thành công!")

class RoleSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="role-setup", description="Tạo bảng lấy role tự động qua Emoji (Admin/Level 2+)")
    @discord.app_commands.default_permissions(manage_roles=True)
    async def role_setup(self, interaction: discord.Interaction):
        modal = PickRoleModal(self.bot)
        await interaction.response.send_modal(modal)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id: return

        db_key = f"equinox_roles_{payload.message_id}"
        mapping_str = await self.bot.redis.get(db_key)
        if not mapping_str: return

        mapping = json.loads(mapping_str)
        emoji_name = str(payload.emoji)

        if emoji_name in mapping:
            role_id = mapping[emoji_name]
            guild = self.bot.get_guild(payload.guild_id)
            if guild:
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        db_key = f"equinox_roles_{payload.message_id}"
        mapping_str = await self.bot.redis.get(db_key)
        if not mapping_str: return

        mapping = json.loads(mapping_str)
        emoji_name = str(payload.emoji)

        if emoji_name in mapping:
            role_id = mapping[emoji_name]
            guild = self.bot.get_guild(payload.guild_id)
            if guild:
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    try:
                        await member.remove_roles(role)
                    except discord.Forbidden:
                        pass

async def setup(bot):
    await bot.add_cog(RoleSystem(bot))
