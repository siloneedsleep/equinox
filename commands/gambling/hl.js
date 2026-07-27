// Luminous High-Low - Giao diện Embed 2.0 [cite: 86, 87, 89, 212, 213]
const { SlashCommandBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder, ComponentType } = require('discord.js');

module.exports = {
    name: 'hl',
    description: 'Luminous High-Low - So sánh năng lượng ánh sáng',
    slashData: new SlashCommandBuilder()
        .setName('hl')
        .setDescription('Luminous High-Low - So sánh năng lượng ánh sáng')
        .addIntegerOption(opt => opt.setName('bet').setDescription('Số tiền cược').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let bet = isSlash ? context.options.getInteger('bet') : parseInt(args[0]);
        if (isNaN(bet) || bet <= 0) return isSlash ? context.reply({ content: '⚠️ Cú pháp: `l!hl <số tiền>`', flags: 64 }) : context.reply('⚠️ Cú pháp: `l!hl <số tiền>`');
        
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        if (db.users[author.id].balance < bet) return isSlash ? context.reply({ content: '❌ Bạn không đủ Lux!', flags: 64 }) : context.reply('❌ Bạn không đủ Lux!');

        db.users[author.id].balance -= bet;
        context.client.writeDB(db);

        let currentNumber = Math.floor(Math.random() * 100) + 1;
        let currentMultiplier = 1.0;
        let isGameOver = false;

        const generateComponents = (disableAll = false) => {
            return new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId('hl_high').setLabel('High (☀️)').setStyle(ButtonStyle.Success).setDisabled(disableAll),
                new ButtonBuilder().setCustomId('hl_low').setLabel('Low (🌙)').setStyle(ButtonStyle.Primary).setDisabled(disableAll),
                new ButtonBuilder().setCustomId('hl_cashout').setLabel('💰 Rút Tiền').setStyle(ButtonStyle.Secondary).setDisabled(disableAll || currentMultiplier === 1.0)
            );
        };

        const embed = new EmbedBuilder()
            .setColor('#FFA500')
            .setTitle('⚖️ Luminous High-Low')
            .setDescription(`Số hiện tại: **${currentNumber}** (1 - 100)\n\nCược: **${bet.toLocaleString()} Lux**\nHệ số: **x${currentMultiplier.toFixed(2)}**`);

        const payload = { embeds: [embed], components: [generateComponents()] };
        const response = await (isSlash ? context.reply({ ...payload, fetchReply: true }) : context.reply(payload));

        const collector = response.createMessageComponentCollector({ componentType: ComponentType.Button, time: 60000 });

        collector.on('collect', async i => {
            if (i.user.id !== author.id) return i.reply({ content: '❌ Đây không phải ván của bạn!', ephemeral: true });

            if (i.customId === 'hl_cashout') {
                isGameOver = true;
                const winAmount = Math.floor(bet * currentMultiplier);
                db.users[author.id].balance += winAmount;
                context.client.writeDB(db);
                
                embed.setColor('#00FF00').setDescription(`🎉 Đã rút tiền!\nThắng: **${winAmount.toLocaleString()} Lux**\nSố dư: **${db.users[author.id].balance.toLocaleString()} Lux**`);
                await i.update({ embeds: [embed], components: [generateComponents(true)] });
                return collector.stop();
            }

            const nextNumber = Math.floor(Math.random() * 100) + 1;
            const choice = i.customId === 'hl_high' ? 'high' : 'low';
            let isWin = false;

            if ((choice === 'high' && nextNumber >= currentNumber) || (choice === 'low' && nextNumber <= currentNumber)) {
                isWin = true;
            }

            if (isWin) {
                // Multiplier linh hoạt dựa trên rủi ro [cite: 90, 91, 92]
                let riskBase = choice === 'high' ? (100 - currentNumber) : currentNumber;
                riskBase = Math.max(1, riskBase);
                currentMultiplier *= (1 + (10 / riskBase)); 

                currentNumber = nextNumber;
                embed.setDescription(`Số hiện tại: **${currentNumber}** (1 - 100)\n\nCược: **${bet.toLocaleString()} Lux**\nHệ số: **x${currentMultiplier.toFixed(2)}**\nTiền rút: **${Math.floor(bet * currentMultiplier).toLocaleString()} Lux**`);
                await i.update({ embeds: [embed], components: [generateComponents()] });
            } else {
                isGameOver = true;
                db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.05);
                context.client.writeDB(db);
                
                embed.setColor('#FF0000').setDescription(`💥 **THUA!** Số tiếp theo là **${nextNumber}**.\nMất: **${bet.toLocaleString()} Lux**\nSố dư: **${db.users[author.id].balance.toLocaleString()} Lux**`);
                await i.update({ embeds: [embed], components: [generateComponents(true)] });
                return collector.stop();
            }
        });

        collector.on('end', () => {
            if (!isGameOver) {
                embed.setColor('#808080').setDescription(`⏳ Hết giờ! Ván chơi hủy, bạn mất cược.`);
                response.edit({ embeds: [embed], components: [generateComponents(true)] }).catch(() => {});
            }
        });
    }
};
