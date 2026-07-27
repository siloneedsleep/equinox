const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'cf',
    description: 'Prism Flip - Tung đồng xu Ánh Sáng',
    slashData: new SlashCommandBuilder()
        .setName('cf')
        .setDescription('Prism Flip - Tung đồng xu Ánh Sáng')
        .addStringOption(opt => opt.setName('choice')
            .setDescription('Chọn mặt đồng xu')
            .setRequired(true)
            .addChoices(
                { name: 'Sun (Nhật Sơn)', value: 'sun' },
                { name: 'Moon (Nguyệt Quang)', value: 'moon' }
            ))
        .addIntegerOption(opt => opt.setName('bet').setDescription('Số tiền cược').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let choice, bet;

        if (isSlash) {
            choice = context.options.getString('choice');
            bet = context.options.getInteger('bet');
        } else {
            choice = args[0]?.toLowerCase();
            bet = parseInt(args[1]);
            
            if (!['sun', 'moon', 's', 'm'].includes(choice) || isNaN(bet)) {
                return context.reply('⚠️ Cú pháp: `l!cf <sun/moon> <số tiền>`');
            }
            if (choice === 's') choice = 'sun';
            if (choice === 'm') choice = 'moon';
        }

        if (bet <= 0) return isSlash ? context.reply({ content: '⚠️ Tiền cược phải lớn hơn 0!', flags: 64 }) : context.reply('⚠️ Tiền cược phải lớn hơn 0!');
        
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        
        if (db.users[author.id].balance < bet) {
            return isSlash ? context.reply({ content: '❌ Bạn không đủ Lux để cược!', flags: 64 }) : context.reply('❌ Bạn không đủ Lux để cược!');
        }

        const rand = Math.random();
        let resultFace = Math.random() < 0.5 ? 'sun' : 'moon';
        let winAmount = 0;
        let resultMsg = '';

        if (rand < 0.01) {
            winAmount = bet * 5;
            db.users[author.id].balance += (winAmount - bet);
            resultMsg = `🌟 **NHẬT THỰC HÀO QUANG (ECLIPSE)!** 🌟\nĐồng xu lơ lửng ở giữa không trung... Bạn được hoàn tiền và nhận thưởng **x5**!`;
        } else if (choice === resultFace) {
            winAmount = bet;
            db.users[author.id].balance += winAmount;
            const faceEmoji = resultFace === 'sun' ? '☀️ Nhật Sơn' : '🌙 Nguyệt Quang';
            resultMsg = `Mặt **${faceEmoji}**!\n✅ Bạn thắng **${winAmount.toLocaleString()} Lux ($LX$)**.`;
        } else {
            db.users[author.id].balance -= bet;
            db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.02);
            const faceEmoji = resultFace === 'sun' ? '☀️ Nhật Sơn' : '🌙 Nguyệt Quang';
            resultMsg = `Mặt **${faceEmoji}**!\n❌ Bạn đã mất **${bet.toLocaleString()} Lux ($LX$)**.`;
        }

        context.client.writeDB(db);

        const msg = `🪙 **PRISM FLIP** 🪙\n${resultMsg}\n💰 Số dư: **${db.users[author.id].balance.toLocaleString()} Lux**`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
