const { QuickDB } = require("quick.db");
// Sử dụng thư viện này nhưng không bắt nó build C++
const db = new QuickDB(); 

module.exports = db;
