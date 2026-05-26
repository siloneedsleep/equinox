class Context {
    constructor(ctx, client) {
        this.ctx = ctx;
        this.client = client;
        
        // Tự động nhận diện xem đây là lệnh Slash hay lệnh Chat thường
        this.isSlash = !!ctx.interaction;
        
        // Hợp nhất các thuộc tính cơ bản để sếp gọi đâu cũng trúng
        this.interaction = this.isSlash ? ctx.interaction : null;
        this.message = this.isSlash ? null : ctx;
        
        this.guild = ctx.guild;
        this.channel = ctx.channel;
        
        // Người dùng kích hoạt lệnh (Hợp nhất giữa .user và .author)
        this.user = this.isSlash ? ctx.interaction.user : ctx.author;
        this.member = ctx.member;
    }

    // Hàm hoãn phản hồi thông minh (Chống lỗi deferReply is not a function)
    async deferReply(options = {}) {
        if (this.isSlash) {
            return await this.interaction.deferReply(options);
        } else {
            // Lệnh chat thường không có khái niệm defer, mình cho hiển thị trạng thái đang gõ (typing) cho hoành tráng
            return await this.channel.sendTyping().catch(() => null);
        }
    }

    // Hàm gửi phản hồi thống nhất
    async reply(options) {
        // Chuẩn hóa chuỗi text thành Object nếu sếp truyền vào dạng chữ thuần
        const payload = typeof options === 'string' ? { content: options } : options;

        if (this.isSlash) {
            if (this.interaction.deferred || this.interaction.replied) {
                return await this.interaction.editReply(payload);
            }
            return await this.interaction.reply(payload);
        } else {
            return await this.message.reply(payload);
        }
    }

    // Hàm chỉnh sửa phản hồi đã gửi
    async editReply(options) {
        const payload = typeof options === 'string' ? { content: options } : options;

        if (this.isSlash) {
            return await this.interaction.editReply(payload);
        } else {
            // Đối với chat thường, mình sẽ tìm lại tin nhắn bot vừa phản hồi để sửa chữ
            if (this.message.repliedMessage) {
                return await this.message.repliedMessage.edit(payload);
            }
            // Nếu chưa lưu vết, gửi tin nhắn mới luôn
            return await this.channel.send(payload);
        }
    }
}

module.exports = Context;
