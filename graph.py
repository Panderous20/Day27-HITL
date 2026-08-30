import json
import os
from datetime import datetime
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from models import AuditEntry


class GraphState(TypedDict):
    customer_id: str
    proposed_action: str
    confidence_score: float
    reasoning: str
    human_decision: str | None


def evaluate_customer(state: GraphState) -> dict:
    customer_id = state.get("customer_id", "")
    
    # Mock đánh giá TOI và churn probability của khách hàng
    if "high" in customer_id.lower() or "limit" in customer_id.lower():
        return {
            "proposed_action": "increase_credit_limit",
            "confidence_score": 0.96,
            "reasoning": "Customer has high churn probability and increasing the credit limit may improve retention.",
        }
    else:
        return {
            "proposed_action": "send_email",
            "confidence_score": 0.92,
            "reasoning": "Customer has moderate churn probability and no high-risk financial action is required.",
        }


def route_action(state: GraphState) -> str:
    proposed_action = state.get("proposed_action", "")
    confidence_score = state.get("confidence_score", 0.0)

    # Rule 1 - Policy Override: Hành động tài chính rủi ro cao luôn cần duyệt
    if proposed_action == "increase_credit_limit":
        return "execute_high_risk_action"

    # Rule 2 - Auto-Execute: Low-risk và confidence cao (>= 0.85)
    if confidence_score >= 0.85:
        return "execute_low_risk_action"

    # Rule 3 - Escalate/Suggest: Confidence thấp (< 0.85) ép buộc human review
    return "execute_high_risk_action"


def execute_low_risk_action(state: GraphState) -> dict:
    return state


def execute_high_risk_action(state: GraphState) -> dict:
    human_decision = state.get("human_decision", "")
    proposed_action = state.get("proposed_action", "")
    confidence_score = state.get("confidence_score", 0.0)

    # Kiểm tra human_decision
    decision_lower = str(human_decision).lower()
    if decision_lower == "approve":
        print(f"[EXECUTED] Action approved: {proposed_action}")
    elif decision_lower == "reject":
        print(f"[ABORTED] Action rejected: {proposed_action}")
    elif decision_lower == "edit":
        print(f"[EXECUTED] Action modified and approved: {proposed_action}")
    else:
        print(f"[UNKNOWN DECISION] Decision: {human_decision}")

    # Khởi tạo AuditEntry
    audit_entry = AuditEntry(
        timestamp=datetime.now().isoformat(),
        agent_id="churn-risk-agent",
        action=proposed_action,
        confidence=confidence_score,
        reviewer_id="operator_01",
        decision=str(human_decision),
    )

    # Ghi vào audit_log.json
    log_path = "audit_log.json"
    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = []
        except Exception:
            logs = []

    logs.append(audit_entry.model_dump())
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    return state


# Build graph
builder = StateGraph(GraphState)

# Add nodes
builder.add_node("evaluate_customer", evaluate_customer)
builder.add_node("execute_low_risk_action", execute_low_risk_action)
builder.add_node("execute_high_risk_action", execute_high_risk_action)

# Add edges
builder.add_edge(START, "evaluate_customer")
builder.add_conditional_edges("evaluate_customer", route_action)
builder.add_edge("execute_low_risk_action", END)
builder.add_edge("execute_high_risk_action", END)

# Memory checkpointer
memory = MemorySaver()

# Compile graph với interrupt_before
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["execute_high_risk_action"]
)

