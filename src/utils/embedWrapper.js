const { EmbedBuilder } = require('discord.js');

/**
 * Hàm bọc Embed dùng chung cho toàn bộ Luminous Bot
 * @param {Object} ctx - Message hoặc Interaction
 * @param {string} content - Nội dung thông báo
 * @param {string} type - 'success', 'error', hoặc 'info'
 * @param {boolean} ephemeral - Chỉ user thấy (mặc định: true cho Interaction)
 */
async function sendEmbed(ctx, content, type = 'info', ephemeral = true) {
    try {
        const colors = {
            info: 0x2b2d31,    // Màu xám đen sang trọng
            success: 0x00ff00, // Xanh lá
            error: 0xff0000    // Đỏ
        };

        const embed = new EmbedBuilder()
            .setDescription(content)
            .setColor(colors[type] || colors.info)
            .setTimestamp();

        // Hỗ trợ Hybrid: Kiểm tra xem là Interaction hay Message
        const options = { embeds: [embed] };
        
        // Thêm ephemeral cho slash command
        if (ctx.isCommand?.() || ctx.isContextMenu?.()) {
            options.ephemeral = ephemeral;
        }

        if (ctx.replied || ctx.deferred) {
            return await ctx.editReply(options);
        }
        
        if (typeof ctx.reply === 'function') {
            return await ctx.reply(options).catch(err => {
                console.error('Error replying:', err);
                return null;
            });
        } else if (ctx.channel?.send) {
            return await ctx.channel.send(options).catch(err => {
                console.error('Error sending message:', err);
                return null;
            });
        }
    } catch (error) {
        console.error('❌ Error trong sendEmbed:', error);
        return null;
    }
}

module.exports = { sendEmbed };
