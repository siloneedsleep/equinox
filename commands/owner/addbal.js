const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const config = require('../../config.json');

module.exports = {
    name: 'addbal',
    description: 'Cộng thêm Lux cho người dùng (Chỉ Owner)',
    slashData: new SlashCommandBuilder()
        .setName('addbal')
        .setDescription('Cộng thêm Lux cho người dùng (Chỉ Owner)')
        .addStringOption(opt => opt.setName('target').setDescription('Ping hoặc User ID').setRequired(true))
        .addIntegerOption(opt => opt.setName('amount').setDescription('Số tiền Lux cần cộng').setRequired(true)),

    async execute(context, args, isSlash) {
        const authorId = isSlash ? context.user.id : context.author.id;

        if (!config.ownerIds.includes(authorId)) {
            const errMsg = '❌ Lệnh này chỉ dành cho Bot Owner!';
            return isSlash ? context.reply({ content: errMsg, flags: 64 }) : context.reply(errMsg);
        }

        let targetInput = isSlash ? context.options.getString('target') : args[0];
        let amount = isSlash ? context.options.getInteger('amount') : parseInt(args[1]);

        if (!targetInput || isNaN(amount) || amount <= 0) {
            const usageMsg = '⚠️ Cú pháp: `l!addbal <@user|id> <amount>` (Số tiền > 0)';
            return isSlash ? context.reply({ content: usageMsg, flags: 64 }) : context.reply(usageMsg);
        }

        const cleanId = targetInput.replace(/[<@!>]/g, '');
        let targetUser;
        try {
            targetUser = await context.client.users.fetch(cleanId);
        } catch {
            return isSlash ? context.reply({ content: '❌ Không tìm thấy người dùng này!', flags: 64 }) : context.reply('❌ Không tìm thấy người dùng này!');
        }

        const db = context.client.readDB();
        if (!db.users[targetUser.id]) db.users[targetUser.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };

        db.users[targetUser.id].balance += amount;
        context.client.writeDB(db);

        const embed = new EmbedBuilder()
            .setColor('#00FF00')
            .setTitle('👑 Bot Owner - Cộng Số Dư')
            .setDescription(`Đã cộng thêm **${amount.toLocaleString()} Lux ($LX$)** cho **${targetUser.username}**.\n💰 Số dư mới: **${db.users[targetUser.id].balance.toLocaleString()} Lux**`);

        return isSlash ? context.reply({ embeds: [embed] }) : context.reply({ embeds: [embed] });
    }
};
