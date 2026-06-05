import discord
from discord.ext import commands
import json
import random
import asyncio
import time

# ==============================================================================
# 🧰 HÀM TIỆN ÍCH DATABASE KINH TẾ NGẦM
# ==============================================================================
def load_db():
    try:
        with open("storage.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_db(data):
    with open("storage.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user_data(data, user_id):
    users = data.setdefault("users", {})
    user_str = str(user_id)
    if user_str not in users:
        users[user_str] = {"cash": 0, "bank": 0, "dirty_cash": 0, "inventory": {}}
    
    # Cập nhật thêm ví Tiền bẩn nếu user cũ chưa có
    if "dirty_cash" not in users[user_str]:
        users[user_str]["dirty_cash"] = 0
        
    return users[user_str]

# ==============================================================================
# 🔫 COG: THẾ GIỚI NGẦM & TỘI PHẠM (CRIME)
# ==============================================================================
class CrimeSyndicate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================================================
    # 🚛 LỆNH BUÔN LẬU XUYÊN BIÊN GIỚI (TẠO TIỀN BẨN)
    # ==========================================================================
    @commands.command(name="smuggle", aliases=["sm"])
    @commands.cooldown(1, 120, commands.BucketType.user) # Hồi chiêu 2 phút để tránh spam
    async def smuggle(self, ctx, amount: int = None):
        if not amount or amount < 1000:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Vốn khởi nghiệp buôn lậu tối thiểu phải là **1,000 ⭐**!")

        data = load_db()
        user_data = get_user_data(data, ctx.author.id)

        if user_data["cash"] < amount:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ Bạn không đủ tiền sạch để nhập hàng! Hiện có: **{user_data['cash']:,} ⭐**")

        # Trừ tiền gốc (Tiền sạch)
        user_data["cash"] -= amount
        save_db(data)

        msg = await ctx.send(f"🚛 **[{ctx.author.name}]** Đã ném **{amount:,} ⭐** vào vali. Đang băng qua Trạm Thu Phí Liên Server...")
        
        # Giả lập thời gian chạy hàng (Hồi hộp)
        await asyncio.sleep(3)
        await msg.edit(content=f"🚨 Cảnh sát mạng lưới (Staff) đang đi tuần tra...")
        await asyncio.sleep(2)

        data = load_db() # Đọc lại DB sau khi delay
        user_data = get_user_data(data, ctx.author.id)

        # Thuật toán tỷ lệ (60% trót lọt, 40% bị tóm)
        chance = random.randint(1, 100)
        
        if chance <= 60: # TRÓT LỌT
            multiplier = random.uniform(2.5, 5.0) # Lãi x2.5 đến x5 lần
            dirty_reward = int(amount * multiplier)
            
            user_data["dirty_cash"] += dirty_reward
            save_db(data)
            
            embed = discord.Embed(title="💰 GIAO DỊCH CHỢ ĐEN TRÓT LỌT!", color=discord.Color.green())
            embed.description = f"Chuyến hàng trót lọt! Bạn đã thu về **{dirty_reward:,} 🚨 Tiền Bẩn**."
            embed.set_footer(text="Ghi chú: Tiền Bẩn không thể dùng để mua đồ, phải dùng lệnh l!launder để rửa!")
            await msg.edit(content=None, embed=embed)
            
        else: # BỊ TÓM TỊCH THU
            sys_data = data.setdefault("system", {})
            sys_data["global_treasury"] = sys_data.get("global_treasury", 0) + amount # Nạp vào quốc khố
            save_db(data)
            
            embed = discord.Embed(title="🚓 BỊ CẢNH SÁT TÓM!", color=discord.Color.red())
            embed.description = f"Chuyến hàng đã bị lính tuần tra tóm gọn tại biên giới! Toàn bộ **{amount:,} ⭐** tiền vốn đã bị tịch thu nạp vào Ngân khố Quốc gia."
            await msg.edit(content=None, embed=embed)

    # ==========================================================================
    # 🚰 LỆNH RỬA TIỀN CHỢ ĐEN (LAUNDER)
    # ==========================================================================
    @commands.command(name="launder", aliases=["bm"])
    async def launder(self, ctx):
        data = load_db()
        user_data = get_user_data(data, ctx.author.id)
        
        dirty_amt = user_data.get("dirty_cash", 0)
        if dirty_amt <= 0:
            return await ctx.send("❌ Bạn làm gì có đồng Tiền Bẩn (🚨) nào mà đòi rửa?")

        # Tính toán phí rửa tiền (15% - 25% hao hụt)
        fee_percent = random.uniform(0.15, 0.25)
        fee_amt = int(dirty_amt * fee_percent)
        clean_amt = dirty_amt - fee_amt
        
        # Chuyển đổi dòng tiền
        user_data["dirty_cash"] = 0
        user_data["cash"] += clean_amt
        
        # Nạp phế rửa tiền vào quốc khố của Sếp
        sys_data = data.setdefault("system", {})
        sys_data["global_treasury"] = sys_data.get("global_treasury", 0) + fee_amt
        
        save_db(data)
        
        embed = discord.Embed(title="🧼 RỬA TIỀN THÀNH CÔNG", color=discord.Color.blue())
        embed.add_field(name="Tiền Bẩn Đưa Vào", value=f"`{dirty_amt:,} 🚨`", inline=True)
        embed.add_field(name="Hao Hụt (Thuế Chợ Đen)", value=f"`-{fee_amt:,} ⭐`", inline=True)
        embed.add_field(name="Tiền Sạch Thu Về", value=f"**{clean_amt:,} ⭐**", inline=False)
        embed.set_footer(text="Số Tiền Sạch đã được cộng trực tiếp vào Ví (Cash) của bạn.")
        
        await ctx.send(embed=embed)

    # ==========================================================================
    # 🔪 LỆNH THUÊ SÁT THỦ ÁM SÁT CƯỚP TIỀN (HITMAN)
    # ==========================================================================
    @commands.command(name="hitman", aliases=["hm"])
    @commands.cooldown(1, 300, commands.BucketType.user) # 5 phút ám sát 1 lần
    async def hitman(self, ctx, target: discord.Member = None):
        if not target:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Cú pháp: `l!hitman @người_muốn_ám_sát`")
            
        if target.id == ctx.author.id or target.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Sát thủ không nhận kèo tự sát hoặc ám sát Bot!")

        data = load_db()
        attacker_data = get_user_data(data, ctx.author.id)
        victim_data = get_user_data(data, target.id)

        hitman_fee = 50000 # Phí thuê sát thủ cố định 50k Star
        if attacker_data["cash"] < hitman_fee:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ Bạn không đủ **{hitman_fee:,} ⭐** để ký hợp đồng sát thủ!")
            
        if victim_data["cash"] < 10000:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Mục tiêu quá nghèo (dưới 10k ⭐), sát thủ chê không thèm giết!")

        # Thu phí hợp đồng
        attacker_data["cash"] -= hitman_fee
        save_db(data)

        msg = await ctx.send(f"🥷 **Bóng đêm buông xuống...** Sát thủ đã nhận **{hitman_fee:,} ⭐** và đang tiếp cận {target.mention}...")
        await asyncio.sleep(4)

        # Check bảo hiểm của nạn nhân
        victim_inventory = victim_data.get("inventory", {})
        has_insurance = victim_inventory.get("insurance_anti_rob", 0) > 0

        data = load_db() # Cập nhật lại
        attacker_data = get_user_data(data, ctx.author.id)
        victim_data = get_user_data(data, target.id)

        # Tỷ lệ ám sát: 40% thành công
        if random.randint(1, 100) <= 40:
            # Cướp 15% - 30% tiền mặt của mục tiêu
            rob_percent = random.uniform(0.15, 0.30)
            stolen_amt = int(victim_data["cash"] * rob_percent)
            
            if has_insurance:
                # Nếu có bảo hiểm: Bị cướp nhưng bảo hiểm đền lại 100% (Tiền in ra từ hệ thống)
                attacker_data["cash"] += stolen_amt
                victim_inventory["insurance_anti_rob"] -= 1 # Trừ 1 vé bảo hiểm
                save_db(data)
                
                await msg.edit(content=f"🔥 **ÁM SÁT THÀNH CÔNG NHƯNG...**\nSát thủ đã cướp được **{stolen_amt:,} ⭐** từ {target.name}. Tuy nhiên, nạn nhân có **Bảo Hiểm Tài Sản Cấp 1**, hệ thống đã đền bù lại toàn bộ số tiền bị mất cho họ!")
            else:
                # Không có bảo hiểm: Mất trắng
                victim_data["cash"] -= stolen_amt
                attacker_data["cash"] += stolen_amt
                save_db(data)
                
                await msg.edit(content=f"🩸 **ÁM SÁT HOÀN HẢO!**\nSát thủ đã đâm gục {target.name} và cướp về cho bạn **{stolen_amt:,} ⭐** sạch!")
        else:
            # Ám sát thất bại
            await msg.edit(content=f"🛡️ **ÁM SÁT THẤT BẠI!**\n{target.name} đã phòng bị và phản công. Sát thủ phải rút lui, bạn mất trắng **{hitman_fee:,} ⭐** tiền hợp đồng!")

    # Bắt lỗi Cooldown cho mảng tội phạm
    @smuggle.error
    @hitman.error
    async def crime_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Cảnh sát đang lùng sục gắt gao! Hãy ẩn náu và thử lại sau **{error.retry_after:.0f} giây**.", delete_after=5)

async def setup(bot):
    await bot.add_cog(CrimeSyndicate(bot))
