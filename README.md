# 🪐 Equinox Network V2 - The Revolutionary Ecosystem

**Equinox Network V2** là bản tái cấu trúc toàn diện từ nền tảng V1, chuyển dịch sang kiến trúc **Event-Driven (Hướng sự kiện)** và **Decoupling (Tách biệt Logic/UI)**. Hệ thống vận hành song song hai thực thể bot đối lập trên cùng một mã nguồn, tạo nên một thế giới ngầm đầy kịch tính và một hoàng gia sang trọng.

**Chủ sở hữu hệ sinh thái:** **Silo**

---

## 🏛️ Kiến Trúc Hệ Thống (Modular Design)

Dự án được xây dựng theo cấu trúc Modular hóa cực cao, giúp dễ dàng mở rộng và bảo trì:

- **`config/`**: Quản lý bí mật hệ thống và cấu hình ca trực.
- **`core/`**: Trái tim của hệ thống, xử lý nạp Identity Bot và kết nối KeyDB Pub/Sub.
- **`backend/`**:
    - `database.py`: Tầng truy cập dữ liệu (Data Access Layer) trên KeyDB.
    - `economy_engine.py`: Động cơ xử lý logic tiền tệ, rửa tiền, ám sát.
    - `web_server.py`: Server xử lý OAuth2 và tín hiệu Deploy.
    - `presence_proxy.py`: WebSocket Gateway giữ trạng thái Profile 24/7.
- **`ai_labs/`**: Bộ não AI Gemini với cơ chế xoay tua API Key và Circuit Breaker.
- **`cogs_shared/`**: Tầng hiển thị (UI/UX) với các lệnh tương tác người dùng.

---

## 🌟 Tính Năng Nổi Bật

### 1. Cơ Chế Giao Ca Song Hành (Dual Persona)
Hệ thống tự động hoán đổi trạng thái giữa hai bot theo thời gian thực (GMT+7):
- **Luminous (06:00 - 17:59)**: Văn minh, hoàng gia, quản lý **Aequor** (Tiền sạch).
- **Tenebris (18:00 - 05:59)**: Giang hồ, chợ đen, thao túng **Aequis** (Tiền bẩn).

### 2. Jules Core - Self-Modifying AI (/jules)
Đặc quyền dành cho **Silo** và Developer:
- **Autonomous Architecture**: Jules có khả năng tự phân tích, đọc/viết mã nguồn và thực thi các lệnh hệ thống để tự sửa lỗi hoặc nâng cấp tính năng ngay trong lúc bot đang chạy.
- **Smart Execution**: Hiển thị quá trình tư duy và log thực thi chi tiết.

### 3. Rich Presence Tối Thượng (/status add)
Đặc quyền dành cho Admin+ và Voice Premium Key:
- **Double-Modal UI**: Tùy chỉnh tên app, nội dung, ảnh và nút bấm trên Profile thật.
- **Proxy Presence (/livestatus)**: Duy trì Profile luôn sáng đèn 24/7 kể cả khi tắt máy thông qua WebSocket Proxy.

### 3. AI Labs - Thao Túng & Chữa Lành
- **Luminous AI**: Tư vấn lịch sự, hoàng gia, giúp giải quyết mâu thuẫn.
- **Tenebris AI**: Cục súc, mỉa mai, có 20% tỉ lệ đưa tin giả để kích động drama.
- **Circuit Breaker**: Tự động xoay tua API Key Gemini khi bị giới hạn (429).

### 4. Kinh Tế & Drama (Economy V2)
- **Mở Túi Mù (Star Pouch)**: Nhận tiền ngẫu nhiên lên đến 100M, loại tiền phụ thuộc vào bot đang trực.
- **Trạm Rửa Tiền**: Chuyển đổi Aequis sang Aequor với mức phí 15-25% nộp vào Quỹ Gia Đình.
- **Hệ Thống Sát Thủ**: Ám sát cướp 30% tài sản sạch.
- **Di Chúc Ngầm**: Bảo vệ tài sản cho người phối ngẫu khi bị sát hại.
- **Truy Nã (Bounty)**: Tự động treo thưởng lên đầu kẻ thủ ác.

### 5. Phân Cấp Quyền Lực (Levels 0 - 4)
- **Level 4 (Owner - Silo)**: Quyền lực tối thượng, kiểm soát toàn bộ hệ thống.
- **Level 3 (Dev)**: Debug và điều phối lỗi.
- **Level 2 (Admin)**: Miễn phí dùng lệnh Status, thực thi công lý tại Tòa án.
- **Luật Bảo Vệ Cấp Trên**: Cấp dưới tuyệt đối không thể phạt gậy (Warn) cấp trên.

---

## 🛠️ Hướng Dẫn Cài Đặt (Pterodactyl / VPS)

### 1. Yêu cầu hệ thống
- Python 3.10+
- **Redis thuần** (Bạn có thể dùng Redis từ tab *Databases* trên Panel hoặc dịch vụ Redis Cloud miễn phí).

### 2. Cấu hình trên Pterodactyl Panel
Bạn có hai cách để nạp cấu hình:

**Cách 1: Sử dụng File (Khuyên dùng)**
- Tải toàn bộ mã nguồn lên File Manager.
- Đổi tên file `config.json.example` thành `config.json`.
- Điền các Token, API Key và URI Redis vào file này.
- **Lưu ý:** Đảm bảo định dạng JSON chuẩn. Nếu có ký tự đặc biệt, hãy kiểm tra kỹ dấu ngoặc và dấu phẩy.

**Cách 2: Sử dụng Biến môi trường (Variables)**
Thêm các biến sau vào mục **Startup** của Panel:
- `LUMINOUS_TOKEN`, `TENEBRIS_TOKEN`
- `REDIS_URI`: Ví dụ `redis://:password@host:port`
- `OWNER_ID`
- `SERVER_PORT`: Bot sẽ tự động bắt port này.

### 3. Startup Command
Thiết lập lệnh khởi chạy trên Panel:
```bash
python main.py
```

### 4. Quy trình tắt Bot
Hệ thống đã tích hợp **Graceful Shutdown**. Khi bạn nhấn nút **Stop** hoặc **Kill** trên Panel, Bot sẽ nhận tín hiệu và đóng toàn bộ kết nối Redis/Discord một cách an toàn trước khi thoát.

---

## 📜 Giấy Phép & Bản Quyền
Bản quyền hệ sinh thái thuộc về **Equinox Network**.
Được phát triển và duy trì bởi **Silo** (Owner) & **Jules** (Core Developer).

---
*Equinox Network V2 - Nơi ánh sáng và bóng tối giao thoa.*
