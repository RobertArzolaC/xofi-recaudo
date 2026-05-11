# WhatsApp Response for Support Tickets — Implementation Plan

**Goal:** Enable assigned employees to send a final response to a support ticket via WhatsApp Cloud API, with confirmation dialog, message preview, and improved comment UI.

**Architecture:** Extends existing `TicketDetailView` with new WhatsApp response panel, adds `TicketWhatsAppResponseView` for handling the send action, and uses the existing `WhatsAppCloudAPIClient` from `core`. A new `is_whatsapp_response` field on `TicketComment` tracks sent responses.

**Tech Stack:** Django 5.x, WhatsApp Cloud API (Meta), SweetAlert2, Metronic theme

---

### Decision Log

| Decision | Alternative | Reason |
|---|---|---|
| `is_whatsapp_response` flag on `TicketComment` | Separate `TicketWhatsAppResponse` model | Reuses existing comment infrastructure, appears in timeline |
| Only assigned employee can respond | Any employee with `change_ticket` | Security: only the person handling the ticket can close it |
| Auto-mark as RESOLVED on send | No status change | Completes the workflow — response = resolution |
| SweetAlert2 confirmation | Bootstrap modal | Already used project-wide, simpler integration |
| Dedicated POST view | AJAX submission | Simpler, follows existing pattern (comment, status views) |

---

### Files Modified

| File | Change |
|---|---|
| `apps/support/models.py:164-168` | Add `is_whatsapp_response` BooleanField to `TicketComment` |
| `apps/support/forms.py:135-152` | Add `TicketWhatsAppResponseForm` |
| `apps/support/views.py:24-26` | Import `WhatsAppCloudAPIClient`, `choices` |
| `apps/support/views.py:73-76` | Add `whatsapp_form` and `partner_tickets` to detail context |
| `apps/support/views.py:177-254` | Add `TicketWhatsAppResponseView` |
| `apps/support/urls.py:37-41` | Add `ticket-whatsapp-response` URL |
| `templates/support/ticket/detail.html` | Full rewrite: WhatsApp panel, preview, confirmation, partner history, comment UI |
| `apps/support/migrations/0002_*.py` | Auto-generated migration for new field |

### Summary of Changes

1. **WhatsApp Response Panel** — Green-bordered card visible only to the assigned employee when ticket is open and partner has a phone number
2. **Message Preview** — Click "Preview" to see formatted message before sending
3. **SweetAlert2 Confirmation** — "Send WhatsApp Response?" dialog shows partner name/phone, confirms action
4. **Auto-close on Send** — Ticket status changes to RESOLVED, a `TicketComment` with `is_whatsapp_response=True` is saved
5. **Partner Ticket History** — New sidebar card showing last 5 tickets from the same partner
6. **Comment UI Improvements** — Color-coded borders (green=whatsapp, orange=internal, blue=public), badges with icons, "Copy to response" button on public comments, auto-scroll to latest comment
