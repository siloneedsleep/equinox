const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'daily',
    description: 'Nhận phần thưởng bảo hộ mỗi ngày',
    slashData: new SlashCommandBuilder()
        .setName('daily')
        .setDescription('Nhận phần thưởng bảo hộ mỗi ngày'),
    
    async execute(context, args, isSlash) {
        const authorId = isSlash ? context.user.id : context.author.id;
        const db = context.client.readDB();
        
        if (!db.users[authorId]) {
            db.users[authorId] = { balance: 0, xp: 0, level: 1, dailyStreak: 0, cooldowns: {} };
        }

        const now = Date.now();
        const cooldownAmount = 24 * 60 * 60 * 1000;
        const userCooldown = db.users[authorId].cooldowns.daily || 0;

        if (now < userCooldown) {
            const timeLeft = Math.round((userCooldown - now) / (60 * 60 * 1000));
            const msg = `⏳ Bạn đã nhận bảo hộ hôm nay! Vui lòng quay lại sau **${timeLeft} giờ**.`;
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        if (now > userCooldown + cooldownAmount * 2) {
            db.users[authorId].dailyStreak = 0; 
        }
        
        db.users[authorId].dailyStreak = (db.users[authorId].dailyStreak || 0) + 1;
        const streak = db.users[authorId].dailyStreak;
        
        let reward = 1000 + (streak * 200);
        let extraMsg = '';

        if (streak >= 7) {
            reward += 5000;
            extraMsg = '\n🎁 **Phần thưởng chuỗi 7 ngày:** Bạn nhận thêm 5,000 Lux ($LX$) và 1 Vé Vòng Quay!';
            db.users[authorId].dailyStreak = 0;
        }

        db.users[authorId].balance += reward;
        db.users[authorId].cooldowns.daily = now + cooldownAmount;
        
        context.client.writeDB(db);

        const msg = `☀️ **BẢO HỘ MỖI NGÀY**\nBạn nhận được **${reward.toLocaleString()} Lux ($LX$)**!\n🔥 Chuỗi điểm danh: **${streak} ngày**${extraMsg}`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
