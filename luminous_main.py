import os
import datetime
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
load_dotenv()
from config.settings import TOKENS, LUMINOUS_ID, TENEBRIS_ID
from database.redis_client import get_redis_connection, init_redis_system

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="l!", intents=intents, help_command=None)

TENEBRIS_INVITE_URL = f"https://discord.com/api/oauth2/authorize?client_id={TENEBRIS_ID}&permissions=8&scope=bot%20applications.commands"

# ⏱️ HÀM NHẬN THỨC THỜI GIAN THỰC (MÚI GIỜ VIỆT NAM UTC+7)
def get_realtime_cycle():
    tz = datetime.timezone(datetime.timedelta(hours=7))
    now = datetime.datetime.now(tz)
    # Luminous ca ngày: 00:00 - 11:59 | Tenebris ca đêm: 12:00 - 23:59
    return "DAY" if 0 <= now.hour < 12 else "NIGHT"

@bot.check
async def global_luminous_check(ctx):
    r = await get_redis_connection()
    if await r.hget("equinox:system:shutdown_status", "luminous") == "SHUTDOWN":
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

    is_overdrive = await r.hget("equinox:system:config", "event_overdrive") == "ON"
    if not is_overdrive:
        # ⏰ DÙNG ĐỒNG HỒ THỰC ĐỂ CHẶN LỆNH LỆCH CA
        cycle = get_realtime_cycle()
        if cycle == "NIGHT" and ctx.command.name not in ["staff", "profile", "marry", "check-marry"]:
            await ctx.send("🌙 Đang là ca đêm (12:00 - 00:00). Trạm Ánh Sáng đã khép cửa... Vui lòng sang thế giới ngầm của Tenebris (t!).")
            return False
    return True

@bot.event
async def on_ready():
    print(f"☀️ {bot.user.name} đã thức tỉnh trực tuyến!")
    
    # Khởi tạo kết nối Redis hạch tâm
    await init_redis_system() 
    r = await get_redis_connection() # <-- LẤY KẾT NỐI REDIS ĐỂ XỬ LÝ QUYỀN
    
    # --- MẠCH ÉP QUYỀN OWNER BẢO MẬT (DỰ PHÒNG CẢ 2 ĐƯỜNG) ---
    try:
        # Đường 1: Tự hỏi Discord API xem ai tạo ra Bot
        app_info = await bot.application_info()
        owner_id = app_info.owner.id
        
        # Đường 2: Nếu có cấu hình file .env thì ưu tiên đè lên luôn
        env_owner = os.getenv("OWNER_DISCORD_ID")
        if env_owner:
            owner_id = int(env_owner)
            
        # Ghi chặt ngai vàng lên Redis vĩnh viễn (Đã sửa từ redis_client thành r)
        await r.sadd("equinox:staff:owners", owner_id)
        print(f"👑 [Hạch Tâm] Đã đồng bộ ID Owner tối cao: {owner_id} lên RAM Đám mây Redis!")
    except Exception as e:
        print(f"❌ Lỗi mạch gác cổng nhân sự: {e}")
        
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
    luminous_presence_task.start()

@tasks.loop(seconds=15)
async def luminous_presence_task():
    r = await get_redis_connection()
    
    # 🔄 TỰ ĐỘNG CẬP NHẬT ĐỒNG HỒ LÊN REDIS MỖI 15 GIÂY CHO CÁC COG KHÁC ĐỌC
    cycle = get_realtime_cycle()
    await r.hset("equinox:system:config", "current_cycle", cycle)
    
    if await r.hget("equinox:system:config", "event_overdrive") == "ON":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="⚡ BIG EVENT OVERDRIVE ⚡"))
        return
        
    if cycle == "DAY":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="☀️ Đang chiếu sáng Thần Điện | l!help"))
    else:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.CustomActivity(name="💤 Trạm Ánh Sáng đang ngủ sâu."))

@luminous_presence_task.before_loop
async def before_presence(): await bot.wait_until_ready()
