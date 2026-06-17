import os
import time
import discord
from discord import app_commands
from discord.ext import commands
from database.redis_client import get_redis_connection

class SystemAdminTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm bổ trợ check quyền Owner nhanh
    async def _is_owner(self, interaction: discord.Interaction, r) -> bool:
        env_owner = os.getenv("OWNER_DISCORD_ID")
        if env_owner and interaction.user.id == int(env_owner):
            return True
        return await r.sismember("equinox:staff:owners", interaction.user.id)

    # ==============================================================================
    # ⚡ 1. LỆNH SLASH: KIỂM TRA ĐỘ TRỄ REDIS DATABASE
    # ==============================================================================
    @app_commands.command(name="redis-ping", description="[OWNER] Kiểm tra tốc độ kết nối thời gian thực đến bộ nhớ đệm Redis Cloud")
    async def redis_ping(self, interaction: discord.Interaction):
        r = await get_redis_connection()
        if not await self._is_owner(interaction, r):
            await interaction.response.send_message("❌ Lệnh này chỉ dành cho Vua!", ephemeral=True)
            return

        start_time = time.perf_counter()
        await r.ping() # Gửi tín hiệu test đến Redis
        end_time = time.perf_counter()
        
        latency = (end_time - start_time) * 1000 # Đổi sang mili-giây (ms)
        
        # Đánh giá chất lượng đường truyền
        status = "🟢 Hoàn hảo" if latency < 50 else "🟡 Hơi lag" if latency < 150 else "🔴 Nguy hiểm (Rất chậm)"

        await interaction.response.send_message(
            f"📊 **BÁO CÁO ĐƯỜNG TRUYỀN REDIS DB:**\n"
            f"• Độ trễ (Latency): `{latency:.2f} ms`\n"
            f"• Trạng thái phản hồi: **{status}**", 
            ephemeral=True
        )

    # ==============================================================================
    # 🔄 2. LỆNH SLASH: NẠP LẠI CODE FILE TRỰC TIẾP (HOT RELOAD)
    # ==============================================================================
    @app_commands.command(name="cog-reload", description="[OWNER] Nạp lại code của một file trong cogs_shared mà không cần reset bot")
    @app_commands.describe(filename="Tên file muốn nạp lại code (Ví dụ: chat_bridge hoặc system_auditor)")
    async def cog_reload(self, interaction: discord.Interaction, filename: str):
        r = await get_redis_connection()
        if not await self._is_owner(interaction, r):
            await interaction.response.send_message("❌ Quyền lực không đủ để thực hiện thay máu hệ thống!", ephemeral=True)
            return

        # Chuẩn hóa tên file phòng trường hợp sếp gõ thừa đuôi .py
        clean_filename = filename.replace(".py", "")
        cog_path = f"cogs_shared.{clean_filename}"

        try:
            await self.bot.reload_extension(cog_path)
            # Sync lại lệnh slash lên Discord sau khi sửa code
            await self.bot.tree.sync()
            await interaction.response.send_message(f"✅ **Hot Reload Thành Công!** Đã cập nhật phiên bản code mới nhất cho file `{clean_filename}.py`.", ephemeral=True)
        except commands.ExtensionNotLoaded:
            # Nếu file đó chưa từng được nạp trước đây, tiến hành nạp mới hoàn toàn
            try:
                await self.bot.load_extension(cog_path)
                await self.bot.tree.sync()
                await interaction.response.send_message(f"📥 Đã nạp mới hoàn toàn file code `{clean_filename}.py` vào hệ thống hạch tâm.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ File mới bị lỗi cú pháp, không nạp được:\n`{str(e)}`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Hot Reload Thất Bại!** Code mới sửa đang dính lỗi:\n`{str(e)}`", ephemeral=True)

    # ==============================================================================
    # ⏰ 3. LỆNH SLASH: BẮT ÉP ĐỔI CA GIẢ LẬP ĐỂ TEST
    # ==============================================================================
    @app_commands.command(name="force-cycle", description="[OWNER] Ép hệ sinh thái chuyển sang Ca Ngày hoặc Ca Đêm giả lập trên Redis")
    @app_commands.choices(ca=[
        app_commands.Choice(name="Ca Ngày (DAY) - Luminous trực ☀️", value="DAY"),
        app_commands.Choice(name="Ca Đêm (NIGHT) - Tenebris trực 🔮", value="NIGHT"),
        app_commands.Choice(name="Trả về mặc định (Theo đồng hồ thực) 🕒", value="REAL")
    ])
    async def force_cycle(self, interaction: discord.Interaction, ca: app_commands.Choice[str]):
        r = await get_redis_connection()
        if not await self._is_owner(interaction, r):
            await interaction.response.send_message("❌ Định đảo lộn trật tự thời gian thiên đình à sếp?", ephemeral=True)
            return

        if ca.value == "REAL":
            # Xóa cấu hình ép buộc, cho phép task loop tự chạy bằng đồng hồ thực tế
            await r.hset("equinox:system:config", "event_overdrive", "OFF")
            await interaction.response.send_message("🕒 Đã trả quyền kiểm soát thời gian về cho Đồng Hồ Thực Tế của hệ thống.", ephemeral=True)
        else:
            # Ép ghi đè ca trực lên RAM Redis
            await r.hset("equinox:system:config", "current_cycle", ca.value)
            # Bật Overdrive tạm thời để chặn task loop tự động đồng bộ đè lên
            await r.hset("equinox:system:config", "event_overdrive", "ON")
            
            bot_active = "𝗟𝗨𝗠𝗜𝗡𝗢𝗨𝗦 ☀️" if ca.value == "DAY" else "𝗧𝗘𝗡𝗘𝗕𝗥𝗜𝗦 🔮"
            await interaction.response.send_message(
                f"⚡ **THAY ĐỔI CẤU TRÚC MA TRẬN THỜI GIAN:**\n"
                f"• Hệ thống đã bị ép chuyển sang ca: `{ca.value}`\n"
                f"• Bot được phép múa lệnh hiện tại: **{bot_active}**\n"
                f"*(Lưu ý: Sau khi test xong nhớ chọn lại 'Trả về mặc định' để bot chạy đúng múi giờ thật nha sếp!)*", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(SystemAdminTools(bot))
