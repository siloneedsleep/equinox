const { SlashCommandBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder, ComponentType } = require('discord.js');

module.exports = {
    name: 'mine',
    description: 'Prism Mines - Dò mìn Lăng Kính (4x4)',
    slashData: new SlashCommandBuilder()
        .setName('mine')
        .setDescription('Prism Mines - Dò mìn Lăng Kính (4x4)')
        .addIntegerOption(opt => opt.setName('mines').setDescription('Số mìn (1-15)').setRequired(true))
        .addIntegerOption(opt => opt.setName('bet').setDescription('Số tiền cược').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let mines, bet;
        if (isSlash) {
            mines = context.options.getInteger('mines');
            bet = context.options.getInteger('bet');
        } else {
            mines = parseInt(args[0]);
            bet = parseInt(args[1]);
            if (isNaN(mines) || isNaN(bet)) return context.reply('⚠️ Cú pháp: `l!mine <số mìn 1-15> <số tiền>`');
        }

        if (mines < 1 || mines > 15) {
            const msg = '⚠️ Số mìn phải từ 1 đến 15!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }
        
        if (bet <= 0) {
            const msg = '⚠️ Tiền cược > 0!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }
        
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        if (db.users[author.id].balance < bet) {
            const msg = '❌ Bạn không đủ Lux!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        db.users[author.id].balance -= bet;
        context.client.writeDB(db);

        const totalCells = 16;
        let board = Array(totalCells).fill('💎');
        let mineIndices = new Set();
        while(mineIndices.size < mines) {
            mineIndices.add(Math.floor(Math.random() * totalCells));
        }
        mineIndices.forEach(idx => board[idx] = '💣');

        let revealed = Array(totalCells).fill(false);
        let safeClicks = 0;
        let currentMultiplier = 1;
        let isGameOver = false;

        const generateComponents = (disableAll = false) => {
            const rows = [];
            for (let i = 0; i < 4; i++) {
                const row = new ActionRowBuilder();
                for (let j = 0; j < 4; j++) {
                    const idx = i * 4 + j;
                    const btn = new ButtonBuilder()
                        .setCustomId(`mine_${idx}`)
                        .setStyle(revealed[idx] ? (board[idx] === '💣' ? ButtonStyle.Danger : ButtonStyle.Success) : ButtonStyle.Secondary)
                        .setLabel(revealed[idx] || disableAll ? board[idx] : '❓')
                        .setDisabled(revealed[idx] || disableAll);
                    row.addComponents(btn);
                }
                rows.push(row);
            }
            const controlRow = new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId('cashout').setLabel('💰 Rút Tiền').setStyle(ButtonStyle.Primary).setDisabled(disableAll || safeClicks === 0)
            );
            rows.push(controlRow);
            return rows;
        };

        const embed = new EmbedBuilder()
            .setColor('#00FFFF')
            .setTitle('⛏️ Prism Mines')
            .setDescription(`Cược: **${bet.toLocaleString()} Lux** | Mìn: **${mines}**\nHệ số hiện tại: **x${currentMultiplier.toFixed(2)}**`);

        const payload = { embeds: [embed], components: generateComponents() };
        const response = await (isSlash ? context.reply({ ...payload, fetchReply: true }) : context.reply(payload));

        const collector = response.createMessageComponentCollector({ componentType: ComponentType.Button, time: 60000 });

        collector.on('collect', async i => {
            if (i.user.id !== author.id) return i.reply({ content: '❌ Đây không phải ván của bạn!', ephemeral: true });

            if (i.customId === 'cashout') {
                isGameOver = true;
                const winAmount = Math.floor(bet * currentMultiplier);
                db.users[author.id].balance += winAmount;
                context.client.writeDB(db);
                
                embed.setColor('#00FF00').setDescription(`🎉 Bạn đã rút tiền an toàn!\nThắng: **${winAmount.toLocaleString()} Lux**\nSố dư: **${db.users[author.id].balance.toLocaleString()} Lux**`);
                await i.update({ embeds: [embed], components: generateComponents(true) });
                return collector.stop();
            }

            const idx = parseInt(i.customId.split('_')[1]);
            revealed[idx] = true;

            if (board[idx] === '💣') {
                isGameOver = true;
                db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.05);
                context.client.writeDB(db);
                
                embed.setColor('#FF0000').setDescription(`💥 **BÙM!** Bạn đạp trúng mìn Bóng Tối.\nMất: **${bet.toLocaleString()} Lux**\nSố dư: **${db.users[author.id].balance.toLocaleString()} Lux**`);
                await i.update({ embeds: [embed], components: generateComponents(true) });
                return collector.stop();
            } else {
                safeClicks++;
                const safeRemaining = (totalCells - mines) - (safeClicks - 1);
                currentMultiplier *= (totalCells - (safeClicks - 1)) / safeRemaining;
                
                embed.setDescription(`Cược: **${bet.toLocaleString()} Lux** | Mìn: **${mines}**\nHệ số hiện tại: **x${currentMultiplier.toFixed(2)}**\nTiền nhận nếu rút: **${Math.floor(bet * currentMultiplier).toLocaleString()} Lux**`);
                await i.update({ embeds: [embed], components: generateComponents() });
            }
        });

        collector.on('end', collected => {
            if (!isGameOver) {
                embed.setColor('#808080').setDescription(`⏳ Hết giờ! Ván chơi bị hủy và bạn mất tiền cược.`);
                response.edit({ embeds: [embed], components: generateComponents(true) }).catch(() => {});
            }
        });
    }
};
