import os
import datetime
import discord
from discord.ext import commands, tasks
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
    print(f"☀️ Luminous (ID: {bot.user.id}) đã thức tỉnh!")
    await init_redis_system()
    
    try:
        r = await get_redis_connection()
        app_info = await bot.application_info()
        await r.hset("equinox:system:staff_roles", str(app_info.owner.id), "owner")
    except Exception as e:
        print(f"❌ Lỗi cấu hình Owner: {e}")
        
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
