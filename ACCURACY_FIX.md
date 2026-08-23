# Accuracy Fix — ParcelPilot Copilot

## What was fixed

The original implementation could produce an access-denied response for a valid order and relied too heavily on an LLM to decide policy outcomes.

This version makes high-risk cancellation and service-credit decisions deterministic and evidence-grounded:

1. Order/ticket lookups use exact identifier columns (`order_id`, `ticket_id`) rather than substring matching across every field.
2. Customer authorization is enforced before an operational record is returned.
3. Unauthorized customer records are never revealed.
4. Cancellation decisions use the authorized workbook order record plus the retrieved current SOP and active customer agreement.
5. Customer-specific agreements override the default current SOP when the retrieved agreement explicitly contains the relevant override.
6. The deprecated policy is never treated as current.
7. The README dataset snapshot is used for time-based questions when the order has not yet been picked up.
8. The final customer answer is natural language and does not expose internal tool/debug details.
9. The LLM is not trusted to calculate the cancellation fee or service-credit eligibility for the assessment's high-risk examples; it is used for open-ended questions only.

## Verified assessment scenario

For the supplied dataset:

**Authenticated account:** Northstar Logistics  
**Question:** Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.

The workbook shows:
- ORD-1001 → ACCT-001
- ACCT-001 → Northstar Logistics
- status → BOOKED
- pickup_actual_at → blank
- booked_at → 2026-08-16 09:00
- cancellation_requested_at → 2026-08-16 11:00

The active Northstar agreement states that Northstar may cancel any BOOKED shipment before pickup with no cancellation fee, regardless of how long ago it was booked.

The current cancellation SOP says BOOKED/not-yet-picked-up shipments are free within 30 minutes and otherwise cost INR 250 unless a customer agreement explicitly waives the fee.

Therefore the deterministic decision is:

**Cancellation allowed — fee ₹0.**

## Run

Windows:

```bat
python -m pip install -r requirements.txt
streamlit run app.py
```

Set `GROQ_API_KEY` in `.env` if you want LLM-powered open-ended answers. The ORD-1001 cancellation decision does not depend on the LLM.
