import os
import discord
from discord.ext import commands, tasks
from config.settings import TOKENS, LUMINOUS_ID
from database.redis_client import get_redis_connection, init_redis_system

intents = discord.Intents.all()
# Luminous dùng Hybrid (chạy song song l! và /)
bot = commands.Bot(command_prefix="l!", intents=intents, help_command=None)

@bot.check
async def global_luminous_check(ctx):
    r = await get_redis_connection()
    
    # 1. Kiểm tra Lệnh Tắt Khẩn Cấp (/system-kill)
    if await r.hget("equinox:system:shutdown_status", "luminous") == "SHUTDOWN":
        return False

    # 2. Kiểm tra đóng băng 5s (Cooldown giao ca)
    if await r.get("equinox:system:global_lock") or await r.get("equinox:system:reboot_lock"):
        return False
        
    # 3. Kiểm tra Ca Trực Ngày/Đêm
    is_overdrive = await r.hget("equinox:system:config", "event_overdrive") == "ON"
    if not is_overdrive:
        cycle = await r.hget("equinox:system:config", "current_cycle")
        if cycle == "NIGHT" and ctx.command.name not in ["staff", "profile"]:
            await ctx.send("🌙 Trạm Ánh Sáng đã khép cửa... Vui lòng sang thế giới ngầm của Tenebris (t!).")
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
            
   # Tự động quét và load thêm tất cả file trong thư mục cogs_shared
    cogs_dir = os.path.join(current_dir, 'cogs_shared')
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                # Bỏ qua 2 file đã load cứng ở trên để tránh lỗi trùng lặp
                if filename[:-3] in ['core_twilight', 'marry_khcuoc']:
                    continue
                try:
                    await bot.load_extension(f'cogs_shared.{filename[:-3]}')
                    print(f"✅ Đã load cogs từ file: {filename}")
                except Exception as e:
                    print(f"❌ Lỗi load file cogs_shared/{filename}: {e}")
                    
    # Ép buộc đồng bộ sau khi đã load đầy đủ toàn bộ lệnh từ extension/cogs
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Đã ép đồng bộ thành công {len(synced)} Slash Commands lên Discord API.")
    except Exception as e:
        print(f"❌ Lỗi đồng bộ lệnh: {e}")

    luminous_presence_task.start()

@tasks.loop(seconds=15)
async def luminous_presence_task():
    r = await get_redis_connection()
    is_overdrive = await r.hget("equinox:system:config", "event_overdrive") == "ON"
    
    if is_overdrive:
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="⚡ BIG EVENT OVERDRIVE ⚡ | Thần Điện xả băng thông!"))
        return

    cycle = await r.hget("equinox:system:config", "current_cycle")
    if cycle == "DAY":
        await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="☀️ Đang chiếu sáng Thần Điện | l!help hoặc /help"))
    else:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.CustomActivity(name="💤 Trạm Ánh Sáng đang ngủ sâu."))

@luminous_presence_task.before_loop
async def before_presence():
    await bot.wait_until_ready()

	if __name__ == "__main__":
