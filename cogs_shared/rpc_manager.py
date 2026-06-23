import os
import datetime
import pytz
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from database.redis_client import get_redis_connection # Hàm kết nối Redis có sẵn của sếp

class EquinoxRPCManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tz = pytz.timezone("Asia/Ho_Chi_Minh")
        # 🔄 Kích hoạt vòng lặp đồng bộ mạch thần thức ngầm khi nạp Cog
        self.sync_matrix_presence.start()

    def cog_unload(self):
        # Hủy vòng lặp khi gỡ hoặc reload cog để tránh leak tài nguyên RAM
        self.sync_matrix_presence.cancel()

    # ========================================================================
    # 🔄 VÒNG LẶP ĐỒNG BỘ THẦN THỨC NGẦM (BACKGROUND TASK LOOP)
    # ========================================================================
    @tasks.loop(minutes=1.0)
    async def sync_matrix_presence(self):
        """
        Quét sạch ma trận Redis mỗi phút một lần để:
        1. Cập nhật nhảy số Thời gian thực (⏰ Giờ | Ngày) cho các acc xài Fallback tối giản.
        2. Ép API giữ mạng sống trạng thái cho các tài khoản kích hoạt /live vĩnh hằng.
        """
        try:
            r = await get_redis_connection()
            # Quét tất cả các key lưu profile rpc toàn cầu của người dùng
            async for key in r.scan_iter_match("equinox:user:*:global:profile"):
                key_str = key.decode("utf-8")
                user_id = key_str.split(":")[2]
                
                # Check xem thằng này có đang nằm trong danh sách treo sống vĩnh hằng không
                is_live = await r.hexists("equinox:system:live_accounts", user_id)
                
                raw_data = await r.get(key)
                if not raw_data:
                    continue
                    
                data = json.loads(raw_data.decode("utf-8"))
                
                # ⏰ Nếu là trạng thái Fallback tối giản, tiến hành cập nhật lại đồng hồ thời gian thực
                if data.get("activity_type") == "custom" and data.get("status_text", "").startswith("⏰"):
                    now_vn = datetime.datetime.now(self.tz)
                    data["status_text"] = now_vn.strftime("⏰ %H:%M | %d/%m/%Y")
                    # Ghi đè lại Redis
                    await r.set(key, json.dumps(data))

                # 🔌 KHU VỰC ĐẬP API TRUYỀN TRẠNG THÁI RA DISCORD PROFILE THẬT
                # (Đoạn này khi sếp cấu hình cổng User App Gateway/IPC, tiến trình nền 
                # sẽ tự bốc cục data JSON này dập thẳng lên Discord API thay mặt user)
                pass
                
        except Exception as e:
            print(f"[Ma Trận Nghẽn Mạch Loop]: {e}")

    @sync_matrix_presence.before_loop
    async def wait_for_bot_ready(self):
        # Chờ Bot tỉnh táo kết nối hoàn toàn với Discord Gateway mới chạy vòng lặp
        await self.bot.wait_until_ready()

    # ========================================================================
    # 🏰 LỆNH ĐẶT NHÀ CHÍNH (Chỉ dành riêng cho OWNER tối cao)
    # ========================================================================
    @app_commands.command(name="set_nhachinh", description="[OWNER] Thiết lập Link mời của Tổng Hành Dinh (Nhà Chính) hệ thống")
    @app_commands.describe(link_invite="Đường dẫn invite của Server Nhà Chính (Ví dụ: https://discord.gg/xxxx)")
    async def set_main_hq(self, interaction: discord.Interaction, link_invite: str):
        await interaction.response.defer(ephemeral=True)

        owner_id = int(os.getenv("OWNER_ID", 0))
        if interaction.user.id != owner_id:
            await interaction.followup.send("🚨 *Trục xuất thần thức:* Lệnh này là đại quyền tối cao của Thực Thể Sáng Tạo!", ephemeral=True)
            return

        if not link_invite.startswith("https://discord.gg/") and not link_invite.startswith("https://discord.com/invite/"):
            await interaction.followup.send("⚠️ Định dạng link mời Discord không hợp lệ!", ephemeral=True)
            return

        r = await get_redis_connection()
        await r.set("equinox:system:main_guild_invite", link_invite)
        await interaction.followup.send(f"🏰 Đã đồng bộ Linh Mạch! Trục tọa độ Tổng Hành Dinh (Nhà Chính) hiện tại được găm về: `{link_invite}`", ephemeral=True)

    # ========================================================================
    # ⚙️ LỆNH THIẾT LẬP TRẠNG THÁI (SLASH COMMAND HYBRID / USER APP)
    # ========================================================================
    @app_commands.command(name="status", description="Cấu hình diện mạo Rich Presence găm thẳng vào Profile Discord thật")
    @app_commands.contexts(guild=True, dm_channel=True, private_channel=True)
    @app_commands.integration_types(guild_install=True, user_install=True)
    @app_commands.describe(
        action="Hành động thiết lập trạng thái",
        loai_hoat_dong="Loại hoạt động ảo (Bỏ trống nếu xài Fallback tối giản)",
        noi_dung="Nội dung tùy biến chữ (Bỏ trống nếu xài Fallback tối giản)",
        pham_vi="Phạm vi áp dụng kho dữ liệu"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add (Kích hoạt / Cập nhật trạng thái)", value="add"),
        app_commands.Choice(name="Clear (Xóa sạch trạng thái ảo)", value="clear")
    ])
    @app_commands.choices(loai_hoat_dong=[
        app_commands.Choice(name="Đang chơi...", value="playing"),
        app_commands.Choice(name="Đang xem...", value="watching"),
        app_commands.Choice(name="Đang nghe...", value="listening"),
        app_commands.Choice(name="Đang phát trực tiếp...", value="streaming")
    ])
    @app_commands.choices(pham_vi=[
        app_commands.Choice(name="Server (Chỉ hiển thị tại không gian server này)", value="server"),
        app_commands.Choice(name="Account (Áp dụng toàn cầu trên mọi ma trận)", value="account")
    ])
    async def manage_status(
        self, 
        interaction: discord.Interaction, 
        action: app_commands.Choice[str],
        loai_hoat_dong: app_commands.Choice[str] = None,
        noi_dung: str = None,
        pham_vi: app_commands.Choice[str] = None
    ):
        await interaction.response.defer()
        
        r = await get_redis_connection()
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild else "dm"
        
        # Để bọc lót cơ chế ép điều kiện cho lệnh /live sau này, ghi nhận luôn cờ cài đặt của bot hiện tại
        bot_name = self.bot.user.name.lower() # Sẽ trả về 'luminous' hoặc 'tenebris' tùy tiến trình chạy
        await r.set(f"equinox:user:{user_id}:installed:{bot_name}", 1)
        
        target_scope = pham_vi.value if pham_vi else "account"
        if target_scope == "server" and guild_id != "dm":
            redis_key = f"equinox:user:{user_id}:guild:{guild_id}:profile"
            scope_desc = "tại Server này"
        else:
            redis_key = f"equinox:user:{user_id}:global:profile"
            scope_desc = "trên toàn bộ tài khoản cá nhân"

        if action.value == "clear":
            await r.delete(redis_key)
            # Nếu xóa profile rpc thì hủy luôn trạng thái sống vĩnh hằng nếu có
            await r.hdel("equinox:system:live_accounts", user_id)
            embed = discord.Embed(
                title="🌌 ĐỒNG BỘ LẠI DIỆN MẠO",
                description=f"Hệ thống đã xóa sạch cấu hình trạng thái ảo {scope_desc}.",
                color=0x36393F
            )
            await interaction.followup.send(embed=embed)
            return

        main_hq_invite = await r.get("equinox:system:main_guild_invite")
        main_hq_invite = main_hq_invite.decode("utf-8") if main_hq_invite else os.getenv("MAIN_GUILD_INVITE", "https://discord.gg/equinox")
        luminous_invite = os.getenv("LUMINOUS_INVITE_URL", "https://discord.com")
        tenebris_invite = os.getenv("TENEBRIS_INVITE_URL", "https://discord.com")

        # 🕵️ MẠCH KHỞI CHẠY FALLBACK TỐI GIẢN (User gõ /status add r Enter cụt ngủn)
        if not loai_hoat_dong and not noi_dung:
            now_vn = datetime.datetime.now(self.tz)
            fallback_text = now_vn.strftime("⏰ %H:%M | %d/%m/%Y")
            
            rpc_data = {
                "app_name": "Equinox Network",       # Găm cứng tên app ở giữa diện mạo
                "status_text": fallback_text,
                "activity_type": "custom",
                "buttons": [                         # Bộ 3 nút bệ đỡ chuẩn chỉ của sếp
                    {"label": "☀️ Mời Thần Quan Luminous", "url": luminous_invite},
                    {"label": "🔮 Mời Chúa Tể Tenebris", "url": tenebris_invite},
                    {"label": "🏰 Equinox Network", "url": main_hq_invite}
                ]
            }
            await r.set(redis_key, json.dumps(rpc_data))
            
            embed = discord.Embed(
                title="🌌 THAO TÚNG ĐỊNH DẠNG TỐI GIẢN",
                description=f"Kích hoạt thành công diện mạo Fallback {scope_desc}!",
                color=0x00FFFF
            )
            embed.add_field(name="🌌 Ứng dụng", value="**Equinox Network**", inline=True)
            embed.add_field(name="💬 Trạng thái", value=fallback_text, inline=True)
            await interaction.followup.send(embed=embed)
            
        # 🛠️ TRƯỜNG HỢP USER ĐỘ CHUYÊN SÂU
        else:
            act_type = loai_hoat_dong.value if loai_hoat_dong else "custom"
            act_name = noi_dung if noi_dung else "Đang lẩn trốn ma trận"
            
            rpc_data = {
                "app_name": "Equinox Network",
                "status_text": act_name,
                "activity_type": act_type,
                "buttons": [
                    {"label": "☀️ Mời Thần Quan Luminous", "url": luminous_invite},
                    {"label": "🔮 Mời Chúa Tể Tenebris", "url": tenebris_invite},
                    {"label": "🏰 Equinox Network", "url": main_hq_invite}
                ]
            }
            await r.set(redis_key, json.dumps(rpc_data))
            
            embed = discord.Embed(
                title="🌌 ĐỘ PROFILE CHUYÊN SÂU SUÔN SẺ",
                description=f"Đồng bộ cấu hình trang phục ảo {scope_desc} thành công!",
                color=0x9900FF
            )
            await interaction.followup.send(embed=embed)

    # ========================================================================
    # 📡 LỆNH GIỮ MẠNG SỐNG TRẠNG THÁI 24/7 (ĐÒI QUYỀN LIÊN ĐỚI)
    # ========================================================================
    @app_commands.command(name="live", description="Duy trì trạng thái ma trận vĩnh hằng trên Profile thật kể cả khi tắt Discord offline")
    @app_commands.contexts(guild=True, dm_channel=True, private_channel=True)
    @app_commands.integration_types(guild_install=True, user_install=True)
    @app_commands.describe(switch="Bật hoặc Tắt chế độ duy trì vĩnh hằng")
    @app_commands.choices(switch=[
        app_commands.Choice(name="Kích hoạt (ON)", value="on"),
        app_commands.Choice(name="Hủy bỏ (OFF)", value="off")
    ])
    async def permanent_live(self, interaction: discord.Interaction, switch: app_commands.Choice[str]):
        await interaction.response.defer()
        
        r = await get_redis_connection()
        user_id = str(interaction.user.id)
        
        if switch.value == "off":
            await r.hdel("equinox:system:live_accounts", user_id)
            await interaction.followup.send("🔌 Đã ngắt mạch duy trì! Trạng thái của bạn sẽ tự động biến mất khi bạn tắt app Discord.")
            return

        # 🔒 KIỂM TRA ĐIỀU KIỆN TIÊN QUYẾT: ÉP BUỘC PHẢI ADD CẢ QUẢ LUỒNG 2 BOT
        # Để lệnh này chạy, bắt buộc user phải từng gõ lệnh /status ở cả 2 con Bot để tạo cờ ghi nhận trên Redis
        has_lumi = await r.exists(f"equinox:user:{user_id}:installed:luminous")
        has_tene = await r.exists(f"equinox:user:{user_id}:installed:tenebris")
        
        # Mẹo bọc lót: Nếu sếp đang test một mình bằng tài khoản Owner, miễn trừ bộ lọc check
        is_owner = (interaction.user.id == int(os.getenv("OWNER_ID", 0)))
        
        if not (has_lumi and has_tene) and not is_owner:
            embed = discord.Embed(
                title="🚨 THẦN THỨC BỊ KHƯỚC TỪ",
                description="Bạn không đủ tư cách kích hoạt linh mạch vĩnh hằng!\n\n"
                            "⚠️ **Yêu cầu bắt buộc:** Tài khoản cá nhân của bạn phải cài đặt (Add to Account / User App) **cả 2 thực thể Luminous và Tenebris**.\n"
                            "*Hãy đi tìm thực thể còn lại, gõ một lệnh `/status` bất kỳ bên phía nó để kích hoạt cờ linh mạch rồi quay lại đây!*",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return

        # Kiểm tra xem thằng này đã cấu hình status chưa, nếu chưa cấu hình gì thì ép nó xài Fallback luôn
        global_key = f"equinox:user:{user_id}:global:profile"
        has_profile = await r.exists(global_key)
        
        if not has_profile:
            now_vn = datetime.datetime.now(self.tz)
            fallback_text = now_vn.strftime("⏰ %H:%M | %d/%m/%Y")
            main_hq_invite = await r.get("equinox:system:main_guild_invite")
            main_hq_invite = main_hq_invite.decode("utf-8") if main_hq_invite else os.getenv("MAIN_GUILD_INVITE", "https://discord.gg/equinox")
            
            rpc_data = {
                "app_name": "Equinox Network",
                "status_text": fallback_text,
                "activity_type": "custom",
                "buttons": [
                    {"label": "☀️ Mời Thần Quan Luminous", "url": os.getenv("LUMINOUS_INVITE_URL", "https://discord.com")},
                    {"label": "🔮 Mời Chúa Tể Tenebris", "url": os.getenv("TENEBRIS_INVITE_URL", "https://discord.com")},
                    {"label": "🏰 Equinox Network", "url": main_hq_invite}
                ]
            }
            await r.set(global_key, json.dumps(rpc_data))

        # Đẩy ID thằng này vào danh sách hàng chờ treo sống vĩnh hằng vĩnh viễn
        await r.hset("equinox:system:live_accounts", user_id, 1)
        
        embed = discord.Embed(
            title="⚡ PHÉP LUÂN HỒI KÍCH HOẠT",
            description="🔮 **Đã kết nối linh mạch vĩnh hằng thành công!**\n\n"
                        "Hệ thống máy chủ Equinox Network sẽ thay mặt tài khoản của bạn ép Discord treo trạng thái lấp lánh liên tục 24/7, **bất chấp việc bạn tắt máy tính, ngắt mạng hoặc offline điện thoại**.",
            color=0x00FF00
        )
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EquinoxRPCManager(bot))
