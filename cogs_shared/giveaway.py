import discord
from discord.ext import commands, tasks
import json
import time
import asyncio
import random
from typing import Optional
from cogs_shared.embed_util import create_premium_embed

class GiveawayModal(discord.ui.Modal, title='Tạo Giveaway'):
    description = discord.ui.TextInput(
        label='Mô tả (Rules, Yêu cầu,...)',
        style=discord.TextStyle.paragraph,
        placeholder='Nhập chi tiết về giveaway này...',
        required=True,
        max_length=1000
    )

    def __init__(self, bot, title_prize: str, end_time: int, winners: int, role: Optional[discord.Role]):
        super().__init__()
        self.bot = bot
        self.title_prize = title_prize
        self.end_time = end_time
        self.winners = winners
        self.role = role

    async def on_submit(self, interaction: discord.Interaction):
        desc = self.description.value
        if self.role:
            desc += f"\n\n**Yêu cầu:** Phải có role {self.role.mention}"

        embed = create_premium_embed(
            title=f"🎉 GIVEAWAY: {self.title_prize}",
            description=f"{desc}\n\nNhấn phản ứng 🎉 để tham gia!\n\n**Số giải:** {self.winners}\n**Kết thúc:** <t:{self.end_time}:R> (<t:{self.end_time}:f>)\n**Host:** {interaction.user.mention}",
            color=0x2ecc71
        )

        await interaction.response.send_message("Đang khởi tạo Giveaway...", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🎉")

        # Lưu vào KeyDB
        gw_data = {
            "channel_id": interaction.channel_id,
            "message_id": msg.id,
            "end_time": self.end_time,
            "prize": self.title_prize,
            "winners": self.winners,
            "host_id": interaction.user.id,
            "req_role_id": self.role.id if self.role else None,
            "desc": desc
        }
        await self.bot.redis.hset("equinox_giveaways", msg.id, json.dumps(gw_data))
        await interaction.edit_original_response(content="✅ Đã tạo Giveaway thành công!")

class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    def parse_duration(self, duration_str: str) -> int:
        units = {"m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration_str[-1].lower()
            val = int(duration_str[:-1])
            if unit in units:
                return val * units[unit]
        except:
            pass
        return 60 # Default 1 phút nếu lỗi

    @discord.app_commands.command(name="giveaway", description="Tạo Giveaway mới (Admin/Level 2+)")
    @discord.app_commands.default_permissions(manage_events=True)
    async def gw_create(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: int = 1,
        role: discord.Role = None
    ):
        seconds = self.parse_duration(duration)
        end_time = int(time.time()) + seconds

        modal = GiveawayModal(self.bot, prize, end_time, winners, role)
        await interaction.response.send_modal(modal)

    @tasks.loop(seconds=15)
    async def check_giveaways(self):
        try:
            giveaways = await self.bot.redis.hgetall("equinox_giveaways")
            now = int(time.time())

            for msg_id_str, gw_json in giveaways.items():
                gw_data = json.loads(gw_json)

                if now >= gw_data["end_time"]:
                    # Hết hạn -> Quay thưởng
                    await self.end_giveaway(int(msg_id_str), gw_data)
                    await self.bot.redis.hdel("equinox_giveaways", msg_id_str)
        except Exception as e:
            print(f"[Giveaway] Lỗi vòng lặp: {e}")

    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def end_giveaway(self, message_id: int, gw_data: dict):
        try:
            channel = self.bot.get_channel(gw_data["channel_id"])
            if not channel:
                channel = await self.bot.fetch_channel(gw_data["channel_id"])

            msg = await channel.fetch_message(message_id)

            # Khắc phục lỗi tìm Reaction: Phải lấy theo .emoji (dù là custom hay default)
            target_reaction = None
            for r in msg.reactions:
                if str(r.emoji) == "🎉":
                    target_reaction = r
                    break

            users = []
            if target_reaction:
                async for user in target_reaction.users():
                    if user.bot: continue
                    # Lọc theo Role nếu có
                    if gw_data.get("req_role_id"):
                        member = msg.guild.get_member(user.id)
                        if member and any(r.id == gw_data["req_role_id"] for r in member.roles):
                            users.append(user)
                    else:
                        users.append(user)

            if not users:
                fail_embed = create_premium_embed(
                    title="GIVEAWAY KẾT THÚC",
                    description=f"Không có ai tham gia hợp lệ cho phần thưởng **{gw_data['prize']}**.",
                    color=0xe74c3c
                )
                await msg.edit(embed=fail_embed)
                await channel.send(f"❌ Không có ai trúng giải Giveaway **{gw_data['prize']}**.")
                return

            winners_count = min(gw_data["winners"], len(users))
            winners = random.sample(users, winners_count)
            winner_mentions = ", ".join(w.mention for w in winners)

            # 1. Edit original message
            win_embed = create_premium_embed(
                title="🎉 GIVEAWAY ĐÃ KẾT THÚC 🎉",
                description=f"**Phần thưởng:** {gw_data['prize']}\n**Người trúng giải:** {winner_mentions}",
                color=0xf1c40f
            )
            await msg.edit(embed=win_embed)

            # 2. In-place announcement
            await channel.send(f"Chúc mừng {winner_mentions}! Bạn đã trúng **{gw_data['prize']}**!\nLink: {msg.jump_url}")

            # 3. DM Notifications
            for winner in winners:
                dm_embed = create_premium_embed(
                    title="🎊 BẠN ĐÃ TRÚNG GIVEAWAY! 🎊",
                    description=f"Chúc mừng bạn đã trúng giải từ máy chủ **{msg.guild.name}**!\n\n**Phần thưởng:** {gw_data['prize']}\n**Host:** <@{gw_data['host_id']}>\n\n[Nhấn vào đây để xem chi tiết]({msg.jump_url})",
                    color=0xf1c40f
                )
                try:
                    await winner.send(embed=dm_embed)
                except discord.Forbidden:
                    pass

        except Exception as e:
            print(f"[Giveaway] Không thể kết thúc {message_id}: {e}")

async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))
