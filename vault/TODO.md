# NutriMatch Capstone — To-Do List

Stack: Nuxt 4 + Tailwind CSS + Lucide icons (frontend, real team codebase) + Django 5 / DRF (backend, replacing Laravel) + PostgreSQL

**Frontend status (2026-09-04):** `frontend/` is now a clone of the team repo (`KPChiu7/NutriMatch-frontend`). Confirmed installed and running clean (`npm install` + `npm run dev` verified, no errors). This replaces the earlier from-scratch/Bootstrap plan — build on this codebase, don't rebuild it.

**Correction (2026-09-06):** local repo is actually checked out on `feature/landing-julia`, not `master` — the merge from PR #1 was done locally but never pushed to `origin/master` (which still only has the original bare Nuxt scaffold commit). `feature/landing-julia` has all the real work and is what CLAUDE.md's file/component descriptions refer to; kept as the working branch since user is now driving both frontend and backend directly (teammate branch-safety caveats no longer apply the same way — confirm before any push/force-op regardless).

**Scope decision (2026-09-04): Philippine food data only, for now.** FNRI Food Exchange Lists is the sole food source to build/seed/query. USDA FoodData Central integration is explicitly deferred — the `usda` schema option stays in `MealPlanFoodItem.source_type` for future extensibility, but no USDA service/endpoint gets built unless the user asks to revisit this later.

## Phase 0 — Backend setup ✅ DONE (2026-09-04)
- [x] Laravel deleted entirely, Django scaffolded directly in `backend/` (schema preserved in `database.txt`, no PHP reference kept)
- [x] `django-admin startproject nutrimatch_api .` + `.venv` (Python 3.13)
- [x] Installed: `django` (6.1.1), `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers`, `python-decouple`, `django-filter`, `httpx`
- [x] SQLite for dev (Postgres not installed on this machine yet — switch before deployment, Phase 8)
- [x] `.env` / `.env.example` wired via `python-decouple` (SECRET_KEY generated, PayMongo/Daily.co/USDA keys stubbed, empty)
- [x] `django-cors-headers` configured for `localhost:3000`
- [x] Custom `User` model in `accounts` app (role enum, soft-delete `deleted_at`, email as USERNAME_FIELD), registered in Django admin, migrated, verified via `manage.py check` + dev server boot (302 redirect on `/admin/` confirms working)

## Phase 1 — Data layer ✅ DONE (2026-09-04)
Reference: `database.txt` (authoritative DBML schema, 21 tables/6 groups)
6 apps created matching the schema's own functional groups, each with models + admin registration:
- [x] `accounts` — `User` (done in Phase 0)
- [x] `profiles` — `RndProfile`, `RndLanguage`, `RndAvailabilitySchedule`, `ClientProfile`, `ClientHealthProfile`
- [x] `scheduling` — `RndClientRelationship` (unique constraint on rnd+client pair), `Appointment`, `ConsultationSession`, `Review` (1-5 rating check constraint)
- [x] `clinical` — `PreConsultationScreening`, `NcpRecord` (ONE record with all 4 phase sections as fields — assessment/diagnosis-PES/intervention/monitoring — matching `frontend/app/components/NCPRecords.vue`'s implementation), `ProgressRecord`
- [x] `nutrition` — `FoodExchangeCategory`, `FoodExchangeItem`, `MealPlan`, `MealPlanMeal`, `MealPlanFoodItem` (RA 10173 data-minimization rule documented directly in the model docstring — only `food_name` persisted from external lookups, never a nutrient payload)
- [x] `communication` — `Message`, `Resource`, `Reminder`, `NotificationLog`
- [x] `billing` — `Invoice` (commission_amt auto-freezes at creation via `save()` override, never recomputed), `PaymentTransaction`
- [x] `core` — `SystemSetting`, `ApiCache` (documented as the one deliberate exception to data minimization — TTL'd cache only), `AuditLog` (admin-locked read-only/no-delete to enforce immutability)
- [x] `sessions`/`migrations` tables intentionally NOT ported — Django's own session/migration machinery replaces them
- [x] All migrations generated + applied cleanly (`manage.py check` clean, 21/21 domain tables confirmed present via `apps.get_models()`)
- [x] Fixed a real bug found along the way: `UserManager.create_superuser`/`create_user` passed `role` both positionally and via `**extra_fields` (since `role` is in `REQUIRED_FIELDS`), causing `createsuperuser` to crash — fixed by always merging role into `extra_fields` before calling `_create_user`
- [x] Verified superuser creation + Django admin login end-to-end

## Phase 2 — Auth ✅ DONE (2026-09-04)
- [x] Custom `User` model with role field — done in Phase 0/1
- [x] SimpleJWT setup: `POST /api/auth/login/` (returns access+refresh+user, role/full_name embedded as JWT claims), `POST /api/auth/refresh/`, `GET /api/auth/me/`
- [x] `POST /api/auth/register/client/` — creates `User` + `ClientProfile` + `ClientHealthProfile` transactionally. Accepts `primary_health_concern` (maps to `health_goals` JSON list) to match `RegisterFlow.vue`'s form fields. Frontend calls the client role "patient" — normalized to `client` server-side, not a field name to copy literally.
- [x] `POST /api/auth/register/rnd/` — creates `User` + `RndProfile` (unverified by default — matches proposal's manual PRC verification requirement)
- [x] Role-based DRF permission classes: `IsAdmin`, `IsRnd`, `IsClient` in `accounts/permissions.py` — ready to use on Phase 3 endpoints, not yet applied anywhere
- [x] Verified end-to-end via curl: register client, register RND, duplicate-email rejection, login (correct tokens + claims), `/me` with and without token (401 when missing), wrong-password rejection, related profile rows actually created with correct data. Test users cleaned from dev DB afterward.
- [ ] Still TODO: wire `frontend/app/components/LoginFlow.vue` and `RegisterFlow.vue`'s `console.log`/`navigateTo` stubs to actually call these endpoints (part of Phase 6's "wire to real data" step) — not done yet, backend is ready and waiting

## Phase 3 — Core API endpoints ✅ DONE (2026-09-04)
All endpoints built, mounted under `/api/`, verified end-to-end via a full scripted flow (register → verify RND → search → request relationship → RND accepts → book appointment → confirm → screening → NCP create/finalize → messages → food exchange). Test data cleaned from dev DB after each run.

- [x] Admin (`accounts`): `GET /admin/users/` (list, filterable by role), `GET /admin/users/<id>/`, `DELETE /admin/users/<id>/` (soft delete), `PATCH /admin/users/<id>/toggle-active/`, `PATCH /admin/users/<id>/verify-rnd/`
- [x] Client matching (`profiles`): `GET /client/rnds/` (filter by specialty/language, **only verified + accepting-new-clients RNDs shown** — confirmed unverified RNDs correctly hidden), `GET /client/rnds/<id>/` (includes average rating), `GET/PATCH /rnd/profile/` (RND self-service)
- [x] Relationship lifecycle (`scheduling`) — found and filled a real gap: the schema/proposal only described client-requests-relationship, with no explicit accept step, which would've made every relationship stuck at `pending` forever. Added: `POST /client/rnds/<id>/request/`, `GET /rnd/relationship-requests/` (RND's inbox), `PATCH /rnd/relationships/<id>/accept/` (pending → active)
- [x] Client appointments: `GET/POST /client/appointments/` (booking blocked unless relationship is active — verified), `GET /client/appointments/<id>/`, `PATCH /client/appointments/<id>/cancel/`
- [x] RND appointments: `GET /rnd/appointments/`, `GET /rnd/appointments/<id>/`, `PATCH .../confirm/`, `PATCH .../complete/`, `PATCH .../cancel/` (each enforces valid status transitions)
- [x] Reviews: `POST /client/reviews/` (only for own completed, not-yet-reviewed appointments)
- [x] Pre-consultation screening (`clinical`): `POST /client/screening/` — runs the calculation engine live (see below), `GET /client/screening/<appointment_id>/`
- [x] NCP records (`clinical`): `GET/POST /rnd/relationships/<id>/ncp/`, `GET/PATCH /rnd/ncp/<id>/`, `PATCH /rnd/ncp/<id>/finalize/` (draft → completed)
- [x] Food exchange (`nutrition`, FNRI only): `GET /food-exchange/categories/`, `GET /food-exchange/items/` (filterable by category/search/diabetes-hypertension-renal flags)
- [x] Messages (`communication`): `GET/POST /relationships/<id>/messages/` (scoped to the caller's own relationship), `DELETE /relationships/<id>/messages/<id>/` (soft delete, sender-only)
- [x] **`clinical/services.py`** — the nutritional calculation engine (Mifflin-St Jeor BMR, TDEE, WHO Asia-Pacific BMI classification, NRS-2002 scoring skeleton). Verified against hand calculation: 70kg/170cm/age 31/male/moderately_active → BMI 24.22 ("Overweight At Risk" per WHO Asia-Pacific 23–24.9 bracket, correctly NOT "Normal"), BMR 1612.50, TDEE 2499.38 — all exact matches. Age is derived from `ClientProfile.date_of_birth` at request time, not stored redundantly.

## Phase 4 — External service integrations ✅ DONE (2026-09-04)
No real API keys yet (PayMongo/Daily.co `.env` values still blank) — built structurally correct against each provider's documented API contract, verified with 13 passing tests using mocked `httpx.Client` (no real network calls). Real keys can be dropped into `.env` later with zero code changes.

- [x] `billing/services.py` — `PayMongoService` (`httpx`-based): `create_payment_link` (PHP→centavos conversion verified), `handle_webhook` (HMAC-SHA256 signature validation via `hmac.compare_digest`, ported exactly from the original Laravel logic), `get_payment_status`
- [x] `POST /api/client/invoices/<id>/pay/` — client-initiated payment, only for own unpaid invoices
- [x] `POST /api/webhooks/paymongo/` — no JWT auth (`AllowAny` + `authentication_classes = []`, `csrf_exempt`), signature validated inside the service; on `payment.paid` marks invoice paid + writes `PaymentTransaction` + `AuditLog` row; on unmatched reference returns 200 anyway (don't make PayMongo retry an event that isn't ours to match)
- [x] `scheduling/services.py` — `DailyCoVideoService`: `create_room` (auto-expiry from `appointment.duration_minutes`), `_generate_host_token` (owner-privilege token for the RND), `delete_room`
- [x] Wired into `RndAppointmentConfirmView`: confirming a `video`-type appointment auto-provisions a `ConsultationSession` + attaches the safe `participant_url` to the appointment. Confirmation still succeeds even if Daily.co fails (gateway hiccup shouldn't block confirming an appointment) — RND can retry video setup separately.
- [x] **Security invariant preserved and test-verified**: `host_url` (RND-only, grants owner controls) is never serialized into any client-facing response — `ConsultationSessionSerializer` only exposes `video_provider`/`session_status`/timing fields, confirmed via an explicit `assertNotIn` test.
- [x] ~~`UsdaFoodService`~~ — still deferred, out of scope (PH food data only, see scope note at top)
- [x] `NutritionCalculatorService` → done early, in Phase 3 as `clinical/services.py`
- [ ] `AuditService` — not built as a separate abstraction; `AuditLog.objects.create(...)` is called directly where it matters so far (e.g. on invoice-paid). Revisit if repetition becomes a problem.
- [x] Found and fixed a real bug along the way: `Invoice.commission_pct` (Phase 1) and `MealPlanFoodItem.exchanges` (Phase 1) used bare float literals (`default=10.00`, `default=1.0`) as Django `DecimalField` defaults — before the first `.save()` round-trips through the DB, the in-memory value is still a Python `float`, and `Decimal * float` raises `TypeError`. This only surfaced now because Phase 1's tests never actually saved an `Invoice`. Fixed both to `Decimal("10.00")`/`Decimal("1.0")`. No migration needed (Django's migration serializer already normalized the stored default identically either way — this was a pure Python-runtime bug, not a schema bug). Worth grep'ing for this pattern (`DecimalField.*default=[0-9]*\.[0-9]`) if more float-literal defaults show up later.

## Phase 5 — Background jobs (if needed)
- [ ] Redis + Celery setup
- [ ] Port any queued jobs (notifications, webhook post-processing)
- [ ] `celery worker` running alongside `runserver` in dev

## Phase 6 — Frontend: fill the gap between `drive/` mockups and current codebase

**Already built (confirmed present, verify against drive/ mockup for fidelity, don't rebuild):**
landing (`index.vue`), login, register (client+rnd combined flow), admin-dashboard, rnd-dashboard, appointments, audit-logs, availability, billing-commission (admin's commission view), meal-planning, messages, ncp-records (all 4 phases in one component), resource-library, reviews, rnd-verification, system-settings, profile-settings, my-patients, client-management (admin's client oversight), earnings, platform-reports

**Missing — no page/component yet, need to build:**
- [ ] `about.vue`, `contact.vue`, `privacy-policy.vue`, `terms.vue` — static marketing pages
- [ ] `404.vue`, `500.vue` (Nuxt error page conventions — `error.vue` at root, not `pages/`)
- [ ] `forgot-password.vue`, `reset-password.vue`
- [x] **`find-rnd.vue` built (2026-09-06)** — `FindRnd.vue` component + page, real data via `GET /client/rnds/`. Specialty (text, `icontains`) and language (dropdown) filters wired to the real query params the backend supports; consultation-mode filter and star ratings from the static mockup were dropped since neither exists on this endpoint (`RndSearchView` uses `RndProfileSerializer`, which has no `average_rating` — that's only added in `RndDetailView`) — didn't fake data that isn't there. Each card has a "Request" button calling `POST /client/rnds/<id>/request/` directly rather than linking to `rnd-profile-view.vue` (not built yet, separate TODO item) — `rnd-profile-view.vue` can link back here later once it exists. Added to client nav. Verified live: only verified+accepting RNDs shown (confirmed an unverified RND fixture correctly excluded), specialty filter narrows results correctly, Request creates a real `pending` `RndClientRelationship` row (confirmed via DB query), button becomes disabled/"Requested" after success.
- [x] **`book-appointment.vue` built (2026-09-06)** — `BookAppointment.vue` component + page. Added a new backend endpoint (`GET /client/relationships/`, `ClientActiveRelationshipsView` in `scheduling/`) since none existed to list which RNDs a client can actually book with — booking requires an ACTIVE relationship (`AppointmentCreateSerializer.validate_rnd_id` enforces this), and there was no way for the frontend to know which RNDs qualify. RND dropdown pre-selects from `?rnd=<id>` query param if present (for a future `rnd-profile-view.vue` "Book" link) or defaults to the first active relationship. Consultation type (video/chat/in-person), native `datetime-local` picker, duration (30/60/90 min), optional notes — submits to `POST /client/appointments/`. Deliberately did NOT replicate the static mockup's fake "available/unavailable" time-slot grid — no backend endpoint computes real slot availability (`RndAvailabilitySchedule` exists but isn't exposed via API), so a real datetime picker was used instead of faking availability data. Empty state (no active relationship yet) links to `find-rnd.vue`. Entry points added: "Book Appointment" button in `Appointments.vue` header (client only) and its empty state. Verified live end-to-end: booking against a real active relationship correctly creates a `pending` `Appointment` row, redirects to `/appointments`, and the new appointment renders correctly with working Cancel action. Test appointment cleaned up after.
- [x] **`client-dashboard.vue` built (2026-09-06), Overview tab only** — the static mockup has 8 tabs (Overview, Health Screening, My Tasks, Log Progress, Consultation Summaries, Resources, Reminders, Billing); deliberately scoped to Overview only since the other 7 need backend features that don't exist yet (task assignment, food/vitals logging, reminders CRUD, resource upload) — building them would mean faking data in the frontend, which this project has consistently avoided. Overview shows only real data: welcome banner (greeting + upcoming appointment or active-RND summary), stat cards (BMI/TDEE/NRS-2002/next appointment — each shows "—" when no data exists rather than a fake number), "Your RND" card (from `GET /client/relationships/`), "Latest Screening" card (from new `GET /client/screening/latest/` endpoint, added since none existed to fetch a client's own most recent screening without already knowing an appointment ID). Set as the client's post-login/post-register landing page (`LoginFlow.vue`/`RegisterFlow.vue` redirects updated from the `/appointments` placeholder), added to top of client nav. Health Screening + Consultation Summaries tabs are good near-term follow-ups (real data already exists, just needs small new read endpoints); Tasks/Logging/Reminders/Billing-on-dashboard need actual new backend features first — logged as separate future work, not attempted here. Verified live: real BMI 24.22/BMR 1613/TDEE 2499 rendered correctly with correct "Overweight (At Risk)" badge, active RND card, empty states correct when no screening/appointment exists. Test screening cleaned up after; client profile DOB/sex fixture kept (needed for BMR calc, reusable for future testing).
- [ ] `client-detail.vue` — RND's per-client chart/history view (distinct from `my-patients.vue` list)
- [ ] `consultation-room.vue` — video call UI (Daily.co embed)
- [ ] `invoices-billing.vue` — client-facing billing/payment history (distinct from admin's `billing-commission.vue`)
- [ ] `meal-plan-view.vue` — client's read-only view of their assigned meal plan
- [ ] `notifications.vue` — full notifications page (currently only `NotificationDropdown.vue` exists, a header widget)
- [ ] `pre-consultation-screening.vue` — NRS-2002/BMI intake form before first appointment
- [ ] `progress-tracker.vue` — client's BMI/labs/adherence over time (charts)
- [ ] `resource-upload.vue` — RND-side upload UI (distinct from `resource-library.vue`, which is browse/view)
- [ ] `rnd-profile-view.vue` — public-facing RND profile as seen by a prospective client (distinct from `profile-settings.vue`, which is the RND editing their own profile)
- [ ] Confirm `rnd-appointments.html` scope is fully covered by the existing shared `appointments.vue`, or needs an RND-specific variant

**Auth wiring ✅ DONE (2026-09-06):**
- [x] Pinia installed (`pinia` + `@pinia/nuxt`); `useAuthStore` (`app/stores/auth.ts`) holds `user`, `rndProfile`, `accessToken`/`refreshToken`, persisted to `localStorage`, hydrated on app start (`app.vue`)
- [x] API composable (`app/composables/useApi.ts`) — injects JWT bearer header via `runtimeConfig.public.apiBase` (from `.env`/`NUXT_PUBLIC_API_BASE`), auto-retries once via `/auth/refresh/` on 401
- [x] `LoginFlow.vue` wired to `POST /auth/login/` (regular + admin login), inline errors, loading state, role-based redirect (client→`/appointments` placeholder, rnd→`/rnd-dashboard`, admin→`/admin-dashboard`)
- [x] `RegisterFlow.vue` wired to `POST /auth/register/client/` and `.../rnd/` — step 2 now branches fields by role (patient: DOB/gender/health concern; RND: PRC license number/specialization, previously missing from the form). Auto-logs in on successful registration.
- [x] Verified live end-to-end via browser automation (not just typecheck): client register→login→redirect, wrong-password 401 handling, RND register→login→redirect — all confirmed via Django server logs + DB inspection. Test accounts cleaned up after each run.
- [x] `dashboard.vue` layout made role-aware: sidebar profile card pulls real user from `useAuthStore()` instead of hardcoded "RND Ivy Hope Alba"; nav branches by role — RND keeps full nav, client gets a **minimal nav (Messages, Reviews, Log Out only)**. Logout now actually clears the auth store.
- [x] RND profile data (`GET /rnd/profile/`) fetched into `auth.rndProfile` after RND login and on hydrate — sidebar now shows real `specialization`/`prc_license_number`/`is_verified` instead of placeholder text. Verified live with a real verified RND account.
- [x] **`Appointments.vue` rewritten (2026-09-06)** — no longer mock-driven. Fetches `GET /client/appointments/` or `/rnd/appointments/` depending on role; client sees the RND's name + Cancel action, RND sees the client's name + Confirm/Decline (pending) or Mark Completed/Cancel (confirmed) + View NCP Record (completed). Wired to real transition endpoints (`.../confirm/`, `.../complete/`, `.../cancel/`), list re-fetches after each action, inline per-row error handling. Added back to client nav. Verified live end-to-end for both roles with a real relationship + 2 appointments fixture (pending→confirm/decline, confirmed→complete/cancel, client cancel) — all transitions worked correctly against the real DB. Test data cleaned up after.
- [x] **`ProfileSettings.vue` rewritten (2026-09-06)** — added a new backend endpoint (`GET/PATCH /client/profile/`, `MyClientProfileView` in `profiles/`, mirroring the existing `MyRndProfileView` pattern) since none existed for clients before. `ClientProfileSerializer` now nests `health_profile` (`source="user.health_profile"`). Frontend: tabs branch by role — client gets Personal Info/Health Info/Security (RND keeps Personal Info/Professional Profile/Languages/Fees & Payouts/Security); "PRC Verified" pill only shows for RND. Client's Personal Info tab is real (address/emergency contact, editable + saved via PATCH); Health Info tab shows real `ClientHealthProfile` data (medical conditions/allergies/dietary restrictions/health goals) as read-only — editing that is RND/clinical-workflow territory (screening, NCP records), not a self-service settings page. **Scope note:** editing first_name/last_name/email/phone on `User` itself isn't possible anywhere in the backend yet (`UserSerializer` is all read-only, `MeView` is GET-only) — Personal Info shows these as read-only for both roles rather than building fake-looking dead controls; a real fix is a separate task if needed later. Added back to client nav. Verified live for both roles incl. a real save round-trip (address/emergency contact persisted to DB, confirmed via direct query) — caught and fixed a real bug in the same pass: RND's `loadProfile()` returned early without clearing `isLoading`, leaving the panel stuck on "Loading…" forever for RND accounts.
- [ ] Toggle `USE_EMPTY_STATE` mock flag off page-by-page as each remaining component becomes wired to a real endpoint (most dashboard pages besides auth/layout/appointments/profile-settings still read from `mock/mockDatabase.js`)

## Phase 7 — Testing & polish
- [ ] pytest + pytest-django test suite for critical paths (auth, booking, payment webhook, NCP)
- [ ] Seed data (management command mirroring `DatabaseSeeder.php` — admin user, food exchange categories, system settings)
- [ ] CORS/env sanity check for deployed URLs
- [ ] Basic rate limiting on auth endpoints (DRF throttling)

## Phase 8 — Deployment
- [ ] Django: Railway/Render/Fly.io (or your school's requirement) + Postgres addon
- [ ] Nuxt: Vercel/Netlify, or same host as backend
- [ ] Environment variables for prod (PayMongo live keys, Daily.co)
- [ ] Retire/archive `backend/` (Laravel) once Django reaches parity — don't delete until demo is confirmed working

## Open questions to resolve early (ask your adviser / check the PDF)
- [ ] Does the capstone require a specific deployment target or grading rubric that assumes Laravel?
- [ ] Is real-time messaging (WebSocket) actually required, or is polling acceptable for MVP?
- [ ] Check `feature/kent-dashboard` branch (skipped for now) for any work not yet in `master` before it's forgotten
