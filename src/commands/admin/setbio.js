const { SlashCommandBuilder } = require('discord.js');
const LuminousEmbed = require('../../utils/EmbedBuilder');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('setbio')
        .setDescription('Thay đổi phần About Me (Tiểu sử) trên profile thật của bot')
        .addStringOption(option => 
            option.setName('content')
                .setDescription('Nội dung tiểu sử mới (tối đa 400 ký tự)')
                .setRequired(true)
        ),
    async execute(ctx, args) {
        // Bảo mật quyền truy cập lệnh 
        const ownerId = '914831312295165982';

        if (ctx.user.id !== ownerId) {
            return await ctx.reply({ embeds: [LuminousEmbed.error('Lệnh này chỉ dành cho chủ sở hữu dự án!')] });
        }

        let bioContent;

        if (ctx.isSlash) {
            bioContent = ctx.interaction.options.getString('content');
        } else {
            if (args.length < 1) {
                return await ctx.reply({ embeds: [LuminousEmbed.error('Vui lòng nhập nội dung tiểu sử! Cú pháp: `l!setbio <nội dung>`')] });
            }
            bioContent = args.join(' ');
        }

        if (bioContent.length > 400) {
            return await ctx.reply({ embeds: [LuminousEmbed.error('Tiểu sử quá dài! API Discord chỉ cho phép tối đa 400 ký tự.')] });
        }

        await ctx.deferReply();

        try {
            // Thay đổi trực tiếp mô tả Application của bot (About Me)
            await ctx.client.application.edit({ description: bioContent });
            
            const embed = LuminousEmbed.success(
                `Đã cập nhật About Me của bot thành công!\n\n` +
                `**Lưu ý:** *Discord API thường sẽ cache (lưu bộ nhớ đệm) thông tin này, nên có thể mất vài phút tiểu sử mới hiển thị đồng bộ ở mọi nơi.*`
            );
            await ctx.reply({ embeds: [embed] });
        } catch (error) {
            console.error(error);
            await ctx.reply({ embeds: [LuminousEmbed.error('Không thể cập nhật tiểu sử. Vui lòng kiểm tra console để xem chi tiết lỗi.')] });
        }
    }
};
