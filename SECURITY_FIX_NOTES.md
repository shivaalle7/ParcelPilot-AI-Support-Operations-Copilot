# Security / Order Lookup Fix

The screenshot showed the security layer working, but the customer-facing
message was misleading for an order that could not be matched to the current
account.

This version:
- recognizes account IDs and account names across common Excel column names;
- accepts `NORTHSTAR`, `Northstar Logistics`, etc. as the same account;
- keeps cross-account records blocked;
- reports "not found in your account" when an order cannot be matched;
- does not leak another customer's record.

For the assessment demo, use the real `ORD-1001` from the supplied workbook.
Do not hard-code the example answer.
