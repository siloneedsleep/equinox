const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'bal',
    description: 'Kiểm tra số dư Lux ($LX$)',
    slashData: new SlashCommandBuilder()
        .setName('bal')
        .setDescription('Kiểm tra số dư Lux ($LX$)')
        .addUserOption(opt => opt.setName('target').setDescription('Người muốn kiểm tra').setRequired(false)),
        
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

        const balance = db.users[targetUser.id].balance;
        const msg = `💰 Số dư của **${targetUser.username}**: **${balance.toLocaleString()} Lux ($LX$)**`;
        
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
