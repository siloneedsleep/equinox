import os
import datetime
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
load_dotenv()
from config.settings import TOKENS, LUMINOUS_ID, TENEBRIS_ID
from database.redis_client import get_redis_connection, init_redis_system

intents = discord.Intents.all()

# Định nghĩa Class Bot để override lại hàm setup_hook chuẩn cấu trúc d.py v2
class LuminousBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="l!", intents=intents, help_command=None)

    async def setup_hook(self):
        # ⚡ 1. Khởi tạo kết nối Redis hạch tâm ngay khi Bot vừa lên cấu trúc
        await init_redis_system() 
        
        # ⚡ 2. Vòng lặp quét tự động nạp toàn bộ Cogs trong thư mục shared
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cogs_dir = os.path.join(current_dir, 'cogs_shared')
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    try:
                        await self.load_extension(f'cogs_shared.{filename[:-3]}')
                        print(f"☀️ [Luminous] Đã nạp thành công extension: {filename}")
                    except Exception as e:
                        # Hiện rõ lỗi ra màn hình console để sếp quản lý lỗi
                        print(f"❌ [Luminous] Lỗi nạp extension {filename}: {e}")
        
        # ⚡ 3. Đồng bộ ma trận lệnh Slash lên Discord API
        try:
            await self.tree.sync()
            print("🚀 [Luminous] Đã đồng bộ hóa thành công ma trận lệnh gạch chéo global!")
        except Exception as e:
            print(f"❌ [Luminous] Lỗi đồng bộ hóa cây lệnh tree: {e}")

bot = LuminousBot()
TENEBRIS_INVITE_URL = f"https://discord.com/api/oauth2/authorize?client_id={TENEBRIS_ID}&permissions=8&scope=bot%20applications.commands"

def get_realtime_cycle():
    tz = datetime.timezone(datetime.timedelta(hours=7))
    now = datetime.datetime.now(tz)
    return "DAY" if 0 <= now.hour < 12 else "NIGHT"

# 🛡️ MẠCH GÁC CỔNG KIỂM TRA LỆNH TOÀN DIỆN (ĐÃ FIX GIẢI MÃ REDIS BYTES)
@bot.check
async def global_luminous_check(ctx):
    r = await get_redis_connection()
    
    # Giải mã an toàn từ bytes sang string trước khi so sánh
    luminous_status = await r.hget("equinox:system:shutdown_status", "luminous")
    if luminous_status and luminous_status.decode('utf-8') == "SHUTDOWN":
        return False
        
    if await r.get("equinox:system:global_lock") or await r.get("equinox:system:reboot_lock"):
        return False
        
    if ctx.guild and not ctx.guild.get_member(TENEBRIS_ID):
        class InviteView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.add_item(discord.ui.Button(label="Triệu Hồi Tenebris (Admin) 🔮", url=TENEBRIS_INVITE_URL, style=discord.ButtonStyle.link))

        embed = discord.Embed(
            title="⚠️ HỆ SINH THÁI CHƯA HOÀN CHỈNH! ⚠️",
            description=f"Thần Điện Luminous không thể vận hành đơn độc nếu thiếu đi vòng tay bảo vệ của ông xã **<@{TENEBRIS_ID}>**.\n\nHãy bấm nút bên dưới để rước nốt chồng em về chung một nhà sếp ơi!",
            color=0xFF0055
        )
        if isinstance(ctx, commands.Context):
            await ctx.send(embed=embed, view=InviteView(), delete_after=30)
        return False

    overdrive_bytes = await r.hget("equinox:system:config", "event_overdrive")
    is_overdrive = overdrive_bytes and overdrive_bytes.decode('utf-8') == "ON"
    
    if not is_overdrive:
        cycle = get_realtime_cycle()
        if cycle == "NIGHT" and ctx.command.name not in ["staff", "profile", "marry", "check-marry"]:
            await ctx.send("🌙 Đang là ca đêm (12:00 - 00:00). Trạm Ánh Sáng đã khép cửa... Vui lòng sang thế giới ngầm của Tenebris (t!).")
            return False
    return True

@bot.event
async def on_ready():
    print(f"☀️ {bot.user.name} đã thức tỉnh trực tuyến!")
    r = await get_redis_connection()
    
    try:
        app_info = await bot.application_info()
        owner_id = app_info.owner.id
        
        env_owner = os.getenv("OWNER_DISCORD_ID")
        if env_owner:
            owner_id = int(env_owner)
            
        await r.sadd("equinox:staff:owners", owner_id)
        print(f"👑 [Hạch Tâm] Đã đồng bộ ID Owner tối cao: {owner_id} lên RAM Đám mây Redis!")
    except Exception as e:
        print(f"❌ Lỗi mạch gác cổng nhân sự: {e}")
        
    if not luminous_presence_task.is_running():
        luminous_presence_task.start()

@tasks.loop(seconds=15)
async def luminous_presence_task():
    r = await get_redis_connection()
    cycle = get_realtime_cycle()
    await r.hset("equinox:system:config", "current_cycle", cycle)
    
    overdrive_bytes = await r.hget("equinox:system:config", "event_overdrive")
    if overdrive_bytes and overdrive_bytes.decode('utf-8') == "ON":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="⚡ BIG EVENT OVERDRIVE ⚡"))
        return
        
    if cycle == "DAY":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="☀️ Đang chiếu sáng Thần Điện | l!help"))
    else:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.CustomActivity(name="💤 Trạm Ánh Sáng đang ngủ sâu."))

@luminous_presence_task.before_loop
async def before_presence(): 
    await bot.wait_until_ready()

# Kích hoạt chạy tiến trình bằng Token ca ngày
bot.run(os.getenv("LUMINOUS_TOKEN"))
