const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'beg',
    description: 'Xin Lộc Lăng Kính (Cày tiền lẻ)',
    slashData: new SlashCommandBuilder()
        .setName('beg')
        .setDescription('Xin Lộc Lăng Kính (Cày tiền lẻ)'),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };

        const now = Date.now();
        const cooldownAmount = 2 * 60 * 1000;
        const userCooldown = db.users[author.id].cooldowns.beg || 0;

        if (now < userCooldown) {
            const timeLeft = Math.round((userCooldown - now) / 1000);
            const msg = `⏳ Luminous đang bận! Hãy quay lại xin lộc sau **${timeLeft}s**.`;
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        db.users[author.id].cooldowns.beg = now + cooldownAmount;
        const isSuccess = Math.random() < 0.70;

        let msg = '';
        if (isSuccess) {
            const earned = Math.floor(Math.random() * (80 - 10 + 1)) + 10;
            db.users[author.id].balance += earned;
            msg = `🤲 Luminous mỉm cười và ban cho bạn **${earned} Lux ($LX$)**!`;
        } else {
            const fails = [
                "Luminous từ chối, nhưng khuyên bạn: *'Hãy cố gắng làm việc thay vì xin xỏ!'*",
                "Tinh thể không phản hồi. Bạn không nhận được Lux nào.",
                "Luminous bận rọi sáng nơi khác rồi. Chúc may mắn lần sau!"
            ];
            msg = `❌ ${fails[Math.floor(Math.random() * fails.length)]}`;
        }

        context.client.writeDB(db);
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
