const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'claim',
    description: 'Nhận phần thưởng thụ động dựa trên Level',
    slashData: new SlashCommandBuilder()
        .setName('claim')
        .setDescription('Nhận phần thưởng thụ động dựa trên Level'),
        
    async execute(context, args, isSlash) {
        const authorId = isSlash ? context.user.id : context.author.id;
        const db = context.client.readDB();
        
        if (!db.users[authorId]) db.users[authorId] = { balance: 0, xp: 0, level: 1, cooldowns: {} };

        const now = Date.now();
        const cooldownAmount = 12 * 60 * 60 * 1000; // 12 tiếng 1 lần
        const userCooldown = db.users[authorId].cooldowns.claim || 0;

        if (now < userCooldown) {
            const timeLeft = Math.round((userCooldown - now) / (60 * 60 * 1000));
            const msg = `⏳ Bạn đã nhận quà Server rồi! Vui lòng quay lại sau **${timeLeft} giờ**.`;
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        const userLevel = db.users[authorId].level || 1;
        const reward = userLevel * 1000; 
        
        db.users[authorId].balance += reward;
        db.users[authorId].cooldowns.claim = now + cooldownAmount;
        
        context.client.writeDB(db);

        const msg = `🎁 **QUÀ TẶNG SERVER (CLAIM)**\nDựa trên đẳng cấp Ánh Sáng (Level ${userLevel}) của bạn, Luminous ban tặng **${reward.toLocaleString()} Lux ($LX$)**!`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
