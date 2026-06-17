import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
from database.redis_client import get_redis_connection

class EquinoxCoreGameplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_sunrise_amnesty.start() # Bật mạch quét tự động Đại Xá Bình Minh
        
        # 👑 CÀI CẮM HOOK PHONG TỎA TOÀN DIỆN (MUTE BOT)
        # Tự động chặn đứng người dùng bị bắt cóc ở TẤT CẢ các lệnh Slash trong hệ thống Bot
        self.old_check = bot.tree.interaction_check
        @bot.tree.interaction_check
        async def global_bot_mute_check(interaction: discord.Interaction) -> bool:
            r = await get_redis_connection()
            # Kiểm tra xem user có nằm trong danh sách đen bị khóa mồm Bot không
            is_bot_muted = await r.sismember("equinox:jail:bot_muted", str(interaction.user.id))
            
            if is_bot_muted:
                # Đặc quyền miễn nhiễm dành riêng cho sếp (Owner)
                env_owner = os.getenv("OWNER_DISCORD_ID")
                if env_owner and interaction.user.id == int(env_owner):
                    return True
                
                await interaction.response.send_message(
                    "❌ **BẠN ĐANG BỊ PHONG TỎA KHỎI MA TRẬN BOT!**\n"
                    "Sếp đã bị Sát thủ Chợ Đen của Tenebris bắt cóc ngầm đêm qua. "
                    "Toàn bộ quyền truy cập và sử dụng mọi lệnh Bot đã bị đóng băng! "
                    "Hãy kiên nhẫn đợi đến khi Luminous thức dậy ban sắc lệnh **Đại Xá Bình Minh** nhé! 🌅",
                    ephemeral=True
                )
                return False
                
            if self.old_check:
                return await self.old_check(interaction)
            return True

    def cog_unload(self):
        self.check_sunrise_amnesty.cancel()

    # ==============================================================================
    # 📡 TÍNH NĂNG 1: SẢNH ĐẠI SỨ QUÁN LIÊN SERVER (BIẾN HÌNH BAN ĐÊM)
    # ==============================================================================
    @app_commands.command(name="embassy-register", description="[ADMIN] Đăng ký kênh hiện tại làm Sảnh Đại Sứ Quán kết nối liên máy chủ")
    @commands.has_permissions(manage_guild=True)
    async def embassy_register(self, interaction: discord.Interaction):
        r = await get_redis_connection()
        # Lưu kênh vào danh mục kết nối trên Redis
        await r.hset("equinox:matrix:embassy_channels", str(interaction.channel.id), str(interaction.guild.id))
        await interaction.response.send_message(
            f"📡 **KẾT NỐI MA TRẬN THÀNH CÔNG:** Kênh {interaction.channel.mention} đã trở thành Sảnh Đại Sứ Quán. "
            f"Mọi tin nhắn gõ tại đây sẽ được đồng bộ xuyên biên giới đến các máy chủ khác!", ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        r = await get_redis_connection()
        # Check xem kênh này có phải sảnh đại sứ quán liên server không
        is_embassy = await r.hexists("equinox:matrix:embassy_channels", str(message.channel.id))
        if not is_embassy:
            return

        # Đọc ca trực thực tế
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if cycle_bytes else "DAY"

        # Thiết lập danh tính mặc định (Ban ngày công khai)
        display_name = message.author.display_name
        avatar_url = message.author.display_avatar.url

        # 🌙 CA ĐÊM (TENEBRIS): KÍCH HOẠT CHẾ ĐỘ "CHỢ ĐEN GIẤU MẶT" ẨN DANH 100%
        if cycle == "NIGHT":
            random.seed(int(message.author.id)) # Giữ cố định 1 bí danh cho 1 người trong đêm
            fake_id = random.randint(10, 99)
            display_name = f"Kẻ Buôn Lậu #{fake_id}"
            avatar_url = "https://i.imgur.com/vI7M6Ad.png" # Ảnh đại diện bóng ma mặc định
            random.seed()

        # Bốc toàn bộ danh sách sảnh đại sứ quán ở các server khác để bắn Webhook qua
        all_embassies = await r.hgetall("equinox:matrix:embassy_channels")
        for ch_id_bytes, g_id_bytes in all_embassies.items():
            target_channel_id = int(ch_id_bytes.decode('utf-8'))
            
            if target_channel_id == message.channel.id:
                continue # Không tự gửi ngược lại chính mình

            target_channel = self.bot.get_channel(target_channel_id)
            if target_channel:
                try:
                    webhooks = await target_channel.webhooks()
                    webhook = discord.utils.get(webhooks, name="Equinox Embassy Bridge")
                    if not webhook:
                        webhook = await target_channel.create_webhook(name="Equinox Embassy Bridge")

                    # Thực hiện bắn dữ liệu xuyên server
                    await webhook.send(
                        content=message.content,
                        username=f"[{message.guild.name}] {display_name}",
                        avatar_url=avatar_url
                    )
                except Exception:
                    pass

    # ==============================================================================
    # ⚔️ TÍNH NĂNG 2: SÁT THỦ ĐÊM KHUYA & ĐẠI XÁ BÌNH MINH (MUTE BOT)
    # ==============================================================================
    @app_commands.command(name="kidnap", description="[CA ĐÊM] Thuê sát thủ Chợ Đen bắt cóc khóa mồm đối tượng khỏi ma trận Bot")
    @app_commands.describe(target="Đối tượng sếp muốn khóa mồm Bot", chi_phi="Số tiền bẩn Aequis bỏ ra để thuê sát thủ (Tối thiểu 1000)")
    async def kidnap_user(self, interaction: discord.Interaction, target: discord.Member, chi_phi: int):
        r = await get_redis_connection()
        user_id = str(interaction.user.id)

        # ⏳ Check ca trực ca đêm
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if cycle_bytes else "DAY"
        if cycle != "NIGHT":
            return await interaction.response.send_message("☀️ Ban ngày Đội trị an Luminous tuần tra gắt lắm sếp! Đợi ca đêm (t!) của Tenebris mở cửa mới thuê được sát thủ ngầm nha.", ephemeral=True)

        if target.id == interaction.user.id:
            return await interaction.response.send_message("❌ Định tự bắt cóc chính mình để trốn nợ à sếp?", ephemeral=True)
        if chi_phi < 1000:
            return await interaction.response.send_message("❌ Sát thủ Chợ Đen không làm việc với giá dưới `1,000 Aequis` đâu sếp!", ephemeral=True)

        # Kiểm tra ví tiền bẩn Aequis
        wallet_key = f"equinox:economy:wallets:{user_id}"
        aequis_bal = int(await r.hget(wallet_key, "aequis") or 0)

        if aequis_bal < chi_phi:
            return await interaction.response.send_message(f"❌ Sếp không đủ tiền bẩn rồi! Ví hiện tại chỉ có `{aequis_bal}` Aequis.", ephemeral=True)

        # Khấu trừ tiền bẩn và nhét nạn nhân vào ngục tối cách ly Bot
        await r.hincrby(wallet_key, "aequis", -chi_phi)
        await r.sadd("equinox:jail:bot_muted", str(target.id))

        await interaction.response.send_message(
            f"🤫 **PHI VỤ ĐÃ KÝ KẾT TRONG BÓNG TỐI:**\n"
            f"• Sếp đã bỏ ra `{chi_phi:,} Aequis` thuê Sát Thủ Bóng Đêm.\n"
            f"🚷 Đối tượng {target.mention} đã bị tóm cổ và **KHÓA TOÀN BỘ QUYỀN SỬ DỤNG BOT**!"
        )

    # 🕒 MẠCH CHẠY NGẦM: ĐẠI XÁ BÌNH MINH (Quét mỗi phút)
    @tasks.loop(minutes=1)
    async def check_sunrise_amnesty(self):
        r = await get_redis_connection()
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if cycle_bytes else "DAY"

        # Nếu bước sang Ca Ngày (DAY), Luminous thực hiện Đại Xá cứu rỗi thiên hạ
        if cycle == "DAY":
            has_jailed = await r.scard("equinox:jail:bot_muted")
            if has_jailed > 0:
                # Xóa sổ toàn bộ danh sách bị Mute Bot ngay lập tức
                await r.delete("equinox:jail:bot_muted")
                print("🌅 [LUMINOUS LORE] Bình minh lên, Thần điện kích hoạt Đại Xá Thiên Hạ! Giải thoát toàn bộ linh hồn bị bắt cóc.")

    @check_sunrise_amnesty.before_loop
    async def before_amnesty(self):
        await self.bot.wait_until_ready()

    # ==============================================================================
    # 🎰 TÍNH NĂNG 3: VÒNG QUAY MA TRẬN ĐỎ ĐEN RỬA TIỀN (TIÊU THỦ AEQUIS)
    # ==============================================================================
    @app_commands.command(name="matrix-wheel", description="[CHỢ ĐEN] Đặt cược 1,000 Aequis quay vòng số ma trận để rửa tiền sạch / trúng hũ độc đắc")
    async def matrix_wheel(self, interaction: discord.Interaction):
        r = await get_redis_connection()
        user_id = str(interaction.user.id)
        wallet_key = f"equinox:economy:wallets:{user_id}"

        # Chi phí cố định cho mỗi lượt xoay vận mệnh
        entry_cost = 1000
        aequis_bal = int(await r.hget(wallet_key, "aequis") or 0)

        if aequis_bal < entry_cost:
            return await interaction.response.send_message(f"❌ Cửa cược yêu cầu `1,000 Aequis (Tiền bẩn)`. Ví của sếp hiện chỉ có `{aequis_bal}`.", ephemeral=True)

        # Trừ tiền đặt cược trước khi quay
        await r.hincrby(wallet_key, "aequis", -entry_cost)

        # 🎰 THUẬT TOÁN ĐỘ TRỰC QUAN ĐỘC QUYỀN (Độ phân giải 0.01% -> 1/10000)
        roll = random.randint(1, 10000)
        
        # Thiết lập bảng tra cứu tỷ lệ nhân phẩm theo đúng cấu hình sếp giao
        if roll == 1: # 1/10000 = 0.01% TRÚNG ĐỘC ĐẮC 10 TRIỆU CẢ 2 LOẠI TIỀN
            await r.hincrby(wallet_key, "aequor", 10000000)
            await r.hincrby(wallet_key, "aequis", 10000000)
            
            embed = discord.Embed(title="🚨 ĐẠI ĐỊA CHẤN: HŨ ĐỘC ĐẮC MA TRẬN ĐÃ NỔ!!! 🚨", color=0xFF00FF)
            embed.description = f"🎉 Thiên địa đảo lộn! Người chơi {interaction.user.mention} vừa quay trúng ô tỷ lệ **`0.01%`**!\n\n" \
                                f"💰 **PHẦN THƯỞNG TỐI CAO:**\n" \
                                f"• Nhận ngay: `+10,000,000 Aequor (Tiền sạch)` ☀️\n" \
                                f"• Nhận ngay: `+10,000,000 Aequis (Tiền bẩn)` 🔮"
            embed.set_footer(text="Uỷ ban quản lý ngân khố Equinox cạn kiệt tài nguyên!")
            return await interaction.response.send_message(embed=embed)

        elif roll <= 101: # 100/10000 = 1% RỦI RO XÓA SỔ TOÀN BỘ TIỀN (SẠCH + BẨN)
            await r.hset(wallet_key, "aequor", "0")
            await r.hset(wallet_key, "aequis", "0")
            
            embed = discord.Embed(title="🔥 KHỦNG HOẢNG TÀI CHÍNH: TRẮNG TAY! 🔥", color=0xFF0000)
            embed.description = f"🚨 Quét sạch ma trận! {interaction.user.mention} quay trúng ô đen đủi **`1%`**.\n" \
                                f"Hệ thống bảo mật tối cao quét phát hiện vết tích. Toàn bộ tài sản ví **Aequor và Aequis đều bị bốc hơi về 0**!"
            return await interaction.response.send_message(embed=embed)

        elif roll <= 601: # 500/10000 = 5% RỦI RO XÓA SỔ TOÀN BỘ TIỀN ĐEN
            await r.hset(wallet_key, "aequis", "0")
            
            embed = discord.Embed(title="⚖️ CẢNH SÁT QUÉT SẠCH TIỀN BẨN! ⚖️", color=0xFF9900)
            embed.description = f"⚠️ Đột kích bất ngờ! {interaction.user.mention} quay trúng ô rủi ro **`5%`**.\n" \
                                f"Đội trị an tuần tra tịch thu và **tiêu hủy toàn bộ số tiền đen Aequis** đang có trong ví. May mắn ví tiền sạch Aequor vẫn còn nguyên!"
            return await interaction.response.send_message(embed=embed)

        else: # 93.99% CÒN LẠI: CÁC PHẦN THƯỞNG NHỎ CHỈ LIÊN QUAN ĐẾN TIỀN
            sub_roll = random.randint(1, 3)
            if sub_roll == 1: # Rửa tiền thành công sang ví sạch
                win_amt = random.randint(200, 800)
                await r.hincrby(wallet_key, "aequor", win_amt)
                title = "☀️ RỬA TIỀN THÀNH CÔNG ☀️"
                reward_msg = f"`+ {win_amt} Aequor (Star)`"
                color = 0x00FFFF
            elif sub_roll == 2: # Trúng thêm tiền bẩn cày vốn
                win_amt = random.randint(150, 600)
                await r.hincrby(wallet_key, "aequis", win_amt)
                title = "🔮 THU HOẠCH CHỢ ĐEN 🔮"
                reward_msg = f"`+ {win_amt} Aequis (Star)`"
                color = 0x4B0082
            else: # Khớp lệnh hoàn vốn cược
                await r.hincrby(wallet_key, "aequor", 2000)
                title = "🔄 LỆNH KHỚP HOÀN VỐN X2 🔄"
                reward_msg = f"`+ 2,000 Aequor (Tiền sạch)`"
                color = 0x00FF88

            # Đọc số dư mới sau khi trúng thưởng nhỏ
            new_aequor = int(await r.hget(wallet_key, "aequor") or 0)
            new_aequis = int(await r.hget(wallet_key, "aequis") or 0)

            embed = discord.Embed(title=title, color=color)
            embed.description = f"🎰 {interaction.user.mention} vừa thực hiện vòng quay vận mệnh ma trận!\n" \
                                f"🎁 Phần thưởng nhận được: **{reward_msg}**\n\n" \
                                f"💳 **CẬP NHẬT SỐ DƯ TÀI KHOẢN:**\n" \
                                f"• Ví Sạch Ban Ngày: `{new_aequor:,} Aequor` ☀️\n" \
                                f"• Ví Đen Ban Đêm: `{new_aequis:,} Aequis` 🔮"
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EquinoxCoreGameplay(bot))
