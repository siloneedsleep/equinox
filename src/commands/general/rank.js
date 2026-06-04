const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const dataManager = require('../../utils/DataManager');

module.exports = {
    // 1. DỮ LIỆU ĐẨY LÊN DISCORD API
    data: new SlashCommandBuilder()
        .setName('rank')
        .setDescription('Kiểm tra cấp độ và lượng điểm kinh nghiệm (XP) hiện tại')
        .addUserOption(option =>
            option.setName('target')
                .setDescription('Người bạn muốn soi Rank (Bỏ trống nếu soi chính mình)')
                .setRequired(false)),

    // 2. LÕI XỬ LÝ LỆNH
    async execute(interaction) {
        // Cho hiện công khai để anh em còn khè nhau
        await interaction.deferReply({ ephemeral: false });

        const targetUser = interaction.options.getUser('target') || interaction.user;
        const guildId = interaction.guild.id;
        const userId = targetUser.id;

        // Rút hồ sơ từ storage.json
        const userData = await dataManager.get(`levels.${guildId}.${userId}`, { xp: 0, level: 1 });

        // TÍNH TOÁN TIẾN TRÌNH LÊN CẤP TIẾP THEO
        // Công thức: Cấp độ N cần (N * 10)^2 XP. Ví dụ Level 2 cần 400 XP.
        const nextLevel = userData.level + 1;
        const xpNeededForNextLevel = Math.pow(nextLevel * 10, 2);
        const currentLevelMinXp = Math.pow(userData.level * 10, 2);
        
        // Vẽ thanh phần trăm (Progress Bar) dài 15 ô
        const progress = userData.xp - currentLevelMinXp;
        const target = xpNeededForNextLevel - currentLevelMinXp;
        const percentage = Math.min(100, Math.max(0, (progress / target) * 100));
        
        const barLength = 15;
        const filledBars = Math.round((percentage / 100) * barLength);
        const emptyBars = barLength - filledBars;
        const progressBar = '█'.repeat(filledBars) + '░'.repeat(emptyBars); // Ký tự thanh quá mượt

        // Bọc vào Thẻ Cấp Độ (Embed)
        const rankEmbed = new EmbedBuilder()
            .setColor('#3498db') // Xanh nước biển
            .setAuthor({ name: `Thẻ Cấp Độ của ${targetUser.username}`, iconURL: targetUser.displayAvatarURL() })
            .setThumbnail(targetUser.displayAvatarURL({ size: 1024 }))
            .addFields(
                { name: '🏆 Cấp độ (Level)', value: `**${userData.level}**`, inline: true },
                { name: '✨ Kinh nghiệm (XP)', value: `**${userData.xp}** / ${xpNeededForNextLevel}`, inline: true },
                { name: `🚀 Tiến trình lên Level ${nextLevel}`, value: `\`${progressBar}\` (${percentage.toFixed(1)}%)`, inline: false }
            )
            .setFooter({ text: 'Luminous V15 - Rank System' })
            .setTimestamp();

        // Trả kết quả về
        await interaction.followUp({ embeds: [rankEmbed] });
    }
};
