const { EmbedBuilder } = require('discord.js');

class LuminousEmbed extends EmbedBuilder {
    constructor() {
        super();
        this.setColor('#2b2d31'); 
        this.setTimestamp();
        this.setFooter({ text: 'Luminous Engine v15' });
    }

    static success(description) {
        return new LuminousEmbed()
            .setColor('#57F287')
            .setDescription(`✅ | ${description}`);
    }

    static error(description) {
        return new LuminousEmbed()
            .setColor('#ED4245')
            .setDescription(`❌ | ${description}`);
    }

    static info(title, description) {
        return new LuminousEmbed()
            .setColor('#5865F2')
            .setTitle(title)
            .setDescription(description);
    }
}

module.exports = LuminousEmbed;
