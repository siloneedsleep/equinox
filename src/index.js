require('dotenv').config();
const { Client, GatewayIntentBits, Collection } = require('discord.js');
const fs = require('fs');
const path = require('path');
const db = require('./database/db');
const { joinVoiceChannel } = require('@discordjs/voice');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildVoiceStates // QUAN TRỌNG: Để treo room 24/7
    ]
});

// Khởi tạo các Collection
client.commands = new Collection();
client.ownerId = process.env.OWNER_ID || '914831312295165982';

// --- Handler nạp lệnh ---
const foldersPath = path.join(__dirname, 'commands');
if (fs.existsSync(foldersPath)) {
    const commandFolders = fs.readdirSync(foldersPath);
    for (const folder of commandFolders) {
        const commandsPath = path.join(foldersPath, folder);
        const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));
        for (const file of commandFiles) {
            const filePath = path.join(commandsPath, file);
            const command = require(filePath);
            if ('data' in command && 'execute' in command) {
                client.commands.set(command.data.name, command);
            }
        }
    }
}

// --- Handler nạp Event ---
const eventsPath = path.join(__dirname, 'events');
if (fs.existsSync(eventsPath)) {
    const eventFiles = fs.readdirSync(eventsPath).filter(file => file.endsWith('.js'));
    for (const file of eventFiles) {
        const filePath = path.join(eventsPath, file);
        const event = require(filePath);
        if (event.once) {
            client.once(event.name, (...args) => event.execute(...args, client));
        } else {
            client.on(event.name, (...args) => event.execute(...args, client));
        }
    }
}

// --- Logic Tự Động Reconnect Voice 24/7 khi Bot Restart ---
client.once('ready', async () => {
    console.log(`✅ ${client.user.tag} đã sẵn sàng!`);
    
    // Quét tất cả server để xem room nào cần treo 24/7
    client.guilds.cache.forEach(async (guild) => {
        const stayChannelId = await db.get(`stay_vc_${guild.id}`);
        if (stayChannelId) {
            const channel = guild.channels.cache.get(stayChannelId);
            if (channel) {
                try {
                    joinVoiceChannel({
                        channelId: channel.id,
                        guildId: guild.id,
                        adapterCreator: guild.voiceAdapterCreator,
                        selfDeaf: true,
                        selfMute: true
                    });
                    console.log(`🎙️ Đã kết nối lại Voice 24/7 tại server: ${guild.name}`);
                } catch (e) {
                    console.error(`❌ Lỗi reconnect voice tại ${guild.name}:`, e);
                }
            }
        }
    });
});

client.login(process.env.TOKEN);
