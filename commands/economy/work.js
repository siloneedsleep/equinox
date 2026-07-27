const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'work',
    description: 'Thu hoạch Năng Lượng Ánh Sáng (Luminous Harvest)',
    slashData: new SlashCommandBuilder()
        .setName('work')
        .setDescription('Thu hoạch Năng Lượng Ánh Sáng (Luminous Harvest)'),
        
    async execute(context, args, isSlash) {
        const authorId = isSlash ? context.user.id : context.author.id;
        const db = context.client.readDB();
        
        if (!db.users[authorId]) {
            db.users[authorId] = { balance: 0, xp: 0, level: 1, dailyStreak: 0, cooldowns: {} };
        }

        const now = Date.now();
        const cooldownAmount = 5 * 60 * 1000;
        const userCooldown = db.users[authorId].cooldowns.work || 0;

        if (now < userCooldown) {
            const timeLeft = Math.round((userCooldown - now) / 1000);
            const msg = `⏳ Thể lực chưa hồi phục! Đợi **${timeLeft}s** nữa để tiếp tục làm việc.`;
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        const luckFactor = Math.random();
        let earned = 0;
        let responseMsg = '';

        if (luckFactor < 0.05) {
            db.users[authorId].cooldowns.work = now + (cooldownAmount * 2);
            responseMsg = '🔥 Bị **"Ánh Sáng Thiêu Rụi"** (Overload)! Không nhận được Lux và thời gian chờ tăng gấp đôi.';
        } else if (luckFactor < 0.15) {
            earned = Math.floor(Math.random() * (1500 - 1000 + 1)) + 1000;
            db.users[authorId].balance += earned;
            db.users[authorId].cooldowns.work = now + cooldownAmount;
            responseMsg = `🌟 **ĐẠI THÀNH CÔNG!** Lăng kính rực rỡ, bạn thu thập được **${earned} Lux ($LX$)**!`;
        } else {
            earned = Math.floor(Math.random() * (500 - 100 + 1)) + 100;
            db.users[authorId].balance += earned;
            db.users[authorId].cooldowns.work = now + cooldownAmount;
            
            const jobs = [
                'Lau chùi Lăng Kính Ánh Sáng', 
                'Thu thập Tia Nắng Bình Minh', 
                'Sạc Năng Lượng Cho Tinh Thể', 
                'Chăm sóc Linh Hồn Ánh Sáng'
            ];
            const job = jobs[Math.floor(Math.random() * jobs.length)];
            responseMsg = `🧹 Hoàn thành **${job}**, nhận được **${earned} Lux ($LX$)**.`;
        }

        context.client.writeDB(db);
        return isSlash ? context.reply(responseMsg) : context.reply(responseMsg);
    }
};
