const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
    name: 'quest',
    description: 'Hệ thống nhiệm vụ hằng ngày (Daily Quests)',
    slashData: new SlashCommandBuilder()
        .setName('quest')
        .setDescription('Hệ thống nhiệm vụ hằng ngày (Daily Quests)'),
        
    async execute(context, args, isSlash) {
        const authorId = isSlash ? context.user.id : context.author.id;
        const db = context.client.readDB();
        
        if (!db.users[authorId]) db.users[authorId] = { balance: 0, xp: 0, level: 1, cooldowns: {}, quest: {} };
        if (!db.users[authorId].quest) db.users[authorId].quest = { date: '', completed: false };

        const today = new Date().toDateString();
        
        if (db.users[authorId].quest.date !== today) {
            db.users[authorId].quest = {
                date: today,
                completed: false,
                progress: 0,
                target: 3 // Ví dụ: Cần hoàn thành 3 ván cờ bạc hoặc lệnh cày tiền bất kỳ
            };
            context.client.writeDB(db);
        }

        if (db.users[authorId].quest.completed) {
            const msg = '✅ Bạn đã hoàn thành toàn bộ nhiệm vụ Luminous hôm nay. Hãy quay lại vào ngày mai!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        db.users[authorId].quest.progress += 1;
        
        let embed = new EmbedBuilder().setColor('#FFD700').setTitle('📜 Nhiệm Vụ Hằng Ngày');

        if (db.users[authorId].quest.progress >= db.users[authorId].quest.target) {
            db.users[authorId].quest.completed = true;
            const reward = 5000;
            db.users[authorId].balance += reward;
            embed.setDescription(`🎉 **Hoàn thành nhiệm vụ!**\nBạn đã nhận được **${reward.toLocaleString()} Lux ($LX$)** và một Hộp Quà Lăng Kính (Ảo).`);
        } else {
            embed.setDescription(`Tiến độ nhiệm vụ hôm nay: **${db.users[authorId].quest.progress} / ${db.users[authorId].quest.target}**\n\n*Gợi ý: Hãy tiếp tục tương tác với các lệnh cày tiền hoặc mini-game để hoàn thành!*`);
        }

        context.client.writeDB(db);
        return isSlash ? context.reply({ embeds: [embed] }) : context.reply({ embeds: [embed] });
    }
};
