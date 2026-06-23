# Reflection Lab 19

**Họ và Tên:** Trần Quốc Khánh  
**MSV:** 2A202600679  

**Báo cáo chạy Bonus:** Đã hoàn thành Challenge "The Semantic Memory". Mã nguồn `agent.py` và `demo.py` nằm trong thư mục `bonus/`. File `demo_output.txt` đính kèm trong thư mục `submission/screenshots/` chứng minh agent kết hợp thành công Episodic Memory (Qdrant) và Fallback Features (Feast) để tạo context cho LLM với 5 queries mẫu.

**1. Khi nào Hybrid Search thắng các mode khác?**
Hybrid Search phát huy sức mạnh tối đa trên các truy vấn dạng "mixed" (pha trộn). Đây là lúc người dùng gõ câu lệnh có chứa từ khóa chuyên ngành chính xác (verbatim keyword) nhưng lại kèm theo mô tả ý định bằng từ ngữ thông thường (paraphrase). Khi đó, Keyword (BM25) bắt dính các thuật ngữ kỹ thuật, trong khi Semantic (Vector) hiểu được ý định tổng thể. RRF kết hợp hai tín hiệu này giúp kết quả vừa chính xác vừa đa dạng, khắc phục điểm mù của từng phương pháp đơn lẻ.

**2. Khi nào KHÔNG nên dùng Hybrid Search?**
Không nên dùng Hybrid khi:
- Người dùng tra cứu mã số lỗi, ID đơn hàng, hoặc tên cấu hình chính xác (exact match): Lúc này Vector Search thường mang lại "nhiễu" do cố gắng tìm các văn bản có cấu trúc tương tự, thay vì tập trung vào keyword. Chỉ dùng BM25 hoặc Exact Match là tối ưu.
- Khi truy vấn cực ngắn, cụt lủn và không có bối cảnh (chỉ 1 từ): BM25 chạy nhanh và hiệu quả hơn.
- Khi hệ thống bị giới hạn tài nguyên và độ trễ (latency budget) rất ngặt nghèo (< 5ms): Hybrid đòi hỏi chạy 2 retriever và thực hiện tính RRF, tốn tài nguyên và thời gian hơn đáng kể.
