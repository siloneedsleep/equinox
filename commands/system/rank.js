const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
    name: 'rank',
    description: 'Xem cấp độ và tiến trình XP hiện tại',
    slashData: new SlashCommandBuilder()
        .setName('rank')
        .setDescription('Xem cấp độ và tiến trình XP hiện tại')
        .addUserOption(opt => opt.setName('target').setDescription('Người dùng cần xem').setRequired(false)),

    async execute(context, args, isSlash) {
        const db = context.client.readDB();
        let targetUser;

        if (isSlash) {
            targetUser = context.options.getUser('target') || context.user;
        } else {
            const targetInput = args[0];
            if (targetInput) {
                const cleanId = targetInput.replace(/[<@!>]/g, '');
                try { targetUser = await context.client.users.fetch(cleanId); } catch {}
            }
            if (!targetUser) targetUser = context.author;
        }

        if (!db.users[targetUser.id]) {
            db.users[targetUser.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
            context.client.writeDB(db);
        }

        const userStats = db.users[targetUser.id];
        const currentLevel = userStats.level || 1;
        const currentXp = userStats.xp || 0;
        const xpRequired = 100 * Math.pow(currentLevel, 2);
        
        const progress = Math.min(100, Math.floor((currentXp / xpRequired) * 100));
        const progressBar = '█'.repeat(Math.floor(progress / 10)) + '░'.repeat(10 - Math.floor(progress / 10));

        const embed = new EmbedBuilder()
            .setColor('#00BFFF')
            .setTitle(`🌟 Hồ Sơ Ánh Sáng: ${targetUser.username}`)
            .addFields(
                { name: 'Cấp độ (Level)', value: `**${currentLevel}**`, inline: true },
                { name: 'Tổng Lux', value: `**${(userStats.balance || 0).toLocaleString()} $LX$**`, inline: true },
                { name: `Tiến trình XP (${progress}%)`, value: `\`${progressBar}\`\n(${currentXp} / ${xpRequired} XP)` }
            )
            .setThumbnail(targetUser.displayAvatarURL({ dynamic: true }));

        return isSlash ? context.reply({ embeds: [embed] }) : context.reply({ embeds: [embed] });
    }
};
