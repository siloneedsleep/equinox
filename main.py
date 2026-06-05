import discord
from discord.ext import commands
import os
import json
import sys
from dotenv import load_dotenv

# ==============================================================================
# 🔧 NẠP BIẾN MÔI TRƯỜNG & LÕI CẤU HÌNH
# ==============================================================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN or TOKEN == "DÁN_TOKEN_BOT_CỦA_SẾP_VÀO_ĐÂY":
    print("🚨 LỖI CHÍ MẠNG: Sếp chưa điền DISCORD_TOKEN vào file .env!")
    sys.exit(1)

# ==============================================================================
# 🛡️ LỚP 1: LÁ CHẮN ANTI-CRASH TOÀN CỤC (SYS EXCEPTHOOK)
# ==============================================================================
def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Cô lập mọi lỗi tràn RAM, rò rỉ bộ nhớ, chống văng tiến trình Python"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print(f"🚨 [Anti-Crash Core] Đã chặn một lỗi chí mạng hệ thống: {exc_value}", file=sys.stderr)

sys.excepthook = handle_unhandled_exception

# ==============================================================================
# 🔀 BỘ QUÉT ĐA PREFIX ĐỘNG (MULTI-PREFIX ENGINE)
# ==============================================================================
async def get_prefix(bot, message):
    """Hỗ trợ mặc định l!, L!, @TagBot và 5 prefix tự chọn của mỗi server"""
    prefixes = ["l!", "L!", f"<@{bot.user.id}> ", f"<@!{bot.user.id}> "]
    
    if message.guild:
        try:
            with open("storage.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                custom = data.get("guilds", {}).get(str(message.guild.id), {}).get("custom_prefixes", [])
                prefixes.extend(custom[:5])
        except Exception:
            pass # Bỏ qua nếu file đang bị lock hoặc chưa có
            
    return prefixes

# Khởi tạo thực thể Bot
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=get_prefix, 
    intents=intents,
    case_insensitive=True, # Lõi nhận diện lệnh không phân biệt HOA/thường (l!bj = L!Bj)
    help_command=None      # Xóa help mặc định để dùng hệ thống Slash/Embed riêng
)

# ==============================================================================
# 🧱 BỨC TƯỜNG LỬA INTERCEPTOR (CHẶN LỆNH KHI BẢO TRÌ)
# ==============================================================================
def check_maintenance(user_id):
    """Kiểm tra xem hệ thống có đang bị sếp đóng băng không"""
    try:
        with open("storage.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        sys_data = data.get("system", {})
        
        if sys_data.get("maintenance", False):
            # Đặc quyền tối cao: Owner và Dev vẫn được dùng lệnh bình thường
            if user_id == sys_data.get("owner_id") or user_id == sys_data.get("developer"):
                return False, None, None
            return True, sys_data.get("maintenance_reason"), sys_data.get("maintenance_until")
    except Exception:
        pass
    return False, None, None

# Chặn lệnh Prefix (l!...)
@bot.check
async def global_prefix_interceptor(ctx):
    is_maintaining, reason, until = check_maintenance(ctx.author.id)
    if is_maintaining:
        time_str = f"<t:{int(until)}:R>" if until else "Vô hạn (Đợi lệnh Sếp)"
        await ctx.send(f"⚠️ **HỆ THỐNG ĐANG BẢO TRÌ!**\n> 📝 **Lý do:** {reason}\n> ⏳ **Mở khóa sau:** {time_str}", delete_after=10)
        return False
    return True

# Chặn lệnh Slash (/...)
@bot.tree.interaction_check
async def global_slash_interceptor(interaction: discord.Interaction):
    is_maintaining, reason, until = check_maintenance(interaction.user.id)
    if is_maintaining:
        time_str = f"<t:{int(until)}:R>" if until else "Vô hạn (Đợi lệnh Sếp)"
        await interaction.response.send_message(
            f"🔒 **BẢO TRÌ TOÀN CỤC LUMINOUS**\n> 📝 **Lý do:** `{reason}`\n> ⏳ **Mở khóa sau:** {time_str}\n*Hệ thống ví Star (⭐) đang được niêm phong an toàn!*",
            ephemeral=True
        )
        return False
    return True

# ==============================================================================
# 🛡️ LỚP 2: LÁ CHẮN ANTI-CRASH CHO COMMANDS
# ==============================================================================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return # Bỏ qua nếu user gõ lầm phím
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kỷ luật quốc gia: Bạn không đủ quyền hạn để xài lệnh này!", delete_after=5)
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Lòng tham vô hạn! Lệnh đang hồi, vui lòng đợi {error.retry_after:.1f} giây.", delete_after=5)
        return
    
    print(f"🚨 [Anti-Crash Command] Chặn lỗi tại lệnh {ctx.command}: {error}", file=sys.stderr)
    await ctx.send("⚠️ Lõi xử lý gặp dao động nhẹ. Giao dịch Star của bạn đã được hủy để bảo toàn!", delete_after=5)

# ==============================================================================
# 🚀 KÍCH NỔ HỆ THỐNG (ON_READY)
# ==============================================================================
@bot.event
async def on_ready():
    print("=" * 60)
    print(f"👑 LUMINOUS ENGINE ĐÃ SẴN SÀNG RỰC LỬA!")
    print(f"🤖 Danh tính: {bot.user.name} (ID: {bot.user.id})")
    print(f"💻 Tiến trình Python bảo mật vĩ mô đang vận hành...")
    print("=" * 60)

    # 1. Đọc và khôi phục diện mạo bot từ storage.json
    try:
        with open("storage.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            sys_data = data.get("system", {})
            bot_settings = sys_data.get("bot_settings", {})
            
            # Nếu đang bảo trì, ép status về DND
            if sys_data.get("maintenance", False):
                await bot.change_presence(status=discord.Status.dnd, activity=discord.Game("⚠️ HỆ THỐNG ĐANG BẢO TRÌ"))
                print("🔒 Bot đang bật chế độ niêm phong bảo trì!")
            else:
                s_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd}
                saved_status = bot_settings.get("saved_status", "online")
                act_text = bot_settings.get("activity_text", "Luminous Network ⭐")
                await bot.change_presence(status=s_map.get(saved_status, discord.Status.online), activity=discord.Game(act_text))
                
    except Exception as e:
        print(f"⚠️ Cảnh báo khôi phục diện mạo: {e}")

    # 2. Tự động nạp tất cả các Modular Cogs
    if not os.path.exists("./cogs"):
        os.makedirs("./cogs")
        print("📁 Đã tạo thư mục ./cogs")

    print("\n📦 Đang nạp các tệp tính năng (Cogs)...")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"  ✅ Đã nạp thành công: {filename}")
            except Exception as e:
                print(f"  ❌ Lỗi khi nạp module {filename}: {e}")

    # 3. Đồng bộ Slash Commands lên Discord Gateway
    try:
        synced = await bot.tree.sync()
        print(f"\n🔥 Đã đồng bộ {len(synced)} lệnh Slash vĩ mô lên mạng lưới toàn cầu.")
    except Exception as e:
        print(f"🚨 Lỗi đồng bộ Slash: {e}")

# Kích hoạt trục xương sống
if __name__ == "__main__":
    bot.run(TOKEN)
