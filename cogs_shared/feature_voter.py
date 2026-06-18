import os
import discord
from discord import app_commands
from discord.ext import commands
from database.redis_client import get_redis_connection

# ==============================================================================
# 🔘 DISCORD VIEW: GIAO DIỆN NÚT BẤM BÌNH CHỌN (ĐÃ FIX LỖI TIME OUT)
# ==============================================================================
class VotingButtons(discord.ui.View):
    def __init__(self, bot, vote_id: str, opt1: str, opt2: str, opt3: str, timeout: int, channel, ping_role=None, ping_user=None, author_name=""):
        # Gán timeout trực tiếp cho View xử lý tự động
        super().__init__(timeout=timeout)
        self.bot = bot
        self.vote_id = vote_id
        self.opt1 = opt1
        self.opt2 = opt2
        self.opt3 = opt3
        self.channel = channel
        self.ping_role = ping_role
        self.ping_user = ping_user
        self.author_name = author_name
        self.message = None # Sẽ gán sau khi gửi tin nhắn thành công

        # Đổi nhãn nút bấm theo tham số truyền vào
        self.button_a.label = opt1
        self.button_b.label = opt2
        self.button_c.label = opt3

    async def _handle_vote(self, interaction: discord.Interaction, option_index: str, option_name: str):
        r = await get_redis_connection()
        user_id = str(interaction.user.id)
        
        # Check xem user đã vote kèo này chưa
        has_voted = await r.hexists(f"equinox:vote:user_choices:{self.vote_id}", user_id)
        if has_voted:
            current_vote = await r.hget(f"equinox:vote:user_choices:{self.vote_id}", user_id)
            return await interaction.response.send_message(
                f"❌ Sếp đã bỏ phiếu cho lựa chọn `{current_vote.decode('utf-8')}` trước đó rồi, không được gian lận vote 2 lần đâu nha!", 
                ephemeral=True
            )

        # Lưu lựa chọn cá nhân và tăng bộ đếm tổng của lựa chọn đó lên Redis
        await r.hset(f"equinox:vote:user_choices:{self.vote_id}", user_id, option_name)
        await r.hincrby(f"equinox:vote:counters:{self.vote_id}", option_index, 1)
        
        await interaction.response.send_message(f"✅ Sếp đã bình chọn thành công cho: **`{option_name}`**", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.primary, custom_id="vote_opt_1")
    async def button_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, "1", button.label)

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="vote_opt_2")
    async def button_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, "2", button.label)

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="vote_opt_3")
    async def button_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, "3", button.label)

    # 📊 KHI HẾT GIỜ (TIMEOUT): Sự kiện tự động kích hoạt cực kỳ chính xác của Discord.py
    async def on_timeout(self):
        r = await get_redis_connection()

        # Khóa toàn bộ nút bấm trên Embed gốc
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

        # Bốc kết quả cuối cùng từ RAM Redis lên xử lý dữ liệu
        counts = await r.hgetall(f"equinox:vote:counters:{self.vote_id}")
        v1 = int(counts.get(b"1", b"0").decode('utf-8'))
        v2 = int(counts.get(b"2", b"0").decode('utf-8'))
        v3 = int(counts.get(b"3", b"0").decode('utf-8'))
        total_votes = v1 + v2 + v3

        # Phân tích xem ai thắng kèo
        results = [(v1, self.opt1), (v2, self.opt2), (v3, self.opt3)]
        results.sort(reverse=True, key=lambda x: x[0]) # Xếp hạng số phiếu cao nhất lên đầu
        
        winner_text = f"🏆 **Tính năng chiến thắng:** `{results[0][1]}` với `{results[0][0]}` phiếu bầu!" if total_votes > 0 else "❌ Không có ai thèm bỏ phiếu bầu nào hết!"

        # Tạo Embed công bố kết quả chung cuộc
        result_embed = discord.Embed(
            title="📊 KẾT QUẢ CUỘC TRƯNG CẦU DÂN Ý 📊",
            description=f"Cổng bình chọn mã số `#{self.vote_id[-6:]}` chính thức đóng cửa!\n\n"
                        f"🥇 **Hạng 1:** `{results[0][1]}` — `{results[0][0]}` phiếu\n"
                        f"🥈 **Hạng 2:** `{results[1][1]}` — `{results[1][0]}` phiếu\n"
                        f"🥉 **Hạng 3:** `{results[2][1]}` — `{results[2][0]}` phiếu\n\n"
                        f"🏁 {winner_text}",
            color=0xFFD700
        )
        result_embed.set_footer(text=f"Tổng số phiếu đã ghi nhận trên hệ thống: {total_votes} lượt. Mở bởi: {self.author_name}")

        # Xử lý chuỗi dữ liệu PING theo yêu cầu setup ban đầu của sếp
        ping_string = ""
        if self.ping_role:
            ping_string += f" {self.ping_role.mention}"
        if self.ping_user:
            ping_string += f" {self.ping_user.mention}"

        # Bắn kết quả kèm lệnh PING chuẩn chỉ vào thẳng kênh gõ lệnh
        try:
            await self.channel.send(content=ping_string if ping_string else None, embed=result_embed)
        except Exception:
            pass

        # Dọn dẹp dữ liệu rác trên Redis để tiết kiệm RAM đám mây
        await r.delete(f"equinox:vote:counters:{self.vote_id}")
        await r.delete(f"equinox:vote:user_choices:{self.vote_id}")


# ==============================================================================
# 📊 COG SYSTEM: QUẢN LÝ LỆNH BÌNH CHỌN PHÂN QUYỀN
# ==============================================================================
class FeatureVoter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vote-feature", description="[STAFF / EVENT] Mở cuộc trưng cầu dân ý bình chọn tính năng mới cho Server")
    @app_commands.describe(
        tinh_nang_1="Tên tính năng lựa chọn 1",
        tinh_nang_2="Tên tính năng lựa chọn 2",
        tinh_nang_3="Tên tính năng lựa chọn 3",
        so_phut="Số phút cuộc bình chọn này sẽ diễn ra trước khi đóng cửa",
        ping_role="Role muốn ping khi kết thúc cuộc bình chọn (Tùy chọn)",
        ping_user="User muốn ping khi kết thúc cuộc bình chọn (Tùy chọn)"
    )
    async def vote_feature_cmd(
        self, 
        interaction: discord.Interaction, 
        tinh_nang_1: str, 
        tinh_nang_2: str, 
        tinh_nang_3: str, 
        so_phut: int,
        ping_role: discord.Role = None,
        ping_user: discord.User = None
    ):
        r = await get_redis_connection()
        user_id = interaction.user.id

        # 🛡️ KIỂM TRA PHÂN QUYỀN: Cho phép Owner, Event Manager (qua role tên 'Event Manager') hoặc quyền Quản lý Server
        env_owner = os.getenv("OWNER_DISCORD_ID")
        is_owner = (env_owner and user_id == int(env_owner)) or await r.sismember("equinox:staff:owners", user_id)
        has_event_role = discord.utils.get(interaction.user.roles, name="Event Manager") is not None
        has_admin_perm = interaction.user.guild_permissions.manage_guild

        if not (is_owner or has_event_role or has_admin_perm):
            return await interaction.response.send_message("❌ Sếp không thuộc Đội ngũ quản lý Event nên không có sắc lệnh mở cổng bình chọn này!", ephemeral=True)

        if so_phut <= 0:
            return await interaction.response.send_message("❌ Thời gian đóng bình chọn phải lớn hơn 0 phút sếp ơi!", ephemeral=True)

        # Đọc ca trực thực tế
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if cycle_bytes else "DAY"
        
        # Khởi tạo ID cuộc bình chọn dựa trên timestamp
        vote_id = f"{interaction.guild.id}:{int(interaction.created_at.timestamp())}"
        
        # Khởi tạo bộ đếm 0 phiếu trên Redis cho 3 option
        await r.hset(f"equinox:vote:counters:{vote_id}", mapping={"1": "0", "2": "0", "3": "0"})

        # Đóng gói giao diện biểu thị hạch tâm cuộc gọi bình chọn
        embed = discord.Embed(
            title="🗳️ TRƯNG CẦU DÂN Ý: BÌNH CHỌN TÍNH NĂNG MỚI 🗳️",
            description=f"Hệ thống Ma trận cần ý kiến đóng góp từ các sếp để nâng cấp cấu trúc! "
                        f"Nhấn vào các nút bấm bên dưới để gửi phiếu bầu ẩn danh lên Redis.\n\n"
                        f"🔹 **Lựa chọn 1:** `{tinh_nang_1}`\n"
                        f"🔹 **Lựa chọn 2:** `{tinh_nang_2}`\n"
                        f"🔹 **Lựa chọn 3:** `{tinh_nang_3}`",
            color=0x00FF88 if cycle == "DAY" else 0x4B0082
        )
        embed.add_field(name="⏱️ Thời hạn đóng hộc thư", value=f"Sẽ tự động kết thúc sau `{so_phut}` phút.", inline=False)
        embed.set_footer(text=f"Mở bởi điều hành viên: {interaction.user.display_name}")

        # Tính số giây timeout
        timeout_seconds = so_phut * 60
        
        # Khởi tạo View nút bấm, truyền toàn bộ bối cảnh qua View để on_timeout tự bốc xử lý
        view = VotingButtons(
            bot=self.bot,
            vote_id=vote_id,
            opt1=tinh_nang_1,
            opt2=tinh_nang_2,
            opt3=tinh_nang_3,
            timeout=timeout_seconds,
            channel=interaction.channel,
            ping_role=ping_role,
            ping_user=ping_user,
            author_name=interaction.user.display_name
        )

        # Bắn Embed bình chọn ra sảnh chat
        await interaction.response.send_message(embed=embed, view=view)
        
        # Gán ngược message vừa tạo vào view để sau này on_timeout lôi ra sửa giao diện (khóa nút)
        view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(FeatureVoter(bot))
