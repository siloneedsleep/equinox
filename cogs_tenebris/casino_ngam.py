import discord
from discord.ext import commands
import random

from config.settings import COLORS
from database.redis_client import get_redis_connection

# ==========================================
# 🃏 GIAO DIỆN UI NÚT BẤM BLACKJACK
# ==========================================
class BlackjackView(discord.ui.View):
    def __init__(self, player, bet_amount, player_hand, dealer_hand, deck, redis_conn):
        super().__init__(timeout=60)
        self.player = player
        self.bet_amount = bet_amount
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.redis = redis_conn

    def calculate_total(self, hand):
        total = 0
        aces = 0
        for card in hand:
            if card in ['J', 'Q', 'K']:
                total += 10
            elif card == 'A':
                aces += 1
            else:
                total += int(card)
        
        for _ in range(aces):
            if total + 11 <= 21:
                total += 11
            else:
                total += 1
        return total

    async def end_game(self, interaction, result, multiplier=2.0):
        for child in self.children:
            child.disabled = True
        
        user_key = f"equinox:user:{self.player.id}"
        
        if result == "WIN":
            win_amount = int(self.bet_amount * multiplier)
            profit = win_amount - self.bet_amount
            await self.redis.hincrby(user_key, "balance_dirty", profit)
            color = COLORS["tenebris_action"]
            title = "🃏 BLACKJACK - THẮNG ĐẬM!"
            desc = f"Chúc mừng <@{self.player.id}>! Nhà cái đền mạng **+{profit:,} Star** bẩn!"
        elif result == "LOSE":
            await self.redis.hincrby(user_key, "balance_dirty", -self.bet_amount)
            color = COLORS["tenebris_error"]
            title = "💀 BLACKJACK - TRẮNG TAY!"
            desc = f"Gà! <@{self.player.id}> vừa cúng cho sòng bạc **-{self.bet_amount:,} Star** bẩn."
        else: # TIE
            color = 0x808080
            title = "🤝 BLACKJACK - HÒA!"
            desc = f"Nhà cái và <@{self.player.id}> bằng điểm. Trả lại tiền cược **{self.bet_amount:,} Star**."

        p_total = self.calculate_total(self.player_hand)
        d_total = self.calculate_total(self.dealer_hand)

        embed = discord.Embed(title=title, description=desc, color=color)
        embed.add_field(name=f"🃏 Bài của bạn ({p_total})", value=" ".join(str(x) for x in self.player_hand), inline=True)
        embed.add_field(name=f"🕴️ Nhà cái ({d_total})", value=" ".join(str(x) for x in self.dealer_hand), inline=True)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Rút Bài (Hit)", style=discord.ButtonStyle.primary, emoji="👇")
    async def hit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message("Không phải sới bạc của mày, cút!", ephemeral=True)
        
        self.player_hand.append(self.deck.pop())
        p_total = self.calculate_total(self.player_hand)

        if p_total > 21:
            await self.end_game(interaction, "LOSE")
        else:
            embed = interaction.message.embeds[0]
            embed.set_field_at(0, name=f"🃏 Bài của bạn ({p_total})", value=" ".join(str(x) for x in self.player_hand), inline=True)
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Dằn Bài (Stand)", style=discord.ButtonStyle.danger, emoji="✋")
    async def stand_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message("Không phải sới bạc của mày, cút!", ephemeral=True)
        
        p_total = self.calculate_total(self.player_hand)
        d_total = self.calculate_total(self.dealer_hand)

        # Nhà cái rút bài nếu tổng điểm dưới 17
        while d_total < 17:
            self.dealer_hand.append(self.deck.pop())
            d_total = self.calculate_total(self.dealer_hand)

        if d_total > 21 or p_total > d_total:
            await self.end_game(interaction, "WIN")
        elif d_total > p_total:
            await self.end_game(interaction, "LOSE")
        else:
            await self.end_game(interaction, "TIE")

# ==========================================
# ⚙️ MODULE CHÍNH: SÒNG BẠC CHỢ ĐEN CA ĐÊM
# ==========================================
class CasinoNgam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🎲 1. GAME TÀI XỈU (TĂNG TỶ LỆ NỔ HŨ)
    @commands.command(name="tx", aliases=["taixiu"])
    async def play_tx(self, ctx, choice: str, amount: str):
        choice = choice.lower()
        if choice not in ["tai", "t", "xiu", "x"]:
            return await ctx.send("Chọn [tài/t] hoặc [xỉu/x] thôi thằng mù!")
        
        is_tai = choice in ["tai", "t"]
        
        r = await get_redis_connection()
        user_key = f"equinox:user:{ctx.author.id}"
        
        dirty_bal = int(await r.hget(user_key, "balance_dirty") or 0)
        
        if amount.lower() == "all":
            bet_amount = dirty_bal
        else:
            try:
                bet_amount = int(amount)
            except ValueError:
                return await ctx.send("Nhập số tiền đàng hoàng xem nào!")

        if bet_amount <= 0:
            return await ctx.send("Định đánh bạc bằng không khí à?")
        
        if bet_amount > dirty_bal:
            return await ctx.send(f"Mày chỉ có **{dirty_bal:,} Star** bẩn thôi! Bốc phét ít thôi!")

        # Cơ chế xúc xắc
        d1, d2, d3 = random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)
        total = d1 + d2 + d3
        result_is_tai = total >= 11
        
        # Đặc quyền Partner: Tăng tỷ lệ nổ hũ nếu là server VIP
        jackpot_chance = 0.05
        partner_tier = int(await r.hget(f"equinox:partner:{ctx.guild.id}", "tier") or 0)
        if partner_tier >= 2:
            jackpot_chance = 0.10 # Tăng lên 10% nổ hũ nếu là VIP Partner
            
        is_jackpot = random.random() < jackpot_chance 
        
        if is_tai == result_is_tai:
            multiplier = 3 if is_jackpot else 2
            win_amount = bet_amount * multiplier
            profit = win_amount - bet_amount
            await r.hincrby(user_key, "balance_dirty", profit)
            
            title = "🎉 NỔ HŨ TÀI XỈU!" if is_jackpot else "🎲 TÀI XỈU - HÚP!"
            color = COLORS["tenebris_action"]
            desc = f"Xúc xắc đổ: **{d1} - {d2} - {d3} = {total}** ({'TÀI' if result_is_tai else 'XỈU'})\nChúc mừng <@{ctx.author.id}> đã húp được **+{profit:,} Star** bẩn!"
        else:
            await r.hincrby(user_key, "balance_dirty", -bet_amount)
            title = "💀 TÀI XỈU - CÚT!"
            color = COLORS["tenebris_error"]
            desc = f"Xúc xắc đổ: **{d1} - {d2} - {d3} = {total}** ({'TÀI' if result_is_tai else 'XỈU'})\nNgu thì chết! <@{ctx.author.id}> bị lột sạch **-{bet_amount:,} Star** bẩn!"

        embed = discord.Embed(title=title, description=desc, color=color)
        await ctx.send(embed=embed)

    # 🃏 2. GAME BLACKJACK (XÌ DÁCH)
    @commands.command(name="bj", aliases=["blackjack"])
    async def play_bj(self, ctx, amount: str):
        r = await get_redis_connection()
        user_key = f"equinox:user:{ctx.author.id}"
        dirty_bal = int(await r.hget(user_key, "balance_dirty") or 0)
        
        if amount.lower() == "all":
            bet_amount = dirty_bal
        else:
            try:
                bet_amount = int(amount)
            except ValueError:
                return await ctx.send("Cược tiền đàng hoàng xem nào!")

        if bet_amount <= 0 or bet_amount > dirty_bal:
            return await ctx.send(f"Mày chỉ có **{dirty_bal:,} Star** bẩn thôi! Két sắt ngầm sắp cạn rồi đấy!")

        # Tạo và xáo trộn bộ bài
        cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = cards * 4
        random.shuffle(deck)

        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        view = BlackjackView(ctx.author, bet_amount, player_hand, dealer_hand, deck, r)
        
        p_total = view.calculate_total(player_hand)
        
        embed = discord.Embed(title="🃏 SÒNG BẠC BLACKJACK CHỢ ĐEN", color=COLORS["tenebris_main"])
        embed.description = f"<@{ctx.author.id}> đang ném **{bet_amount:,} Star** bẩn vào sới bạc."
        embed.add_field(name=f"🃏 Bài của bạn ({p_total})", value=" ".join(str(x) for x in player_hand), inline=True)
        embed.add_field(name="🕴️ Nhà cái", value=f"{dealer_hand[0]} ❓", inline=True)
        
        # Nếu ra ngay xì dách từ 2 lá đầu
        if p_total == 21:
            await ctx.send(embed=embed)
            await view.end_game(ctx, "WIN", multiplier=2.5) # Thưởng Blackjack x2.5 cược
            return

        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(CasinoNgam(bot))
