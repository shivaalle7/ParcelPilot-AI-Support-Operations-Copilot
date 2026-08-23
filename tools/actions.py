from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

@dataclass
class PendingAction:
    id: str
    action: str
    ticket_id: str | None
    priority: str
    reason: str
    summary: str
    message: str

_ACTIONS = {}

def prepare_escalation(ticket_id, priority, reason, summary):
    action_id = str(uuid.uuid4())[:8]
    item = PendingAction(
        id=action_id,
        action="create_escalation",
        ticket_id=ticket_id,
        priority=priority,
        reason=reason,
        summary=summary,
        message=f"Prepared {priority} escalation for {ticket_id}. Confirm to create it."
    )
    _ACTIONS[action_id] = asdict(item)
    return asdict(item)

def execute_pending(action_id):
    item = _ACTIONS.get(action_id)
    if not item:
        return {"error": "Pending action not found or already executed."}
    result = {
        "status": "created",
        "escalation_id": "ESC-" + str(uuid.uuid4())[:8].upper(),
        "created_at": datetime.utcnow().isoformat(),
        **item,
    }
    _ACTIONS.pop(action_id, None)
    return result
