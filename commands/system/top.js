const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
    name: 'top',
    description: 'Bảng xếp hạng Đại gia / Cấp độ',
    slashData: new SlashCommandBuilder()
        .setName('top')
        .setDescription('Bảng xếp hạng Đại gia / Cấp độ'),

    async execute(context, args, isSlash) {
        const db = context.client.readDB();
        const users = Object.entries(db.users).map(([id, data]) => ({ id, ...data }));

        const topLux = [...users].sort((a, b) => (b.balance || 0) - (a.balance || 0)).slice(0, 10);

        let description = '';
        for (let i = 0; i < topLux.length; i++) {
            const user = topLux[i];
            let userObj;
            try {
                userObj = await context.client.users.fetch(user.id);
            } catch {
                userObj = { username: 'Unknown User' };
            }
            
            let medal = '🏅';
            if (i === 0) medal = '🥇';
            if (i === 1) medal = '🥈';
            if (i === 2) medal = '🥉';

            description += `${medal} **${userObj.username}** — ${Number(user.balance || 0).toLocaleString()} Lux\n`;
        }

        const embed = new EmbedBuilder()
            .setColor('#FFD700')
            .setTitle('🏆 BẢNG XẾP HẠNG ĐẠI GIA LUX')
            .setDescription(description || 'Chưa có dữ liệu.')
            .setFooter({ text: `Hũ Jackpot Server hiện tại: ${(db.jackpot || 0).toLocaleString()} Lux` });

        return isSlash ? context.reply({ embeds: [embed] }) : context.reply({ embeds: [embed] });
    }
};
