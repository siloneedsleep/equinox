import os
import discord
from discord import app_commands
from discord.ext import commands
from database.redis_client import get_redis_connection
from config.settings import LUMINOUS_ID, TENEBRIS_ID

class SystemAuditor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==============================================================================
    # 🧪 LỆNH SLASH: TỰ ĐỘNG KIỂM THỬ HỆ THỐNG LỆNH
    # ==============================================================================
    @app_commands.command(name="test-commands", description="[OWNER] Quét và kiểm tra toàn bộ trạng thái hoạt động của hệ thống lệnh")
    async def test_commands(self, interaction: discord.Interaction):
        r = await get_redis_connection()
        
        # 👑 1. XÁC THỰC QUYỀN OWNER TỐI CAO
        is_owner = False
        env_owner = os.getenv("OWNER_DISCORD_ID")
        if env_owner and interaction.user.id == int(env_owner):
            is_owner = True
        if not is_owner:
            is_owner = await r.sismember("equinox:staff:owners", interaction.user.id)
            
        if not is_owner:
            await interaction.response.send_message(
                "❌ Lệnh kiểm thử hạch tâm tối mật. Dân thường vui lòng né ra chỗ khác!", 
                ephemeral=True
            )
            return

        # Gửi phản hồi tạm thời vì quá trình quét có thể mất vài giây
        await interaction.response.defer(ephemeral=True)

        # ⏳ 2. KIỂM TRA VÀ LẤY CA TRỰC HIỆN TẠI TỪ REDIS
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if isinstance(cycle_bytes, bytes) else str(cycle_bytes)
        is_overdrive = await r.hget("equinox:system:config", "event_overdrive") == b"ON" or await r.hget("equinox:system:config", "event_overdrive") == "ON"

        # Xác định xem con bot đang thực thi lệnh này có đang trong ca trực của nó không
        is_correct_cycle = True
        if not is_overdrive:
            if self.bot.user.id == LUMINOUS_ID and cycle != "DAY":
                is_correct_cycle = False
            elif self.bot.user.id == TENEBRIS_ID and cycle != "NIGHT":
                is_correct_cycle = False

        # 📊 3. THIẾT LẬP EMBED BÁO CÁO
        bot_name = "𝗟𝗨𝗠𝗜𝗡𝗢𝗨𝗦 ☀️" if self.bot.user.id == LUMINOUS_ID else "𝗧𝗘𝗡𝗘𝗕𝗥𝗜𝗦 🔮"
        embed = discord.Embed(
            title=f"🧪 BÁO CÁO KIỂM THỬ HỆ THỐNG: {bot_name}",
            description=f"**Trạng thái ca trực:** {'`OVERDRIVE` ⚡' if is_overdrive else f'`CA {cycle}`'}\n"
                        f"**Kết nối Redis DB:** `ONLINE` 🟢\n"
                        f"**Kết nối Discord API:** `CONNECTED` 🟢\n\n"
                        f"🤖 *Dưới đây là danh sách phân tích trạng thái khả dụng của các lệnh:*",
            color=0x00FF88 if is_correct_cycle else fxFF9900
        )

        available_cmds = []
        blocked_cmds = []
        error_cmds = []

        # 🔍 4. LỌC VÀ KIỂM TRA TOÀN BỘ LỆNH ĐANG CÓ TRONG BOT
        
        # Nhóm A: Lệnh thường (Prefix Commands - l! hoặc t!)
        all_prefix_commands = list(self.bot.commands)
        # Nhóm B: Lệnh Slash (Slash Commands - /)
        all_slash_commands = list(self.bot.tree.get_commands())

        # Danh sách các lệnh luôn được mở bất kể lệch ca (Đồng bộ với bộ lọc chính của ông)
        bypass_list = ["staff", "profile", "marry", "check-marry", "test-commands"]

        # Kiểm tra Nhóm Slash Commands
        for cmd in all_slash_commands:
            if not is_correct_cycle and cmd.name not in bypass_list:
                blocked_cmds.append(f"`/{cmd.name}` (Sai ca trực)")
            else:
                available_cmds.append(f"`/{cmd.name}` (Sẵn sàng)")

        # Kiểm tra Nhóm Prefix Commands
        for cmd in all_prefix_commands:
            if not is_correct_cycle and cmd.name not in bypass_list:
                blocked_cmds.append(f"`{self.bot.command_prefix}{cmd.name}` (Sai ca trực)")
            else:
                # Kiểm tra xem lệnh có bị lỗi logic nạp / thiếu hàm bổ trợ không
                try:
                    if cmd.enabled is False:
                        error_cmds.append(f"`{self.bot.command_prefix}{cmd.name}` (Đang bị tắt hạch tâm)")
                    else:
                        available_cmds.append(f"`{self.bot.command_prefix}{cmd.name}` (Sẵn sàng)")
                except Exception as e:
                    error_cmds.append(f"`{self.bot.command_prefix}{cmd.name}` (Lỗi cấu trúc: {str(e)})")

        # 📝 5. ĐỔ DỮ LIỆU VÀO CÁC TRƯỜNG EMBED
        if available_cmds:
            embed.add_field(
                name="🟢 LỆNH HOẠT ĐỘNG HOÀN HẢO", 
                value="\n".join(available_cmds[:15]) + (f"\n*...và {len(available_cmds) - 15} lệnh khác*" if len(available_cmds) > 15 else ""), 
                inline=False
            )
        else:
            embed.add_field(name="🟢 LỆNH HOẠT ĐỘNG HOÀN HẢO", value="`Không có`", inline=False)

        if blocked_cmds:
            embed.add_field(
                name="⚠️ LỆNH BỊ KHÓA DO CHIA CA", 
                value=f"*(Các lệnh này sẽ tự động mở lại khi đổi ca sang {cycle})*\n" + "\n".join(blocked_cmds[:10]) + (f"\n*...và {len(blocked_cmds) - 10} lệnh khác*" if len(blocked_cmds) > 10 else ""), 
                inline=False
            )

        if error_cmds:
            embed.add_field(
                name="❌ LỆNH LỖI CODE / CHẾT NỘI BỘ", 
                value="\n".join(error_cmds), 
                inline=False
            )
            embed.color = 0xFF0000

        # Gửi kết quả cuối cùng về cho Owner xem ẩn danh
        await interaction.edit_original_response(embed=embed)


async def setup(bot):
    await bot.add_cog(SystemAuditor(bot))
