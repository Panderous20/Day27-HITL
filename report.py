"""
BÁO CÁO TRẢ LỜI CÂU HỎI KIẾN TRÚC HUMAN-IN-THE-LOOP (HITL)
Dự án: Day27-HITL
"""

# ==============================================================================
# CÂU 1: LỰA CHỌN INTERRUPT_BEFORE HAY INTERRUPT_AFTER?
# ==============================================================================
"""
[Câu hỏi]:
Nếu mục tiêu là để con người rewrite một customer retention email vừa được generate
trước khi nó di chuyển đến một routing node, bạn sẽ dùng interrupt_before hay interrupt_after? Tại sao?

[Trả lời]:
Nên dùng: interrupt_after=["generate_email"] (hoặc interrupt_before=["routing_node"])

[Giải thích chi tiết]:
1. Cơ chế hoạt động:
   - Node `generate_email` chịu trách nhiệm tạo ra bản thảo (draft) email và lưu vào `GraphState`.
   - Nếu dùng `interrupt_before=["generate_email"]`, graph sẽ dừng TRƯỚC KHI email được sinh ra.
     Lúc này trong State chưa có nội dung email, con người không có gì để đọc và chỉnh sửa (rewrite).
   - Nếu dùng `interrupt_after=["generate_email"]`, graph sẽ hoàn thành việc sinh email,
     cập nhật state chứa nội dung draft, sau đó mới TẠM DỪNG (interrupt).
2. Quy trình can thiệp (HITL Workflow):
   - Bước 1: `generate_email` chạy -> sinh `draft_email` vào State.
   - Bước 2: Graph tạm dừng do `interrupt_after`.
   - Bước 3: Human Operator đọc `draft_email` trên UI, chỉnh sửa nội dung nếu cần.
   - Bước 4: Gọi `graph.update_state(config, {"email_content": new_text})` để ghi đè.
   - Bước 5: Gọi `graph.invoke(None, config)` để resume, graph chuyển tiếp sang `routing_node`
     với nội dung email đã được chuẩn hóa bởi con người.
"""


# ==============================================================================
# CÂU 2: GIẢI PHÁP NGĂN CHẶN ALERT FATIGUE (HỘI CHỨNG MỆT MỎI VÌ CẢNH BÁO)
# ==============================================================================
"""
[Tình huống]:
500 actions `send_email` mỗi ngày bị kẹt ở confidence 0.82 (ngay dưới ngưỡng 0.85),
gây quá tải và mệt mỏi cho human reviewer (Alert Fatigue).

[Các thay đổi cụ thể về UI/UX và Architecture]:

1. Cải tiến về Kiến trúc & Routing Policy (Architecture):
   - Điều chỉnh Ngưỡng Động theo Mức độ Rủi ro (Dynamic Risk-based Thresholds):
     * Gửi email là hành động low-risk, không có rủi ro tài chính hay phá hủy dữ liệu.
       Do đó, có thể hạ ngưỡng auto-execute của `send_email` từ 0.85 xuống 0.80.
       (Ngưỡng 0.85+ chỉ nên áp dụng bắt buộc cho high-risk financial actions).
   - Cơ chế Phân tầng 3 mức (Tiered Review):
     * Confidence >= 0.80: Auto-execute ngay lập tức.
     * 0.65 <= Confidence < 0.80: Đưa vào hàng đợi duyệt không đồng bộ (Async Queue).
     * Confidence < 0.65: Escalate khẩn cấp yêu cầu review ngay.
   - Kiểm toán theo Xác suất / Lấy mẫu ngẫu nhiên (Audit Sampling):
     * Cho phép tự động gửi email với confidence 0.82, nhưng chọn ngẫu nhiên 5-10%
       (25-50 email) đưa vào luồng kiểm toán hậu kỳ (Post-execution Review / Human-on-the-loop)
       thay vì chặn 100% (500 email).

2. Cải tiến về Giao diện & Trải nghiệm Người dùng (UI/UX):
   - Duyệt hàng loạt (Batch Approval / Bulk Actions):
     * Cung cấp nút "Approve All Low-Risk Emails (Score >= 0.80)" hoặc checkbox chọn nhiều,
       giúp xử lý 500 email chỉ với vài cú click thay vì 500 lần duyệt đơn lẻ.
   - Triage & gom nhóm thông minh (Smart Grouping / Categorization):
     * Gom nhóm các email theo phân khúc khách hàng hoặc cùng template lý do churn.
     * Chỉ highlight (làm nổi bật) các trường hợp ngoại lệ (anomalies) hoặc từ ngữ nhạy cảm.
   - Tối ưu thao tác nhanh (Keyboard Shortcuts & Fast Preview):
     * Hỗ trợ phím tắt (`A` để Approve, `R` để Reject, `Space` để xem trước) để tăng tốc độ duyệt.
"""


# ==============================================================================
# CÂU 3: RỦI RO CỦA LLM SELF-CONFIDENCE VÀ CÁCH CALIBRATE ĐIỂM SỐ
# ==============================================================================
"""
[Tình huống]:
Agent tự báo confidence 0.95 khi đề xuất `increase_credit_limit` nhưng lại sai về thu nhập thực tế.

[Phần 1: Tại sao việc chỉ phụ thuộc vào tự đánh giá của LLM lại nguy hiểm?]:
1. Ảo giác và Tự tin thái quá (LLM Overconfidence & Hallucination):
   - LLMs là mô hình xác suất sinh từ (next-token prediction), không có nhận thức chân lý nội tại.
   - Khi được yêu cầu tự chấm điểm, mô hình thường có xu hướng "tự tin giả tạo" (báo điểm 0.9 - 0.99)
     ngay cả khi các suy luận hoặc trích xuất số liệu nền tảng là hoàn toàn bịa đặt/sai lệch.
2. Thiếu đối soát thực tế (Lack of Grounding):
   - LLM không tự kiểm tra lại cơ sở dữ liệu gốc nếu không có công cụ xác thực (deterministic tools).
3. Rủi ro Tài chính & Tuân thủ (High Financial / Compliance Risk):
   - Cấp hạn mức tín dụng dựa trên thu nhập sai sẽ trực tiếp dẫn đến rủi ro nợ xấu, tổn thất tài chính
     cho tổ chức tín dụng và vi phạm quy định pháp lý ngân hàng.

[Phần 2: Làm thế nào để calibrate (hiệu chuẩn) điểm số trước bước routing?]:
1. Xác thực dữ liệu bằng Deterministic Verification Node (Code/DB Rule Layer):
   - Tạo một node trung gian truy vấn trực tiếp Database / Core Banking API để lấy thu nhập thực tế.
   - Tính toán độ lệch: `diff = abs(income_llm - income_db)`.
   - Nếu `diff > 0` hoặc dữ liệu không khớp -> Tự động ghi đè điểm confidence = 0.0 hoặc trừ điểm phạt.
2. Sử dụng Mô hình Kiểm định Độc lập (Critic / Validator Agent):
   - Tách rời Agent đề xuất và Agent thẩm định. Một LLM validator riêng biệt sẽ kiểm tra lại các trích dẫn,
     logic tính toán và đưa ra điểm số phản biện khách quan.
3. Kỹ thuật Hiệu chuẩn Thống kê (Statistical Calibration / Meta-Model):
   - Áp dụng các thuật toán hiệu chuẩn xác suất (như Temperature Scaling, Platt Scaling hoặc Isotonic Regression).
   - Huấn luyện một mô hình Machine Learning nhỏ (như Logistic Regression / XGBoost) nhận đầu vào là:
     (tính nhất quán của logit, độ dài lý giải, dữ liệu khách hàng) để dự đoán xác suất chính xác thực sự.
4. Hard Policy Guardrails (Chính sách Cứng):
   - Duy trì quy tắc kiến trúc không thể vượt qua: Mọi hành động tài chính quan trọng (như tăng hạn mức tín dụng)
     luôn bị chặn để Human Review (như Rule 1), bất kể điểm confidence được tính toán là bao nhiêu.
"""


def main():
    print("=" * 80)
    print("BÁO CÁO PHÂN TÍCH KIẾN TRÚC HUMAN-IN-THE-LOOP (HITL)")
    print("=" * 80)
    print("\n--- CÂU 1 ---")
    print("Lựa chọn: interrupt_after=['generate_email'] (hoặc interrupt_before=['routing_node'])")
    print("\n--- CÂU 2 ---")
    print("Giải pháp Alert Fatigue: Dynamic Thresholds, Batch Approval, Audit Sampling")
    print("\n--- CÂU 3 ---")
    print("Calibration: Deterministic Verification Layer, Critic Agent, Hard Guardrails")
    print("=" * 80)


if __name__ == "__main__":
    main()

