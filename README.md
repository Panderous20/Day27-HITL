# 🛡️ Day 27: Human-in-the-Loop (HITL) Agentic Workflow

Dự án mẫu triển khai kiến trúc **Human-in-the-Loop (HITL)** sử dụng **LangGraph** và **Streamlit** để kiểm soát các quyết định của AI Agent, đảm bảo an toàn (safety), tuân thủ chính sách (policy compliance) và ghi vết kiểm toán (audit logging).

---

## 📌 Tổng Quan Kiến Trúc

```
                +-------------------------+
                |    evaluate_customer    |
                +-------------------------+
                             |
                             v
                +-------------------------+
                |      route_action       |
                +-------------------------+
                 /                       \
  (increase_credit_limit OR conf < 0.85)   (send_email AND conf >= 0.85)
               /                           \
              v                             v
+--------------------------+    +-------------------------+
| execute_high_risk_action |    | execute_low_risk_action |
+--------------------------+    +-------------------------+
              X                              |
      (INTERRUPT BEFORE)                     v
              |                             END
              v
     Human Review (Streamlit)
     [Approve / Reject / Edit]
              |
              v
       Resume Execution
              |
              v
   Audit Log (audit_log.json)
              |
              v
             END
```

---

## ⚙️ Cài Đặt (Installation)

1. **Khởi tạo môi trường ảo (Khuyến nghị):**
   ```bash
   python -m venv .venv
   # Trên Windows:
   .venv\Scripts\activate
   # Trên Linux/macOS:
   source .venv/bin/activate
   ```

2. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Hướng Dẫn Sử Dụng (Usage)

### 1. Khởi chạy Giao diện Streamlit Dashboard
```bash
streamlit run app.py
```
Ứng dụng sẽ mở tại `http://localhost:8501`.

### 2. Chạy thử nghiệm Workflow trong UI
1. Nhập **Customer ID**:
   - `CUST_HIGH_001` (để kích hoạt trường hợp rủi ro cao: `increase_credit_limit`)
   - `CUST_LOW_002` (để kích hoạt trường hợp rủi ro thấp: `send_email`)
2. Nhấn **Run Evaluation**.
3. Nếu phát hiện hành động rủi ro cao, graph sẽ **tạm dừng (interrupted)** và hiển thị **Action Card**:
   - **Approve**: Phê duyệt action và tiếp tục thực thi.
   - **Reject**: Từ chối và hủy thực thi action.
   - **Edit**: Mở rộng bảng chỉnh sửa để sửa đổi `proposed_action`, sau đó bấm **Submit Edit & Resume**.

---

## 🎯 Chính Sách Định Tuyến & Ngưỡng Quyết Định

### 1. Confidence Threshold
- **Ngưỡng sử dụng:** `0.85`
- **Low-Risk Action (`send_email`)**:
  - `confidence >= 0.85` $\rightarrow$ **Auto-Execute** (`execute_low_risk_action`).
  - `confidence < 0.85` $\rightarrow$ **Escalate sang Human Review** (`execute_high_risk_action`).

### 2. Hard Policy Rule (Chính sách Cứng)
- Với hành động tài chính rủi ro cao: **`increase_credit_limit`**
- **Bắt buộc Human Review** thông qua `interrupt_before=["execute_high_risk_action"]` **bất kể điểm `confidence_score` là bao nhiêu** (kể cả `0.99`).

---

## 📜 Nhật Ký Kiểm Toán (Audit Logging)

Tất cả các hành động sau khi có quyết định của con người đều được lưu trữ append-only vào file:
```
audit_log.json
```

### Schema AuditEntry ([`models.py`](file:///d:/Project/Day27-HITL/models.py)):
```json
{
  "timestamp": "2026-08-31T00:54:34.123456",
  "agent_id": "churn-risk-agent",
  "action": "increase_credit_limit",
  "confidence": 0.96,
  "reviewer_id": "operator_01",
  "decision": "approve"
}
```

---

## 📁 Cấu Trúc Repository

```
Day27-HITL/
├── .gitignore          # Cấu hình bỏ qua cache, venv, secrets, logs
├── app.py              # Streamlit UI & HITL approval interface
├── audit_log.json      # Lịch sử ghi vết kiểm toán (Audit trail)
├── graph.py            # LangGraph state, nodes, routing, checkpointer
├── models.py           # Pydantic schemas (AuditEntry)
├── report.py           # Báo cáo phân tích kiến trúc HITL & câu trả lời lý thuyết
├── requirements.txt    # Danh sách thư viện phụ thuộc
└── README.md           # Tài liệu hướng dẫn sử dụng
```

---

## 🔒 Bảo Mật & Tuân Thủ (Security)
- Repository **không lưu trữ** API key, Access token, Password, hay Private key.
- Toàn bộ file cấu hình môi trường `.env` thực tế đã được khai báo loại trừ trong `.gitignore`.

