# ParcelPilot UX v5

Customer-facing chat is now intentionally human-first.

Removed from the main customer experience:
- Retrieval index status
- Document chunk counts
- Mode / role / security / action-safety metrics
- Agent Activity panel
- Internal tool names

Kept:
- Simple account context
- Natural-language answer
- Optional "View supporting information" section
- Confirmation UI only when a real state-changing action is prepared

The backend still performs authorization and tool orchestration; those implementation
details are simply not shown to the customer.

The lookup layer was also fixed so a matching record from another account does not
cause an early rejection before the system searches for the authenticated customer's
matching record.
