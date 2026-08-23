from tools.actions import prepare_escalation, execute_pending

def test_action_requires_confirmation():
    item = prepare_escalation("TKT-1","High","test","test summary")
    assert item["id"]
    result = execute_pending(item["id"])
    assert result["status"] == "created"
