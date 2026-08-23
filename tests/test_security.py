from security.auth import UserContext, authorize_record

def test_customer_cannot_access_other_account():
    user = UserContext("Customer","customer","NORTHSTAR","Northstar Logistics")
    assert authorize_record(user, {"account_id":"LUMENWORKS"}) is False

def test_customer_can_access_own_account():
    user = UserContext("Customer","customer","NORTHSTAR","Northstar Logistics")
    assert authorize_record(user, {"account_id":"NORTHSTAR"}) is True

def test_internal_can_access():
    user = UserContext("Internal Support","support_agent",None,None)
    assert authorize_record(user, {"account_id":"LUMENWORKS"}) is True

def test_customer_can_access_mapped_account_id():
    user = UserContext("Customer", "customer", "NORTHSTAR", "Northstar Logistics")
    assert authorize_record(user, {"account_id": "ACCT-001"}) is True

def test_customer_cannot_access_mapped_other_account_id():
    user = UserContext("Customer", "customer", "NORTHSTAR", "Northstar Logistics")
    assert authorize_record(user, {"account_id": "ACCT-002"}) is False

def test_customer_lumenworks_can_access_mapped_id():
    user = UserContext("Customer", "customer", "LUMENWORKS", "LumenWorks")
    assert authorize_record(user, {"account_id": "ACCT-002"}) is True

