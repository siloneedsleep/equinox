const { QuickDB } = require("quick.db");
const db = new QuickDB(); // Tự động tạo file json.sqlite ở thư mục gốc

module.exports = db;
