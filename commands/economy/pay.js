const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'pay',
    description: 'Chuyển Lux ($LX$) cho người khác (Có giới hạn theo Level)',
    slashData: new SlashCommandBuilder()
        .setName('pay')
        .setDescription('Chuyển Lux ($LX$) cho người khác (Có giới hạn theo Level)')
        .addUserOption(opt => opt.setName('target').setDescription('Người nhận').setRequired(true))
        .addIntegerOption(opt => opt.setName('amount').setDescription('Số tiền chuyển').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let targetUser;
        let amount;

        if (isSlash) {
            targetUser = context.options.getUser('target');
            amount = context.options.getInteger('amount');
        } else {
            const targetInput = args[0];
            amount = parseInt(args[1]);
            if (!targetInput || isNaN(amount)) {
                return context.reply('⚠️ Cú pháp: `l!pay <@user> <số tiền>`');
            }
            const cleanId = targetInput.replace(/[<@!>]/g, '');
            try { targetUser = await context.client.users.fetch(cleanId); } catch {}
        }

        if (!targetUser || targetUser.bot || targetUser.id === author.id) {
            const msg = '❌ Không thể chuyển tiền cho người này!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        if (amount <= 0) {
            const msg = '⚠️ Số tiền phải lớn hơn 0!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        if (!db.users[targetUser.id]) db.users[targetUser.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };

        if (db.users[author.id].balance < amount) {
            const msg = '❌ Bạn không đủ Lux để thực hiện giao dịch này!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        const levelSender = db.users[author.id].level || 1;
        const levelReceiver = db.users[targetUser.id].level || 1;
        const baseLimit = 5000;
        const transferLimit = baseLimit * (levelSender * levelReceiver);

        if (amount > transferLimit) {
            const msg = `❌ Hạn mức giao dịch tối đa giữa Level ${levelSender} và Level ${levelReceiver} là **${transferLimit.toLocaleString()} Lux/ngày**!`;
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        const tax = Math.floor(amount * 0.05);
        const finalAmount = amount - tax;

        db.users[author.id].balance -= amount;
        db.users[targetUser.id].balance += finalAmount;
        db.jackpot = (db.jackpot || 0) + tax;

        context.client.writeDB(db);

        const msg = `💸 **GIAO DỊCH THÀNH CÔNG**\nBạn đã chuyển **${finalAmount.toLocaleString()} Lux ($LX$)** cho **${targetUser.username}** (Đã trừ 5% thuế bổ sung vào Hũ Jackpot Server).`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
