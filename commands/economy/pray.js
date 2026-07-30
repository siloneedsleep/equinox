const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'pray',
    description: 'Cầu nguyện Ánh Sáng (Nhận Lux và Buff May mắn)',
    slashData: new SlashCommandBuilder()
        .setName('pray')
        .setDescription('Cầu nguyện Ánh Sáng (Nhận Lux và Buff May mắn)'),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };

        const now = Date.now();
        const cooldownAmount = 60 * 60 * 1000;
        const userCooldown = db.users[author.id].cooldowns.pray || 0;

        if (now < userCooldown) {
            const timeLeft = Math.round((userCooldown - now) / (60 * 1000));
            const msg = `⏳ Hãy kiên nhẫn! Bạn có thể cầu nguyện lại sau **${timeLeft} phút**.`;
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        const earned = Math.floor(Math.random() * (150 - 50 + 1)) + 50;
        db.users[author.id].balance += earned;
        db.users[author.id].cooldowns.pray = now + cooldownAmount;
        
        db.users[author.id].luckBuffUntil = now + (15 * 60 * 1000); 

        context.client.writeDB(db);

        const msg = `🙏 **CẦU NGUYỆN ÁNH SÁNG**\nBạn nhận được **${earned} Lux ($LX$)**.\n✨ *May mắn cờ bạc của bạn được tăng thêm trong 15 phút tới!*`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
