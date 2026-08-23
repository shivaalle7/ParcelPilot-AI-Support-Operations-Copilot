
import re
from datetime import datetime
import pandas as pd


def _norm(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _parse_dt(value):
    if value is None or value == "":
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        # README stores the snapshot as e.g. "2026-08-16 11:00 Asia/Kolkata".
        # Strip the named timezone for deterministic interval arithmetic; all
        # workbook timestamps are in the same local timezone.
        cleaned = re.sub(r"\s+[A-Za-z]+/[A-Za-z_]+\s*$", "", str(value))
        dt = pd.to_datetime(cleaned, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.to_pydatetime() if hasattr(dt, "to_pydatetime") else dt


def _docs_for(evidence, source_type=None, customer=None):
    out = []
    for e in evidence:
        if source_type and e.get("source_type") != source_type:
            continue
        if customer and e.get("customer") and _norm(e.get("customer")) != _norm(customer):
            continue
        out.append(e)
    return out


def _combined(evidence):
    return "\n".join(str(e.get("content", "")) for e in evidence).lower()


def evaluate_cancellation(order, evidence, customer_name=None):
    """
    Deterministic cancellation decision for the supplied ParcelPilot source model.
    The order facts come from the authorized workbook record. Policy/override facts
    come from retrieved current documents. No order/customer is hard-coded.
    """
    if not order:
        return None

    status = str(order.get("status", "")).strip().upper()
    booked_at = _parse_dt(order.get("booked_at"))
    requested_at = _parse_dt(order.get("cancellation_requested_at"))
    pickup_actual = _parse_dt(order.get("pickup_actual_at"))

    if status == "DRAFT":
        return {
            "decision": "allowed",
            "fee_inr": 0,
            "answer_type": "cancellation",
            "reason": "Draft shipments may be cancelled without a fee.",
            "facts": {"status": status, "pickup": "Not picked up"},
        }

    if status in {"PICKED_UP", "DELIVERED"}:
        if status == "PICKED_UP":
            reason = "The shipment has already been picked up, so the cancellation SOP does not allow a normal cancellation; the return-to-origin workflow should be used instead."
        else:
            reason = "The shipment has already been delivered, so it cannot be cancelled."
        return {
            "decision": "not_allowed",
            "fee_inr": None,
            "answer_type": "cancellation",
            "reason": reason,
            "facts": {"status": status, "pickup": "Picked up" if pickup_actual else status},
        }

    if status != "BOOKED":
        return {
            "decision": "needs_review",
            "fee_inr": None,
            "answer_type": "cancellation",
            "reason": f"The order is in {status or 'an unknown'} status, which is not covered by the standard cancellation cases in the supplied SOP.",
            "facts": {"status": status},
        }

    pickup_state = "Picked up" if pickup_actual else "Not picked up"

    # Find an active customer agreement. The retrieved agreement is the authority;
    # we only apply it when its text actually contains the relevant cancellation rule.
    agreement_docs = _docs_for(evidence, "customer_agreement", customer_name)
    agreement_text = "\n".join(str(d.get("content", "")) for d in agreement_docs).lower()

    has_no_fee_override = (
        "no cancellation fee" in agreement_text
        and "booked" in agreement_text
        and "before pickup" in agreement_text
    )

    if has_no_fee_override:
        return {
            "decision": "allowed",
            "fee_inr": 0,
            "answer_type": "cancellation",
            "reason": "The active customer agreement explicitly waives the cancellation fee for BOOKED shipments before pickup, overriding the default fee rule.",
            "facts": {
                "status": status,
                "pickup": pickup_state,
                "agreement_override": True,
                "requested_at": requested_at.isoformat() if requested_at else None,
                "booked_at": booked_at.isoformat() if booked_at else None,
            },
            "authority": "customer_agreement",
        }

    # Default SOP: no fee within 30 minutes; INR 250 after 30 minutes.
    elapsed_minutes = None
    if booked_at and requested_at:
        elapsed_minutes = (requested_at - booked_at).total_seconds() / 60

    if elapsed_minutes is None:
        return {
            "decision": "needs_review",
            "fee_inr": None,
            "answer_type": "cancellation",
            "reason": "The order is BOOKED and not picked up, but the booking/cancellation timestamps needed to determine the default 30-minute fee window are missing.",
            "facts": {"status": status, "pickup": pickup_state},
        }

    if elapsed_minutes <= 30:
        fee = 0
    else:
        fee = 250

    return {
        "decision": "allowed",
        "fee_inr": fee,
        "answer_type": "cancellation",
        "reason": "The current SOP permits cancellation before pickup and applies its 30-minute fee window because no applicable customer agreement override was found.",
        "facts": {
            "status": status,
            "pickup": pickup_state,
            "minutes_after_booking": round(elapsed_minutes, 1),
            "agreement_override": False,
        },
        "authority": "current_sop",
    }


def evaluate_service_credit(order, evidence, customer_name=None, snapshot_time=None):
    """
    Deterministic service-credit decision using the order record, current SOP and
    customer agreement. For an unpicked order, the dataset snapshot is used as
    the reference time when supplied.
    """
    if not order:
        return None

    pickup_end = _parse_dt(order.get("pickup_window_end"))
    actual = _parse_dt(order.get("pickup_actual_at"))
    snapshot = _parse_dt(snapshot_time)
    carrier_fault = bool(order.get("carrier_fault", False))
    customer_fault = bool(order.get("customer_fault", False))
    shipment_fee = float(order.get("shipment_fee_inr") or 0)

    if not pickup_end:
        return {
            "decision": "needs_review",
            "answer_type": "service_credit",
            "reason": "The scheduled pickup-window end time is missing.",
        }

    reference = actual or snapshot
    if not reference:
        return {
            "decision": "needs_review",
            "answer_type": "service_credit",
            "reason": "The pickup completion time or dataset snapshot time is missing.",
        }

    delay_hours = (reference - pickup_end).total_seconds() / 3600

    agreement_docs = _docs_for(evidence, "customer_agreement", customer_name)
    agreement_text = "\n".join(str(d.get("content", "")) for d in agreement_docs).lower()

    # LumenWorks-style override is derived from the agreement text rather than
    # hard-coded to an account name.
    m_hours = re.search(r"more than\s+(\d+(?:\.\d+)?)\s*hours", agreement_text)
    m_credit = re.search(r"fixed\s+inr\s+([\d,]+)", agreement_text)
    has_override = (
        "service credit" in agreement_text
        and "carrier is at fault" in agreement_text
        and m_hours is not None
        and m_credit is not None
    )

    if not carrier_fault or customer_fault:
        return {
            "decision": "not_eligible",
            "answer_type": "service_credit",
            "reason": "A service credit requires carrier fault and no customer-caused issue.",
            "facts": {"delay_hours": round(delay_hours, 2), "carrier_fault": carrier_fault, "customer_fault": customer_fault},
        }

    if has_override:
        threshold = float(m_hours.group(1))
        credit = float(m_credit.group(1).replace(",", ""))
        eligible = delay_hours > threshold
        return {
            "decision": "eligible" if eligible else "not_eligible",
            "credit_inr": int(credit) if credit.is_integer() else credit,
            "answer_type": "service_credit",
            "reason": "The active customer agreement replaces the default service-credit threshold and amount.",
            "facts": {
                "delay_hours": round(delay_hours, 2),
                "threshold_hours": threshold,
                "carrier_fault": carrier_fault,
                "customer_fault": customer_fault,
                "agreement_override": True,
            },
            "authority": "customer_agreement",
        }

    # Default SOP: >2 hours, carrier fault, no customer fault; lower of INR 500 or 10%.
    eligible = delay_hours > 2
    credit = min(500, 0.10 * shipment_fee) if eligible else 0
    return {
        "decision": "eligible" if eligible else "not_eligible",
        "credit_inr": round(credit, 2),
        "answer_type": "service_credit",
        "reason": "The current SOP default applies because no applicable customer-agreement override was found.",
        "facts": {
            "delay_hours": round(delay_hours, 2),
            "threshold_hours": 2,
            "carrier_fault": carrier_fault,
            "customer_fault": customer_fault,
            "agreement_override": False,
        },
        "authority": "current_sop",
    }


def format_cancellation_answer(customer_name, order_id, result):
    if result["decision"] == "allowed":
        fee = result.get("fee_inr")
        if fee == 0:
            if result["facts"].get("agreement_override"):
                return (
                    f"Yes. {customer_name} can cancel {order_id} without a cancellation fee.\n\n"
                    f"{order_id} is currently {result['facts'].get('status')} and has not been picked up. "
                    f"{customer_name}'s active customer agreement specifically allows BOOKED shipments to be "
                    f"cancelled before pickup without a fee, regardless of how long ago the shipment was booked. "
                    f"That agreement takes precedence over the standard cancellation rule.\n\n"
                    f"Therefore, the applicable cancellation fee is ₹0."
                )
            return f"Yes. {order_id} can be cancelled before pickup without a fee because the request is within the standard 30-minute cancellation window."
        return (
            f"Yes. {order_id} can be cancelled before pickup, but the applicable cancellation fee is ₹{fee:,}. "
            f"The standard 30-minute no-fee window has passed and no applicable customer-agreement waiver was found."
        )

    if result["decision"] == "not_allowed":
        return f"{order_id} cannot be cancelled through the normal cancellation workflow. {result['reason']}"

    return f"I can't determine the cancellation outcome for {order_id} confidently yet. {result['reason']}"

def format_service_credit_answer(customer_name, order_id, result):
    if result["decision"] == "eligible":
        credit = result.get("credit_inr")
        return (
            f"Yes. Based on the supplied ParcelPilot records, {customer_name} is eligible for a "
            f"₹{credit:,.0f} service credit for {order_id}.\n\n"
            f"The pickup was {result['facts']['delay_hours']:.2f} hours past the scheduled pickup-window end, "
            f"carrier fault is recorded, and no customer fault is recorded. "
            f"The applicable customer agreement replaces the default service-credit rule."
        )
    if result["decision"] == "not_eligible":
        return f"Based on the supplied records, {customer_name} is not currently eligible for a service credit for {order_id}. {result['reason']}"
    return f"I can't determine the service-credit outcome for {order_id} confidently yet. {result['reason']}"
