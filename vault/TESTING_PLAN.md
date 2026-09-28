# NutriMatch — Testing Plan

Drafted 2026-09-28. Covers the whole system: automated backend tests, browser end-to-end
tests of the real user journeys, a manual checklist for things that can't be automated,
and non-functional checks (RA 10173, security, performance). Work top to bottom — each
layer depends on the one above it.

Test accounts: `vault/test-logins.txt`. Reference design for visual checks: `feature/client`
worktree on `http://localhost:3002`.

---

## Where things stand (2026-09-28)

| Area | Status |
|---|---|
| Backend unit/API tests | 121 tests across 8 apps (`manage.py test`): accounts 29, scheduling 25, clinical 22, billing 13, profiles 9, communication 9, core 8, nutrition 6 |
| Known failing | 3 WebSocket tests in `communication.tests.MessageConsumerTests` time out — **already broken before 2026-09-28** (fail identically on a clean checkout of commit 533bd9d) |
| Frontend tests | None. No test tooling installed in `frontend/` |
| Seed data | `python manage.py seed` loads only FNRI food exchange data + system settings. No demo users/records |
| Database | Cleaned 2026-09-28 — only the 7 accounts, their profiles/availability, FNRI data, and settings remain. Backup: `C:\Users\PC\Documents\NutriMatch-db-backups\db-before-clean-2026-09-28.sqlite3` |

---

## 1. Demo data command — do this first

Build `python manage.py seed_demo` (idempotent, safe to re-run) that creates a known
starting state every test can rely on:

- **RNDs:** one pending admin verification (with a license photo), two verified with
  weekly availability, consultation formats (one video-only), fees, bios, languages.
- **Clients:** one brand new (no screening), one with a screening, one with an active RND
  and history.
- **History for the active client:** a meal plan with meals and food items, an NCP draft,
  3–4 progress records, a completed appointment with an invoice, a review, a few messages.

Also add a way to reset (wipe activity data and re-seed) so manual and automated runs
always start from the same point. Doubles as demo data for the capstone defense.

---

## 2. Backend tests — fill the gaps

- [ ] Fix the 3 failing WebSocket consumer tests (`communication.tests.MessageConsumerTests`).
- [ ] Meal logs: upsert per meal per day, photo upload (Cloudinary mocked), RND notified,
      client can only log meals from their own plan.
- [ ] Progress records: BMI auto-computed from the latest screening's height; null when no
      screening exists.
- [ ] Profile editing: `PATCH /auth/me/` edits name/phone but ignores email;
      `PATCH /client/profile/`; `PATCH /rnd/profile/` bio + consultation formats.
- [ ] `GET /client/screening/` list is scoped to the requesting client.
- [ ] Admin RND list returns a signed license-photo URL, never the raw public_id.
- [ ] **Access control (RA 10173):** a client can't read another client's screenings, meal
      plans, meal logs, progress, messages or invoices; an RND can't touch another RND's
      patients; the video `host_url` never appears in any client-facing response.

---

## 3. End-to-end browser tests (Playwright)

Install Playwright in `frontend/`, run against the real backend + `seed_demo` data.
Priority order: A–D are the core journey, do those first.

| # | Flow | What to check |
|---|---|---|
| A | **RND onboarding** | Register with a PRC license photo (JPG/PNG/WEBP ≤5 MB; PDF rejected) → email code → admin sees the photo on RND Verification and approves → RND sets availability, consultation formats, fee, bio |
| B | **Client onboarding** | Register → email code → login → screening. Check values against hand calculations (e.g. male, 172 cm, 90 kg, 31 y, lightly active → BMI 30.42 Obese II, BMR 1825, TDEE 2509.38) |
| C | **Discover & book** | Find an RND filters (specialization, language, mode), sort, pagination → profile → booking modal only offers the RND's formats and only their available days/hours → booking creates a pending appointment + pending relationship |
| D | **RND confirms** | Confirm is blocked until the client has a screening → confirming activates the relationship → video room created → client joins the consultation room |
| E | **Clinical care** | NCP record through all 4 phases + finalize → meal plan with FNRI foods → client sees it and logs meals (status, time, photo) → RND notified → progress record → client's Progress Tracker (charts, range filter) |
| F | **Billing** | Complete appointment → invoice with frozen commission → client pays via PayMongo test mode → webhook through ngrok → invoice paid → RND earnings updated |
| G | **Reviews** | Leave a review only after completion, only once → rating shows on Find an RND and the RND profile |
| H | **Admin** | Verify / reject / suspend / reinstate RNDs, change commission %, audit log entries appear |

**Edge cases to include:**
- Decline or cancel a pending first booking (relationship stays pending, not active)
- Rebook an RND after being discharged (relationship reopens as pending)
- RND not accepting new clients: new clients blocked, existing clients can still book
- Unverified RND never appears in Find an RND and can't be booked
- Booking a format the RND doesn't offer is rejected
- Dates around midnight Philippine time (UTC+8) — a booking must land on the chosen date
- Invalid uploads (wrong type, too large) on registration, meal logs, resources

---

## 4. Manual checklist

Things that are real external services or need human eyes:

- [ ] Gmail verification and password-reset codes arrive and work
- [ ] Jitsi video call between two devices/browsers (RND + client)
- [ ] PayMongo test cards (success and failure) with the ngrok webhook
- [ ] Cloudinary uploads: resources, meal-log photos, PRC license (license must not open
      without the signed link)
- [ ] Real-time chat with Redis running (`nutrimatch-redis` container)
- [ ] Phone-sized screens for every client page
- [ ] Side-by-side design comparison against `http://localhost:3002` for each ported page
- [ ] Email text and toasts read correctly (no leftover mock names or dates)

---

## 5. Non-functional checks

- **RA 10173 / privacy:** audit logs written for sensitive actions; consent text on
  registration; license photo private; minimum personal data in public views (reviews show
  first name + last initial only); only `food_name` stored from external food lookups.
- **Security:** auth rate limits still enforced; role checks on every endpoint (client vs RND
  vs admin); no secrets in the repo; CORS/allowed hosts correct.
- **Performance:** basic load check on RND search and the RND/client dashboards with
  `seed_demo` data; watch for N+1 queries.
- **Console hygiene:** fix the hydration-mismatch warnings (auth lives in localStorage, so
  role-dependent pages render differently on server vs browser — Appointments.vue is the
  known one; Profile Settings was fixed with `<ClientOnly>`).

---

## Suggested order

1. `seed_demo` command
2. Backend gap tests (section 2)
3. Playwright flows A–D, then E–H and edge cases
4. Manual checklist + non-functional checks before the defense

---

## Open decision

- Screening: ticking "Unintended weight loss" is saved but doesn't change the NRS-2002 score
  (the backend derives weight loss from screening history by design). Decide whether a
  first-time client's self-reported weight loss should count when there's no earlier
  screening to compare against.
