import os
import datetime
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv # <-- THÊM ĐỂ ĐỌC FILE .ENV CA ĐÊM
from config.settings import TOKENS, LUMINOUS_ID, TENEBRIS_ID
from database.redis_client import get_redis_connection, init_redis_system

# Nạp các biến môi trường từ file .env ngay khi chạy
load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="t!", intents=intents, help_command=None)

LUMINOUS_INVITE_URL = f"https://discord.com/api/oauth2/authorize?client_id={LUMINOUS_ID}&permissions=8&scope=bot%20applications.commands"

# ⏱️ HÀM NHẬN THỨC THỜI GIAN THỰC (MÚI GIỜ VIỆT NAM UTC+7)
def get_realtime_cycle():
    tz = datetime.timezone(datetime.timedelta(hours=7))
    now = datetime.datetime.now(tz)
    return "DAY" if 0 <= now.hour < 12 else "NIGHT"

@bot.check
async def global_tenebris_check(ctx):
    r = await get_redis_connection()
    if await r.hget("equinox:system:shutdown_status", "tenebris") == "SHUTDOWN":
        return False 
    if await r.get("equinox:system:global_lock") or await r.get("equinox:system:reboot_lock"):
        return False
        
    if ctx.guild and not ctx.guild.get_member(LUMINOUS_ID):
        class InviteView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.add_item(discord.ui.Button(label="Triệu Hồi Luminous (Admin) ☀️", url=LUMINOUS_INVITE_URL, style=discord.ButtonStyle.link))

        embed = discord.Embed(
            title="⚠️ HỆ SINH THÁI CHƯA HOÀN CHỈNH! ⚠️",
            description=f"Chợ Đen Tenebris không thể giao dịch lậu nếu thiếu đi Ánh Sáng bảo kê của cô vợ **<@{LUMINOUS_ID}>** phía sau.\n\nHãy bấm nút bên dưới để rước nốt bả về quản lý giùm cái sếp!",
            color=0x4B0082
        )
        if isinstance(ctx, commands.Context):
            await ctx.send(embed=embed, view=InviteView(), delete_after=30)
        return False

    is_overdrive = await r.hget("equinox:system:config", "event_overdrive") == "ON"
    if not is_overdrive:
        # ⏰ DÙNG ĐỒNG HỒ THỰC ĐỂ CHẶN LỆNH LỆCH CA
        cycle = get_realtime_cycle()
        if cycle == "DAY" and ctx.command.name not in ["staff", "profile", "marry", "check-marry"]:
            await ctx.send("☀️ Đang là ca ngày (00:00 - 12:00). Nhìn lại đồng hồ hộ cái! Vợ tao đang trực, biến ra chỗ khác!")
            return False
    return True

@bot.event
async def on_ready():
    print(f"🔮 {bot.user.name} đã thức tỉnh trực tuyến!")
    
    await init_redis_system() 
    r = await get_redis_connection() # <-- LẤY KẾT NỐI REDIS ĐỂ ÉP QUYỀN TRÊN RAM
    
    try:
        app_info = await bot.application_info()
        owner_id = app_info.owner.id
        
        env_owner = os.getenv("OWNER_DISCORD_ID")
        if env_owner:
            owner_id = int(env_owner)
            
        # Đã sửa từ redis_client thành r để không bốc lỗi NameError
        await r.sadd("equinox:staff:owners", owner_id)
        print(f"👑 [Thế Giới Ngầm] Đã kiểm chốt và nhận diện Owner: {owner_id}")
    except Exception as e:
        print(f"❌ Lỗi mạch gác cổng nhân sự ca đêm: {e}")
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cogs_dir = os.path.join(current_dir, 'cogs_shared')
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await bot.load_extension(f'cogs_shared.{filename[:-3]}')
                except Exception:
                    pass
    try:
        await bot.tree.sync()
    except Exception:
        pass
    tenebris_presence_task.start()

@tasks.loop(seconds=15)
async def tenebris_presence_task():
    r = await get_redis_connection()
    
    # 🔄 TỰ ĐỘNG CẬP NHẬT ĐỒNG HỒ LÊN REDIS MỖI 15 GIÂY CHO CÁC COG KHÁC ĐỌC
    cycle = get_realtime_cycle()
    await r.hset("equinox:system:config", "current_cycle", cycle)
    
    if await r.hget("equinox:system:config", "event_overdrive") == "ON":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="⚡ BIG EVENT OVERDRIVE ⚡"))
        return
        
    if cycle == "NIGHT":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="🔮 Chợ Đen đã mở cửa | t!help"))
    else:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.CustomActivity(name="🌙 Đang ngủ trong Bóng Tối..."))

@tenebris_presence_task.before_loop
async def before_presence(): await bot.wait_until_ready()
