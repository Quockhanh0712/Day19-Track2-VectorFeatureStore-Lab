# Kiến trúc Trợ lý AI: "The Semantic Memory"

*(Được đóng góp bởi: Antigravity AI Assistant)*

## Sơ đồ Kiến trúc

```mermaid
graph TD
    User([Người dùng VN])
    App[AI Assistant Interface]
    Stream[Real-time Stream / Kafka]
    Qdrant[(Qdrant Vector Store\nEpisodic Memory)]
    Feast[(Feast Feature Store\nStable Profile & Activity)]
    LLM[Large Language Model\n(e.g., GPT-4o / Claude 3.5)]

    User -- "Gửi tin nhắn / Đọc tài liệu" --> App
    App -- "Lưu nội dung (text, timestamp)" --> Embedder[Embedding Model: bge-m3]
    Embedder -- "Lưu chunk vector" --> Qdrant
    
    App -- "Hành vi (click, time spent)" --> Stream
    Stream -- "Cập nhật activity" --> Feast
    
    User -- "Query (e.g., 'Tóm tắt bài về Cloud')" --> App
    App -- "1. Lấy thông tin user (get_online_features)" --> Feast
    App -- "2. Tìm kiếm semantic (hybrid_search filtered by user_id)" --> Qdrant
    
    Feast -. "Trả về User Profile & Latent Prefs" .-> App
    Qdrant -. "Trả về Top-K Memories" .-> App
    
    App -- "3. Assemble Context & Query" --> LLM
    LLM -- "4. Trả lời được cá nhân hóa" --> App
    App -- "Phản hồi" --> User
```

## Các Quyết Định Thiết Kế Kiến Trúc (Trade-offs)

### Quyết định 1: Chiến lược Chunking - "Conversation-Turn Chunking"
- **X vs Y:** Tôi đã chọn cách gộp tin nhắn theo lượt hội thoại (Conversation-turn chunking) thay vì ngắt mỗi tin nhắn thành một chunk (Per-message chunking) hoặc ngắt theo số token cố định (Fixed-window chunking).
- **Lý do chọn X:** Trong môi trường chat, người dùng thường nhắn nhiều tin nhắn ngắn liên tiếp để diễn đạt một ý (ví dụ: "Cho mình hỏi" -> "Về bài toán cloud" -> "Nó scale như thế nào?"). Nếu dùng Per-message chunking, các vector sẽ bị mất ngữ cảnh và rác, khiến Qdrant không thể tìm ra đúng đoạn thông tin khi user recall. Gộp theo conversation-turn (có semantic break) giữ được ngữ cảnh toàn vẹn của câu hỏi và câu trả lời.
- **Trade-off:** Dù việc này làm tăng độ trễ lúc lưu trữ (phải đợi hết một lượt hội thoại mới chunk và embed), nhưng chất lượng retrieval được cải thiện vượt bậc, đặc biệt cho các câu hỏi paraphrase về sau.

### Quyết định 2: Feature Schema - "Tabular + Latent Embedding"
- **X vs Y:** Tôi chọn thiết kế schema kết hợp cả các feature tĩnh (Tabular) và đặc trưng ngầm định (Latent Embedding) thay vì chỉ dùng Tabular thuần tuý.
- **Lý do chọn X:** User profile có những thứ định lượng được (`reading_speed_wpm`, `topic_affinity`) nhưng cũng có những sở thích rất khó gọi tên rõ ràng. Việc lưu một vector trung bình (average embedding) của các tài liệu user hay đọc vào Feature Store làm `preference_embedding` cho phép hệ thống thực hiện re-ranking kết quả từ Vector Store bằng cosine similarity, tạo ra độ cá nhân hóa sâu sắc mà các rule-based tabular features không làm được.
- **Trade-off:** Điều này đòi hỏi offline pipeline phải liên tục tính toán lại vector trung bình cho user (tốn compute cost), nhưng đổi lại chất lượng recommendation và recall được cá nhân hóa hoàn toàn.

### Quyết định 3: Freshness Strategy - "Micro-Batching (5-minute)"
- **X vs Y:** Tôi chọn chiến lược cập nhật Micro-Batching (5 phút 1 lần) cho cả Episodic Memory và Feature Store, thay vì Real-time Streaming (Push API) hoặc Daily Batch.
- **Lý do chọn X:** Trợ lý AI cá nhân không phải là hệ thống High-Frequency Trading. Khi người dùng vừa đọc một tài liệu, họ hiếm khi ngay lập tức hỏi "Tôi vừa đọc gì cách đây 1 giây?". Độ trễ 5 phút là hoàn toàn có thể chấp nhận được về mặt trải nghiệm người dùng (UX), nhưng lại giảm thiểu độ phức tạp của hạ tầng đi hàng chục lần so với việc thiết lập hệ thống event-driven streaming (như Kafka) cho từng sự kiện click.
- **Trade-off:** Chấp nhận một chút "độ trễ trí nhớ" (amnesia) trong khoảng thời gian ngắn 5 phút để đổi lấy chi phí hạ tầng thấp và dễ bảo trì.

## Cân nhắc bối cảnh Tiếng Việt (Vietnamese Context Awareness)

Một hệ thống AI cho người Việt phải giải quyết triệt để vấn đề **Code-switching (pha trộn Anh-Việt)** và **Lỗi gõ phím không dấu/sai chính tả**.
- **Embedding Model:** Việc dùng `BAAI/bge-small-en-v1.5` như bài lab cơ bản là chưa đủ tốt cho tiếng Việt. Hệ thống thực tế cần dùng `bge-m3` để bắt được ngữ nghĩa đa ngôn ngữ (Multilingual).
- **BM25 Tokenization:** Thay vì `text.lower().split()`, hệ thống phải dùng các thư viện Word Segmentation chuyên dụng cho tiếng Việt (như `pyvi` hoặc `underthesea`) để BM25 không bị tách sai các từ ghép (ví dụ "máy tính" không bị tách thành "máy" và "tính").
- Trong Feature Store, chúng ta thêm một feature `code_switching_ratio` để biết người dùng này thích AI trả lời thuần Việt hay chêm tiếng Anh (như "deploy lên cloud"), từ đó nhét vào system prompt của LLM cho phù hợp.

## Phương án thay thế đã bị loại bỏ (Rejected Alternative)

- **Phương án bị loại:** Tôi đã xem xét việc lưu toàn bộ Episodic Memory (lịch sử chat) vào thẳng Feature Store (dưới dạng một Array feature cực lớn).
- **Lý do loại bỏ:** Feature Store (như Feast trên Redis/SQLite) được thiết kế cho việc look-up theo Key-Value tốc độ cao (`O(1)`), không hỗ trợ tìm kiếm Nearest Neighbor (`O(log N)`) dựa trên vector distance. Nếu lưu lịch sử chat vào Feature Store, ta sẽ phải kéo toàn bộ lịch sử đó về Application Layer rồi mới search, dẫn đến thảm họa về Network I/O và RAM khi lịch sử phình to lên hàng trăm MB. Do đó, Vector Store (Qdrant) và Feature Store (Feast) phải được tách bạch rõ ràng theo đúng chức năng của chúng.
