import os
import discord
from discord.ext import commands, tasks
from config.settings import TOKENS, TENEBRIS_ID
from database.redis_client import get_redis_connection, init_redis_system

intents = discord.Intents.all()
# Tenebris dùng Prefix t!
bot = commands.Bot(command_prefix="t!", intents=intents, help_command=None)

@bot.check
async def global_tenebris_check(ctx):
    r = await get_redis_connection()
    
    if await r.hget("equinox:system:shutdown_status", "tenebris") == "SHUTDOWN":
        return False 

    if await r.get("equinox:system:global_lock") or await r.get("equinox:system:reboot_lock"):
        return False
        
    is_overdrive = await r.hget("equinox:system:config", "event_overdrive") == "ON"
    if not is_overdrive:
        cycle = await r.hget("equinox:system:config", "current_cycle")
        if cycle == "DAY" and ctx.command.name not in ["staff", "profile"]:
            await ctx.send("☀️ Nhìn lại đồng hồ hộ cái! Đang là ca ngày văn minh của vợ tao, biến ra chỗ khác!")
            return False
            
    return True

@bot.event
async def on_ready():
    print(f"☀️/🔮 {bot.user.name} (ID: {bot.user.id}) đã thức tỉnh!")
    await init_redis_system()
    
    # --- ĐOẠN SỬA ĐƯỜNG DẪN TUYỆT ĐỐI LOAD EXTENSIONS CHUẨN HOST ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Danh sách các extensions cần load
    extensions = ["cogs_shared.core_twilight", "cogs_shared.marry_khcuoc"]
    
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Đã load extension: {ext}")
        except Exception as e:
            print(f"❌ Lỗi load extension {ext}: {e}")
            
    # Tự động quét và load thêm tất cả file trong thư mục cogs (nếu có)
    cogs_dir = os.path.join(current_dir, 'cogs')
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Đã load cogs từ file: {filename}")
                except Exception as e:
                    print(f"❌ Lỗi load file cogs/{filename}: {e}")
                    
    # Ép buộc đồng bộ sau khi đã load đầy đủ toàn bộ lệnh từ extension/cogs
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Đã ép đồng bộ thành công {len(synced)} Slash Commands lên Discord API.")
    except Exception as e:
        print(f"❌ Lỗi đồng bộ lệnh: {e}")

    tenebris_presence_task.start()

@tasks.loop(seconds=15)
async def tenebris_presence_task():
    r = await get_redis_connection()
    is_overdrive = await r.hget("equinox:system:config", "event_overdrive") == "ON"
    
    if is_overdrive:
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="⚡ BIG EVENT OVERDRIVE ⚡ | Chợ Đen mở lậu tẹt ga!"))
        return

    cycle = await r.hget("equinox:system:config", "current_cycle")
    if cycle == "NIGHT":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="🔮 Chợ Đen đã mở cửa | t!help để giao dịch"))
    else:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.CustomActivity(name="🌙 Đang ngủ trong Bóng Tối..."))

@tenebris_presence_task.before_loop
async def before_presence():
    await bot.wait_until_ready()

if __name__ == "__main__":
    bot.run(TOKENS["TENEBRIS"])
