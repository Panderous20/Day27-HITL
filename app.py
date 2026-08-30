import streamlit as st
from graph import graph

st.set_page_config(page_title="HITL Approval Dashboard", layout="centered")

st.title("🛡️ Human-in-the-Loop (HITL) Dashboard")

# Khởi tạo compiled graph trong session_state
if "graph" not in st.session_state:
    st.session_state.graph = graph

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "customer_thread_1"

config = {"configurable": {"thread_id": st.session_state.thread_id}}

st.subheader("1. Khởi chạy Agent Evaluation")
customer_id = st.text_input("Customer ID", value="CUST_HIGH_001")

if st.button("Run Evaluation"):
    initial_state = {
        "customer_id": customer_id,
        "proposed_action": "",
        "confidence_score": 0.0,
        "reasoning": "",
        "human_decision": None,
    }
    # Invoke graph lần đầu
    st.session_state.graph.invoke(initial_state, config)
    st.rerun()

# Lấy pending state hiện tại từ checkpointer
current_state = st.session_state.graph.get_state(config)

if current_state and current_state.values:
    state_values = current_state.values
    next_nodes = current_state.next

    # Kiểm tra xem graph có đang bị tạm dừng chờ duyệt không
    if "execute_high_risk_action" in next_nodes:
        st.warning("⚠️ High-Risk Action Detected - Yêu cầu Human Review")
        
        # Render Action Card
        with st.container(border=True):
            st.markdown("### 📋 Action Card")
            st.write(f"**Customer ID:** {state_values.get('customer_id')}")
            st.write(f"**Proposed Action:** `{state_values.get('proposed_action')}`")
            st.write(f"**Confidence:** `{state_values.get('confidence_score')}`")
            st.write(f"**Reasoning:** {state_values.get('reasoning')}")

            # Thao tác Edit nếu cần
            with st.expander("✏️ Chỉnh sửa Action trước khi duyệt (Edit)"):
                edited_action = st.text_input(
                    "Chỉnh sửa proposed_action:",
                    value=state_values.get("proposed_action", ""),
                    key="edit_action_input"
                )
                if st.button("Submit Edit & Resume"):
                    st.session_state.graph.update_state(
                        config,
                        {
                            "human_decision": "edit",
                            "proposed_action": edited_action,
                        }
                    )
                    st.session_state.graph.invoke(None, config)
                    st.success(f"Đã cập nhật action thành '{edited_action}' và tiếp tục thực thi!")
                    st.rerun()

            # Các nút Approve / Reject
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", use_container_width=True, type="primary"):
                    st.session_state.graph.update_state(
                        config,
                        {"human_decision": "approve"}
                    )
                    st.session_state.graph.invoke(None, config)
                    st.success("Đã phê duyệt action và tiếp tục thực thi!")
                    st.rerun()

            with col2:
                if st.button("❌ Reject", use_container_width=True):
                    st.session_state.graph.update_state(
                        config,
                        {"human_decision": "reject"}
                    )
                    st.session_state.graph.invoke(None, config)
                    st.info("Đã từ chối action và tiếp tục thực thi!")
                    st.rerun()
    else:
        st.success("✅ Graph đã hoàn thành thực thi.")
        with st.expander("Xem State hiện tại"):
            st.json(state_values)
