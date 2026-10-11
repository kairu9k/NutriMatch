# NutriMatch — Testing Plan

First drafted 2026-09-28, **updated 2026-10-11**. Covers automated backend tests, browser
end-to-end tests of the real user journeys, a manual checklist for things that can't be
automated, and non-functional checks (RA 10173, security, performance). Work top to bottom.

Test accounts: `vault/test-logins.txt` (local only, gitignored). Demo data:
`python manage.py seed_demo --reset` — rebuilds only the `@nutrimatch.test` accounts.

---

## Where things stand (2026-10-11)

| Area | Status |
|---|---|
| Backend unit/API tests | **351 tests** across 8 apps (`manage.py test accounts billing core profiles scheduling clinical nutrition communication`): scheduling 77, accounts 74, clinical 57, billing 40, communication 37, nutrition 26, profiles 26, core 14 |
| Known failing | Only the 3 WebSocket tests in `communication.tests.MessageConsumerTests` — they need Redis running (`REDIS_URL`); not installed on the dev machine |
| Frontend tests | None. No test tooling in `frontend/`; pages are checked by hand in the browser after each change |
| Demo data | **Done.** `seed_demo`: 5 RNDs + 7 clients + demo admin, each at a different stage (see the table below) |

**Demo journey stages** (all `@nutrimatch.test`, password in `test-logins.txt`):

| Account | Use it to test |
|---|---|
| Maria (RND) | Dashboard, My Patients, Appointments (To complete / Upcoming), NCP Records worklist, Meal Planning, Earnings with a released payout |
| Jose (RND) | Earnings without payout details (reminder card) |
| Angela (RND) | Not accepting new clients |
| Ramon (RND) | A booking request waiting over 24 hours |
| Kristine (RND) | Pending application — admin RND Verification |
| Ana | Brand-new client onboarding |
| Benjamin | Screened, no RND — Find an RND and booking |
| Carla | Full history with Maria, upcoming visit with payment due, NCP follow-up draft, meal plan + logs |
| Daniel | Jose's patient, one paid visit, low-sodium plan |
| Elena | First booking with Ramon, pending |
| Felix | At nutritional risk; paid visit ended yesterday, **not completed, no NCP** — To complete, NCP "No record yet", attention flags, room "Mark it complete" |
| Grace | **Discharged** — read-only chart, Discharged tab, rebooking reopens it |

---

## 1. Backend tests

Done since the first draft (now covered by tests): progress BMI from the screening height,
progress limits and the RND-only private note; NCP partial drafts, finalize minimum,
field limits, "other measurements" rules, context pre-fill, overview worklist; discharge
rules and read-only record; patient list / summary / meal-plan grouping; appointment board
and decline/cancel reason; client room info (no host link or RND notes); billing pages,
receipts, payouts; reminders; resources sharing; admin overview.

Still to add:

- [ ] Fix or skip-when-no-Redis the 3 WebSocket consumer tests.
- [ ] Meal-log photo upload (Cloudinary mocked) and the RND notification.
- [ ] `PATCH /auth/me/` ignores email; `PATCH /rnd/profile/` bio + formats + clinic address rules.
- [ ] One access-control sweep test: a client can't read another client's screening, meal
      plan, meal logs, progress, messages or invoices; an RND can't read another RND's
      patients (most endpoints are covered individually — this makes it one checklist).
- [ ] Appointment payload sent to clients includes the RND's full user record (email,
      phone) — decide and fix, then test that it's public-only (see "Open decisions").

---

## 2. End-to-end browser flows

Run against the real backend + `seed_demo` data. Each row lists what to check; A–F are the
core journey for the defense.

| # | Flow | What to check |
|---|---|---|
| A | **RND application** | 5-step application with PRC number + license photo → email code → "Application submitted" → admin sees it on RND Verification, approves (email sent) → RND signs in |
| B | **Client onboarding** | Register (consent checkboxes) → email code → onboarding: about you, health background, screening. Check: male, 172 cm, 90 kg, 31 y, lightly active → BMI 30.42 Obese II, BMR 1825, TDEE 2509.38 |
| C | **Find & book** | Filters (specialty, language, format, max fee) → profile (next open slots) → booking only offers the RND's formats and hours → pending request |
| D | **RND confirms & client pays** | Appointments → Requests → Review & confirm (screening shown) → invoice issued → client pays (PayMongo test) → receipt email → room link appears only when paid and inside the join window |
| E | **Consultation room** | Countdown; RND panel Patient / NCP / Progress; NCP draft saved from the room is linked to the consultation; **End & mark complete** → wrap-up list; Exit asks if the NCP form has unsaved changes; client panel shows only RND details, meal-plan targets, checklist |
| F | **NCP record** | Pre-fill from screening/progress, PES picker, live BMI / energy / macro checks, limits block Save draft, unsaved-changes prompt, Review lists what's missing, Finalize confirmation, record becomes read-only; follow-up carries over PES/targets and shows previous goals in Monitoring |
| G | **Meal plan** | Meal Planning starts on the patient list → create → send → client sees it and logs meals → adherence shows on the dashboard / My Patients / Client Detail |
| H | **Progress** | Record progress (chart + RND-only private note) → client Progress page shows the numbers but not the note |
| I | **Discharge** | Blocked while there's an upcoming consultation or NCP draft → reason → client notified + emailed → chart read-only → client rebooks → reopens on confirm |
| J | **Billing & payouts** | Client Billing (pay-by deadline, receipt print/resend) · RND Earnings (pending → posted after 3 days → paid out on the 5th, statement print, resend payout email) · cancel a paid visit → refund pending → admin marks refunded |
| K | **Resources & reminders** | Upload shares with nobody → share with confirmed clients → client library View / Download; automatic reminders (24 h / 1 h, payment due, meal logging) and RND-set repeating reminders; client mute + email opt-in |
| L | **Admin** | User overview (no passwords), deactivate with reason (login shows the support email), send password reset, audit log entries, appointments, billing & commission, payouts, platform reports |

**Edge cases to include:**
- Decline a request (reason required) and cancel a confirmed one (paid → refund pending)
- Unpaid at the start time → auto-cancelled, invoice voided
- RND not accepting new clients: new clients blocked, existing clients can still book
- Unverified / rejected RND never listed and can't sign in
- Booking a format the RND doesn't offer is rejected; in-person needs a clinic address
- Dates around midnight Philippine time (UTC+8) land on the chosen date
- Invalid uploads (type, size) on registration, profile photo, meal logs, resources
- Out-of-range values on screening, NCP and progress forms are refused with a clear message

---

## 3. Manual checklist

Real external services or things that need human eyes:

- [ ] Gmail verification, password reset, receipts, discharge and payout emails arrive and read correctly
- [ ] Jitsi video call between two devices (RND + client)
- [ ] PayMongo test cards (success and failure) with the ngrok webhook; the Billing page sync catches a missed webhook
- [ ] Cloudinary uploads; the PRC license only opens through the signed link
- [ ] Real-time chat with Redis running
- [ ] **Print / PDF:** client receipt, RND earnings statement, NCP record summary, meal plan
- [ ] **Phone width** on every page (DevTools phone view) — not yet checked: Billing print, the
      consultation room, the RND Reminders tab
- [ ] No leftover mock names, dates or placeholder numbers anywhere

---

## 4. Non-functional checks

- **RA 10173 / privacy:** consent stored at registration; audit rows for sensitive actions
  (record viewed by admin, deactivation, discharge, NCP deleted, payouts, refunds); license
  photo private; client-facing RND data public-only; RND private notes never reach the
  client; only `food_name` stored from external food lookups.
- **Security:** auth rate limits; role checks on every endpoint; no secrets in the repo
  (`.env`, `db.sqlite3`, `test-logins.txt` stay out of git); rotate the PayMongo webhook
  secret before deploying; CORS / allowed hosts.
- **Performance:** dashboards and list pages compute in batches (no per-row queries) —
  spot-check with `seed_demo` data; 3-second page load target from the proposal.
- **Console hygiene:** no errors or hydration warnings on the main pages.

---

## Suggested order before the defense

1. `seed_demo --reset`
2. Backend gaps (section 1)
3. Flows A–F, then G–L and the edge cases
4. Manual checklist + non-functional checks

---

## Open decisions

- **USDA FoodData Central:** cut on purpose (2026-09-04), but objective 3 in the proposal still
  mentions international nutrient databases — revise the objective with the adviser or add a
  small USDA fallback search (food name only).
- **Diet templates** for diabetes, hypertension, renal and weight management (objective 3) —
  not built yet.
- **Appointment payload** shows the RND's email and phone to clients — make it public-only.
- Screening: self-reported "unintended weight loss" on a first screening doesn't change the
  NRS-2002 score (weight loss is derived from screening history by design) — decide whether
  it should count when there's no earlier screening.
