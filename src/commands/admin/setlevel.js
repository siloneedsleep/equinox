const { SlashCommandBuilder } = require('discord.js');
const LuminousEmbed = require('../../utils/EmbedBuilder');
const db = require('../../database/JsonManager');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('setlevel')
        .setDescription('Cài đặt cấp độ cho người dùng (Chỉ dành cho Owner)')
        .addUserOption(option => 
            option.setName('target')
                .setDescription('Người dùng cần cài đặt')
                .setRequired(true)
        )
        .addIntegerOption(option => 
            option.setName('level')
                .setDescription('Cấp độ mới')
                .setRequired(true)
        ),
    async execute(ctx, args) {
        if (ctx.user.id !== process.env.OWNER_ID) {
            return await ctx.reply({ embeds: [LuminousEmbed.error('Bạn không có quyền sử dụng lệnh này, lệnh này chỉ dành cho Owner!')] });
        }

        let targetUser;
        let newLevel;

        if (ctx.isSlash) {
            targetUser = ctx.interaction.options.getUser('target');
            newLevel = ctx.interaction.options.getInteger('level');
        } else {
            if (args.length < 2) {
                return await ctx.reply({ embeds: [LuminousEmbed.error('Bạn vui lòng tag người dùng và nhập cấp độ! Cú pháp: `l!setlevel @user 10`')] });
            }
            targetUser = ctx.message.mentions.users.first();
            newLevel = parseInt(args[1]);

            if (!targetUser) {
                return await ctx.reply({ embeds: [LuminousEmbed.error('Không tìm thấy người dùng bạn đã tag!')] });
            }
            if (isNaN(newLevel)) {
                return await ctx.reply({ embeds: [LuminousEmbed.error('Cấp độ phải là một con số hợp lệ!')] });
            }
        }

        await ctx.deferReply();

        const dbKey = `level_${targetUser.id}`;
        await db.set(dbKey, newLevel);

        const embed = LuminousEmbed.success(
            `Đã cập nhật cấp độ của **${targetUser.username}** thành **${newLevel}**!`
        );

        await ctx.reply({ embeds: [embed] });
    }
};
