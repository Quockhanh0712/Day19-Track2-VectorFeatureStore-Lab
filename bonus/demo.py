import os
import sys
from pathlib import Path

# Thêm đường dẫn project vào sys.path để chạy từ root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bonus.agent import HybridMemoryAgent

def main():
    print("Khởi tạo HybridMemoryAgent...")
    feast_repo_path = str(Path(__file__).resolve().parent.parent / "app" / "feast_repo")
    
    # Kiểm tra xem thư mục feast tồn tại không
    if not os.path.exists(feast_repo_path):
        print(f"Lỗi: Không tìm thấy feast repo ở {feast_repo_path}")
        sys.exit(1)
        
    agent = HybridMemoryAgent(feast_repo_path=feast_repo_path)
    
    print("Thêm Episodic Memories...")
    agent.remember("Gần đây tôi đang học về Kubernetes và tự động mở rộng hệ thống.")
    agent.remember("Tôi rất thích đọc sách khoa học viễn tưởng.")
    agent.remember("Cloud security là một chủ đề tôi đang nghiên cứu cho dự án công ty.")
    agent.remember("Hệ thống của tôi đang cần một phương pháp tự động scale hạ tầng theo lưu lượng người dùng.")
    
    print("\n--- 5 Demo Queries ---\n")
    
    queries = [
        ("Hỏi đơn giản (chỉ vector hit)", "Tôi đã đọc gì về Kubernetes?"),
        ("Hỏi cần profile context", "Recommend đọc gì tiếp"),
        ("Hỏi cần fresh activity", "Tôi đang quan tâm gì gần đây?"),
        ("Hỏi paraphrase (vector wins)", "Tài liệu về tự động mở rộng hạ tầng?"),
        ("Hỏi mixed (hybrid + profile)", "Cho tôi summary cloud security")
    ]
    
    for i, (q_type, q_text) in enumerate(queries, 1):
        print(f"Query {i} - {q_type}:\n\"{q_text}\"")
        context = agent.recall(query=q_text, user_id="u_001")
        print(f"Assembled Context:\n{context}")
        print("-" * 40)

if __name__ == "__main__":
    main()
