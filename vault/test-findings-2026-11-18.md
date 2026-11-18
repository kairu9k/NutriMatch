# Pre-launch test findings (2026-11-18)

Plan: `vault/test-plan-2026-11-18.md`. Fresh scratch database, Brave, 127.0.0.1:3001 / localhost:3001 against 127.0.0.1:8001.

## Automated checks
- Backend suite: 642 tests OK (serial run; the `--parallel 4` run crashed with "cannot pickle 'traceback' object", a Django runner limit on Windows, not a test failure).
- `makemigrations --check`: no changes.

## Findings

| # | Where | What | Cause | Fix | Proof |
|---|-------|------|-------|-----|-------|
| 1 | RND dashboard, Earnings | "It needs ₱500.00 cleared and your payout details" shown right after payout details were saved | The sentence listed both conditions whenever `eligible` was false | Name payout details only when `has_payout_account` is false (`RNDDashboard.vue`) | Fresh RND with payout details |
| 2 | RND welcome pop-up | "Add payout details" button and step text right after the RND entered them in onboarding | The copy was written before payout moved into onboarding | The pop-up reads `/rnd/payout-account/`; with details saved it says "Open Earnings" and "Your payout details are on the Earnings page" (`WelcomeModal.vue`) | Reloaded: buttons "Open Earnings, Go to my dashboard" |
| 3 | Client dashboard | "Hi Carlo, welcome back." on the very first visit, right after onboarding | Fixed greeting | "welcome back" only once `welcome_seen_at` is set (`ClientDashboard.vue`) | First visit now reads "Hi Carlo." |
| 4 | Client Pay (`POST /api/client/invoices/<id>/pay/`) | The reply sent the client NutriMatch's `commission_pct`/`commission_amt`, admin `notes` and the gateway reference | The view returned the full admin-style `InvoiceSerializer` | Reply is only `id, amount, status, payment_url` (`billing/views.py`) | `test_initiate_payment_view` RED then GREEN, billing 65/65 |
| 5 | Consultation room, video | With both people connected (live video both ways), the RND still read "Carlo hasn't joined… mark a no-show" and the client "Report that Rita didn't show up" for up to 30–60 s | The notes come from the appointment's attendance, re-read only on a 30 s (RND) / 60 s (client) timer; nothing re-read it when the other person arrived | `VideoCall.vue` emits `peer-joined`; the room re-reads attendance for both roles at once (`onPeerJoined`). The server's own checks were already right (the API reported `rnd_in_call: true`) | Two Brave tabs, notes cleared after the join |
| 6 | Consultation room | Wrap-up note "6 minutes left" while the timer said "5 min left" | Note rounded up (`ceil`), timer rounded (`dur`) | Note rounds like the timer (`minsLeftText`) | Both showed 5 |
| 7 | Consultation room, RND | "Stay in the call for 5 more minute(s)" | Hard-coded "(s)" | "1 more minute" / "N more minutes" | Seen live: "Stay in the call 5 more minutes" |
| 8 | Consultation room, client | Finish screen said "Rita has marked it complete" when the call closed it by itself | Copy from before the automatic close | "Your consultation with Rita is complete." | Read in code |
| 9 | Consultation room, client | After the consultation was cancelled or finished, the side panel still said "Upload them so Rita can see them during the call" and "Before your call" | Panels shown in every state | Shown only while the consultation is confirmed | Cancelled room reloaded |
| 10 | Room and Client Detail | "from the Nov 18, self-reported at screening weight" | Phrase built around the source | "from the weight on Nov 18, self-reported at screening" | Seen live |
| 11 | Everywhere the type is shown (RND Appointments, Help & Support picker, admin) | "In Person" with a capital P | `Appointment.Type.IN_PERSON` label | Label "In person" (`scheduling/0012_in_person_label`, choices only, no data change) | Migration applied to scratch DB |
| 12 | Admin Support, Admin Appointments, RND notification | A dispute about a completed in-person visit was titled "No-show dispute" | Wording from before in-person disputes existed | "Consultation dispute" / "Dispute:" / "Dispute decided" | Read in code |

## What was walked through in the browser (Brave)

| Step | Result |
|------|--------|
| RND registration (licence photo, selfie, specializations, consent), email code, "Application sent" | Works |
| Sign-in refused while the application waits | Works ("still under review") |
| Admin approves after the 4-point check, approval email | Works |
| RND onboarding (profile, fee and formats with clinic, weekly hours for all week, payout), welcome pop-up | Works (findings 1, 2) |
| Client registration, email code, onboarding with allergy and screening (BMI 29.4 Obese I, BMR 1526, TER 2500 checked by hand) | Works (finding 3) |
| Find an RND, book 12:00 PM, RND reviews the screening and confirms, invoice | Works |
| PayMongo test checkout (GCash), Billing sync to Paid, receipt email | Works (finding 4) |
| Video call between two tabs, attendance recorded, 15 and 5 minute notes, call ends at the scheduled end | Works (findings 5, 6, 7) |
| Video consultation completes by itself (6 min together), summary, RND earnings ₱720 on hold | Works (finding 8) |
| Nobody joined: closes by itself as a full refund | Works |
| RND absent: client reports 15 min after the start, cancelled, refund pending | Works (finding 9) |
| No-show: locked until the RND had 5 minutes in the call, then marked; client sees the note and the Help & Support line | Works |
| Reschedule: RND offers a later time only (4 PM held slot skipped), client proposes another, RND accepts, same paid invoice | Works |
| In-person: RND marks complete from To complete; client disputes in Help & Support (SR-0001), page shows "You disputed this" | Works (finding 11) |
| Admin decides the dispute (refund), invoice Refund pending, reply sent | Works (finding 12) |
| Refund through PayMongo (test mode) on an auto-refunded consultation: PayMongo confirms, invoice Refunded | Works |
| Payout run: ₱1,440 cleared by Nov 5, released with a reference, Paid out | Works |
| Admin dashboard and Billing figures (commission only on kept payments) | Add up |
| Phone width (390 px) for 22 client, RND and admin pages | No sideways scroll |

## Not a bug (checked)
- Find an RND cards have no fee: removed on purpose (commit e16be33); the fee shows on the profile and in booking.
- Admin dashboard "2 things to do today" vs "3 things need your attention": the headline counts the admin's own to-dos; the third is a "keep an eye on" item.
- `UnicodeEncodeError` for "₱" in the backend log: only the console email backend on Windows (test setup with Gmail blank). Real email goes through Gmail or Brevo; the error was caught and the payment was not affected.
- The parallel test run crash ("cannot pickle 'traceback'"): Django's parallel runner on Windows; the serial run is the result.

## Not covered this time
- The NCP form, meal plan, meal logs, labs and review flows were not repeated (full pass on Nov 16; only wording changed since).
- Video call on two real devices or a phone network (both sides were tabs on this PC).

## Before going live
- Migrations that run on Render's start: `scheduling/0011_reschedule_proposals`, `scheduling/0012_in_person_label`, `communication/0011_support_dispute_label`. Every new choice value fits its column (checked against Postgres length rules).
- No new environment variables.
- `rnd-design-pass` is 12 commits ahead of `main`, `main` has nothing new, so merging is a fast-forward. Pushing `main` deploys Render and Vercel.
