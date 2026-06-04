require('dotenv').config();
const { REST, Routes } = require('discord.js');
const fs = require('fs');
const path = require('path');

const commands = [];
const commandsPath = path.join(__dirname, 'src', 'commands');

// Quét toàn bộ các thư mục con (admin, general, system...) để gom lệnh
if (fs.existsSync(commandsPath)) {
    const commandFolders = fs.readdirSync(commandsPath);
    
    for (const folder of commandFolders) {
        const commandsSubPath = path.join(commandsPath, folder);
        
        if (fs.statSync(commandsSubPath).isDirectory()) {
            const commandFiles = fs.readdirSync(commandsSubPath).filter(file => file.endsWith('.js'));
            
            for (const file of commandFiles) {
                const filePath = path.join(commandsSubPath, file);
                const command = require(filePath);
                
                // Trích xuất dữ liệu lệnh (data) để đẩy lên Discord
                if ('data' in command && 'execute' in command) {
                    commands.push(command.data.toJSON());
                } else {
                    console.log(`[Cảnh Báo] Lệnh tại ${filePath} bị thiếu thuộc tính bắt buộc.`);
                }
            }
        }
    }
} else {
    console.log(`[Lỗi] Không tìm thấy thư mục ${commandsPath}`);
}

// Khởi tạo bộ máy REST API với Token của bot
const rest = new REST({ version: '10' }).setToken(process.env.TOKEN);

// Kích hoạt tiến trình đẩy lệnh
(async () => {
    try {
        console.log(`🚀 [Hệ Thống] Đang bắt đầu làm mới và đẩy ${commands.length} lệnh Slash (/) lên Discord API...`);

        // Đẩy lệnh lên Global (Toàn cầu - Áp dụng cho mọi server bot tham gia)
        const data = await rest.put(
            Routes.applicationCommands(process.env.CLIENT_ID), 
            { body: commands },
        );

        console.log(`✅ [Thành Công] Đã triển khai hoàn tất ${data.length} lệnh Slash (/)!`);
        console.log(`⚠️ Lưu ý: Lệnh Global có thể mất vài phút để cập nhật trên tất cả các server.`);
    } catch (error) {
        console.error(`❌ [Lỗi Hệ Thống] Quá trình đẩy lệnh thất bại:`, error);
    }
})();
