import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import datetime
from config.settings import LUMINOUS_ID, TENEBRIS_ID
from database.redis_client import get_redis_connection

class CoreTwilight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cron_twilight_lock.start()

    def cog_unload(self):
        self.cron_twilight_lock.cancel()

    # ==========================================
    # ⏰ 1. ĐỒNG HỒ TỰ ĐỘNG KHÓA MẠCH 5 GIÂY LÚC 12:00
    # ==========================================
    @tasks.loop(seconds=1)
    async def cron_twilight_lock(self):
        now = datetime.datetime.now()
        # Chạm đúng 12:00:00 trưa hoặc đêm
        if (now.hour == 12 or now.hour == 0) and now.minute == 0 and now.second == 0:
            r = await get_redis_connection()
            # Đặt khóa tổng toàn vương quốc đúng 5 giây
            await r.set("equinox:system:global_lock", "FROZEN", ex=5)
            
            # Đảo ca trực trên DB
            current_cycle = await r.hget("equinox:system:config", "current_cycle")
            new_cycle = "NIGHT" if current_cycle == "DAY" else "DAY"
            await r.hset("equinox:system:config", "current_cycle", new_cycle)
            
            print(f"[{now.strftime('%H:%M:%S')}] ⏳ HỆ THỐNG ĐÓNG BĂNG 5S ĐỂ GIAO CA SANG {new_cycle}!")
            await asyncio.sleep(1) # Tránh loop chạy lại trong cùng 1 giây

    @cron_twilight_lock.before_loop
    async def before_cron(self):
        await self.bot.wait_until_ready()

    # ==========================================
    # 👑 2. NÚT BẤM HẠT NHÂN: TẮT KHẨN CẤP (/system-kill)
    # ==========================================
    @app_commands.command(name="system-kill", description="[Owner/Dev] Đóng băng khẩn cấp BOT")
    @app_commands.describe(target="Chọn thực thể muốn tắt")
    @app_commands.choices(target=[
        app_commands.Choice(name="Luminous (Ca ngày)", value="luminous"),
        app_commands.Choice(name="Tenebris (Ca đêm)", value="tenebris"),
        app_commands.Choice(name="Tắt cả hai (Toàn hệ thống)", value="both")
    ])
    @app_commands.default_permissions(administrator=True) # Tạm dùng Admin check, sau bọc hàm Owner sau
    async def system_kill(self, interaction: discord.Interaction, target: str):
        r = await get_redis_connection()
        
        if target in ["luminous", "both"]:
            await r.hset("equinox:system:shutdown_status", "luminous", "SHUTDOWN")
            if self.bot.user.id == LUMINOUS_ID:
                await self.bot.change_presence(status=discord.Status.invisible)
                
        if target in ["tenebris", "both"]:
            await r.hset("equinox:system:shutdown_status", "tenebris", "SHUTDOWN")
            if self.bot.user.id == TENEBRIS_ID:
                await self.bot.change_presence(status=discord.Status.invisible)

        await interaction.response.send_message(f"🔒 Đã ngắt mạch năng lượng của `{target.upper()}`. Hệ thống giả chết thành công!", ephemeral=True)

    # ==========================================
    # 👑 3. KÍCH HOẠT LẠI HỆ THỐNG (/system-wakeup)
    # ==========================================
    @app_commands.command(name="system-wakeup", description="[Owner/Dev] Khởi động lại BOT (Có 5s Cooldown)")
    @app_commands.describe(target="Chọn thực thể muốn bật")
    @app_commands.choices(target=[
        app_commands.Choice(name="Luminous (Ca ngày)", value="luminous"),
        app_commands.Choice(name="Tenebris (Ca đêm)", value="tenebris"),
        app_commands.Choice(name="Bật cả hai", value="both")
    ])
    @app_commands.default_permissions(administrator=True)
    async def system_wakeup(self, interaction: discord.Interaction, target: str):
        r = await get_redis_connection()
        
        # Đặt cờ Reboot Lock 5 giây để dọn dẹp
        await r.set("equinox:system:reboot_lock", "REBOOTING", ex=5)
        
        if target in ["luminous", "both"]:
            await r.hset("equinox:system:shutdown_status", "luminous", "ACTIVE")
        if target in ["tenebris", "both"]:
            await r.hset("equinox:system:shutdown_status", "tenebris", "ACTIVE")

        await interaction.response.send_message(f"🔋 Đã bơm lại mạch sống cho `{target.upper()}`. Hệ thống đang tiến hành Unload 5 giây!", ephemeral=True)

    # ==========================================
    # ⚡ 4. SẮC LỆNH BIG EVENT (/system-twilight-event)
    # ==========================================
    @app_commands.command(name="system-twilight-event", description="[Owner/Event Manager] Kích hoạt Big Event Overdrive")
    @app_commands.describe(status="Bật hoặc Tắt", duration="Thời gian diễn ra (Phút)")
    @app_commands.choices(status=[
        app_commands.Choice(name="ON - Bật", value="ON"),
        app_commands.Choice(name="OFF - Tắt", value="OFF")
    ])
    @app_commands.default_permissions(administrator=True)
    async def big_event(self, interaction: discord.Interaction, status: str, duration: int = 60):
        r = await get_redis_connection()
        
        if status == "ON":
            await r.hset("equinox:system:config", "event_overdrive", "ON")
            # Thiết lập thời gian hết hạn (Unix Timestamp)
            expire_at = int(datetime.datetime.now().timestamp()) + (duration * 60)
            await r.hset("equinox:system:config", "event_expire_at", expire_at)
            
            embed = discord.Embed(title="⚡ BIG EVENT OVERDRIVE ĐÃ KÍCH HOẠT", color=0xFFD700)
            embed.description = f"Mạch ngày đêm đã bị đóng băng! Cả Luminous và Tenebris sẽ thức tỉnh 100% công suất trong `{duration} phút` tới!"
            await interaction.response.send_message(embed=embed)
        else:
            await r.hset("equinox:system:config", "event_overdrive", "OFF")
            await interaction.response.send_message("🛑 Đã tắt Big Event. Khôi phục lại quỹ đạo luân phiên Ngày/Đêm.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CoreTwilight(bot))
