const fs = require('fs').promises;
const path = require('path');

class DataManager {
    constructor() {
        // Trỏ đường dẫn về thư mục gốc chứa storage.json
        this.filePath = path.join(__dirname, '../../storage.json');
        this.writeQueue = Promise.resolve(); // Hàng đợi tránh xung đột ghi file
    }

    /**
     * Đọc dữ liệu từ storage.json một cách an toàn
     */
    async read() {
        try {
            // Kiểm tra file tồn tại chưa, chưa có thì tự tạo mới
            try {
                await fs.access(this.filePath);
            } catch {
                await fs.writeFile(this.filePath, JSON.stringify({}, null, 4), 'utf8');
                return {};
            }

            const data = await fs.readFile(this.filePath, 'utf8');
            if (!data.trim()) return {}; // Tránh lỗi parse nếu file trống
            
            return JSON.parse(data);
        } catch (error) {
            console.error(`[DataManager] Lỗi đọc file storage.json:`, error);
            return {};
        }
    }

    /**
     * Ghi dữ liệu vào storage.json qua cơ chế hàng đợi và tệp tạm
     */
    async write(data) {
        this.writeQueue = this.writeQueue.then(async () => {
            const tempPath = `${this.filePath}.tmp`;
            try {
                const jsonString = JSON.stringify(data, null, 4);
                
                // Ghi vào file tạm trước để tránh mất dữ liệu nếu bot sập giữa chừng
                await fs.writeFile(tempPath, jsonString, 'utf8');
                
                // Đổi tên file tạm thành file chính (Ghi đè cực kỳ an toàn)
                await fs.rename(tempPath, this.filePath);
            } catch (error) {
                console.error(`[DataManager] Lỗi ghi file storage.json:`, error);
                // Dọn rác nếu lỗi
                try { await fs.unlink(tempPath); } catch {}
            }
        });

        return this.writeQueue;
    }

    /**
     * Lấy dữ liệu theo đường dẫn (VD: get('partners.123.webhook_url'))
     */
    async get(keyPath, defaultValue = null) {
        const data = await this.read();
        const keys = keyPath.split('.');
        let current = data;

        for (const key of keys) {
            if (current === null || current === undefined || typeof current !== 'object') {
                return defaultValue;
            }
            current = current[key];
        }

        return current !== undefined ? current : defaultValue;
    }

    /**
     * Cập nhật/Thêm mới dữ liệu theo đường dẫn (VD: set('partners.123.webhook_url', 'link...'))
     */
    async set(keyPath, value) {
        const data = await this.read();
        const keys = keyPath.split('.');
        let current = data;

        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            if (!(key in current) || current[key] === null || typeof current[key] !== 'object') {
                current[key] = {};
            }
            current = current[key];
        }

        current[keys[keys.length - 1]] = value;
        await this.write(data);
        return true;
    }

    /**
     * Xóa một trường dữ liệu trong JSON
     */
    async delete(keyPath) {
        const data = await this.read();
        const keys = keyPath.split('.');
        let current = data;

        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            if (!(key in current)) return false;
            current = current[key];
        }

        const lastKey = keys[keys.length - 1];
        if (current && lastKey in current) {
            delete current[lastKey];
            await this.write(data);
            return true;
        }
        return false;
    }
}

// Xuất ra một instance duy nhất (Singleton) để dùng chung toàn mạng lưới
module.exports = new DataManager();
