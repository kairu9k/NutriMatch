# NutriMatch — Project Notes

Capstone project (STI College Davao, BSIT) — *NutriMatch: Web-Based Clinical Nutrition Consultation Management System*. Full proposal: `vault/C1-NUTRIMATCH-FINALv5.pdf`.

## What it is

Connects clients with licensed Registered Nutritionist-Dietitians (RNDs) in the Philippines for structured Medical Nutrition Therapy (MNT), built around the clinical **4-phase Nutrition Care Process (NCP)**: Assessment → Diagnosis (PES statement) → Intervention → Monitoring & Evaluation. This is a real standardized clinical methodology (Academy of Nutrition and Dietetics) — not an invented workflow, so don't restructure it without checking the proposal.

Three roles: **client**, **RND**, **admin**.

## Stack (current — deviates from the original proposal)

- **Frontend:** Nuxt 4 + Tailwind CSS + Lucide icons. Lives in `frontend/`.
- **Backend:** **Django 6.1.1 + DRF + SimpleJWT**, lives in `backend/`. The Laravel implementation was fully deleted (not kept as reference) — `vault/database.txt` (DBML schema) and `vault/C1-NUTRIMATCH-FINALv5.pdf` are now the authoritative references for porting domain logic, not PHP source. This is a deliberate stack change from the originally-proposed Laravel+MySQL — approved by the user, don't second-guess it or suggest reverting.
- Original proposal's documented stack was Laravel 11 + Nuxt.js 3.10 + MySQL 8 — no longer applicable, superseded.
- DB: SQLite for dev (`backend/db.sqlite3`), Postgres planned before deployment (not yet installed on the dev machine as of 2026-09-04).

## Folder map

- `frontend/` — **the real, active frontend repo**, cloned from the team's GitHub (`KPChiu7/NutriMatch-frontend`), currently on `master` (includes the merged `feature/landing-julia` PR). This is a separate git repo from the project root — don't assume root-level git commands apply here. Has its own `mock/mockDatabase.js` designed for a clean swap to real API calls later (see comments at top of that file).
- `backend/` — **Django project** (`nutrimatch_api/` settings module + 7 domain apps, all 21 tables from `vault/database.txt` modeled and migrated as of 2026-09-04). Has its own `.venv/` (Python 3.13, activate via `./.venv/Scripts/python.exe` on Windows — the `python`/`python3`/`py` aliases on this machine are inconsistent, always invoke the venv's own executable directly rather than relying on `activate`). `.env` holds local secrets (gitignored), `.env.example` is the template. App layout mirrors the schema's own 6 functional groups:
  - `accounts` — `User` (custom, role enum, email-based auth)
  - `profiles` — `RndProfile`, `RndLanguage`, `RndAvailabilitySchedule`, `ClientProfile`, `ClientHealthProfile`
  - `scheduling` — `RndClientRelationship`, `Appointment`, `ConsultationSession`, `Review`
  - `clinical` — `PreConsultationScreening`, `NcpRecord`, `ProgressRecord`
  - `nutrition` — `FoodExchangeCategory`, `FoodExchangeItem`, `MealPlan`, `MealPlanMeal`, `MealPlanFoodItem`
  - `communication` — `Message`, `Resource`, `Reminder`, `NotificationLog`
  - `billing` — `Invoice`, `PaymentTransaction`
  - `core` — `SystemSetting`, `ApiCache`, `AuditLog`
  - All 7 apps now have full `serializers.py`/`views.py`/`urls.py` as of Phase 3 (2026-09-04), mounted under `/api/`. Verified end-to-end via a scripted flow covering every core path.
  - `accounts`: auth (`/api/auth/*` — login, refresh, me, register/client, register/rnd) + admin user management (`/api/admin/users/*`)
  - `profiles`: RND search/detail (`/api/client/rnds/*`, only verified+accepting RNDs surfaced), RND self-profile (`/api/rnd/profile/`)
  - `scheduling`: relationship request/accept (`/api/client/rnds/<id>/request/`, `/api/rnd/relationship-requests/`, `/api/rnd/relationships/<id>/accept/` — this accept step was NOT in the original schema/proposal design, added because without it every relationship would be stuck at `pending` forever), client+RND appointment CRUD/status-transitions, reviews
  - `clinical`: pre-consultation screening (`/api/client/screening/*`) and NCP records (`/api/rnd/relationships/<id>/ncp/`, `/api/rnd/ncp/<id>/`, finalize). `clinical/services.py` holds the nutritional calculation engine (Mifflin-St Jeor BMR, TDEE, WHO Asia-Pacific BMI classification, NRS-2002 skeleton) — verified against hand-calculated values, do not modify these formulas without re-checking `vault/C1-NUTRIMATCH-FINALv5.pdf`. Age for BMR is derived live from `ClientProfile.date_of_birth`, not stored redundantly.
  - `nutrition`: food exchange categories/items (`/api/food-exchange/*`) — FNRI only, per the PH-only scope decision
  - `communication`: relationship-scoped messages (`/api/relationships/<id>/messages/*`)
  - `billing`: Phase 4 (done 2026-09-04) added `services.py` (`PayMongoService`), `views.py` (`InitiatePaymentView`, `PayMongoWebhookView`), `urls.py` (`/api/client/invoices/<id>/pay/`, `/api/webhooks/paymongo/` — the webhook route is `AllowAny`/no-JWT by design, PayMongo calls it unauthenticated and its own HMAC signature check is the real gate). No real PayMongo keys yet — `.env` values blank, service raises a clear config error if called without them. Verified via 13 passing tests with `httpx.Client` fully mocked (`billing/tests.py`, `billing/test_views.py`) — no live network calls made.
  - `scheduling` also gained `services.py` (`DailyCoVideoService`) in Phase 4 — wired into `RndAppointmentConfirmView`: confirming a video appointment auto-creates a `ConsultationSession` + Daily.co room. **Security invariant, test-verified**: `host_url` (grants RND/owner controls) must never appear in any client-facing serialized response — only `participant_url` (via `Appointment.video_session_url`) is client-visible. If you touch `ConsultationSessionSerializer` or add new appointment/session serializers, re-verify this doesn't regress.
  - `core`: models exist (Phase 1), no endpoints yet — `SystemSetting`/`ApiCache` not exposed via API; `AuditLog` is written to directly (e.g. `AuditLog.objects.create(...)` in the payment webhook handler) rather than through a dedicated service abstraction — revisit only if that repetition becomes a real problem.
  - **Known landmine class, already hit once**: Django `DecimalField(default=<float literal>)` (e.g. `default=10.00` or `default=1.0`) silently stores a Python `float` as the in-memory default until the first DB round-trip — `Decimal * float` then raises `TypeError` the first time that field is used in arithmetic before saving. Always write `Decimal("10.00")` instead. Fixed on `Invoice.commission_pct` and `MealPlanFoodItem.exchanges`; grep `DecimalField.*default=[0-9]*\.[0-9]` if adding new decimal fields with non-integer defaults.
  - Frontend's `LoginFlow.vue`/`RegisterFlow.vue` and all other components are NOT yet wired to these endpoints — they still just `console.log`/read from `mock/mockDatabase.js`. Backend is ready; frontend wiring is planned as part of Phase 6.
- `vault/` — project reference/documentation folder (renamed from `drive/`). Contains:
  - ~40 static Bootstrap 5 HTML mockups (design reference only, not live code). Useful as a visual/UX spec for screens not yet built in `frontend/`, but the actual frontend uses Tailwind, not Bootstrap — don't port Bootstrap markup directly, ports need re-authoring in Tailwind.
  - `vault/database.txt` — **authoritative DBML schema** (dbdiagram.io format), 21 tables across 6 functional groups, matches the proposal exactly. This is the primary reference for Django models — more precise than any prior source. Key rules encoded in it: `meal_plan_food_items` stores only `food_name` (plain text) from external FNRI/USDA lookups, never the nutrient payload (RA 10173 data minimization); `ncp_records` is one longitudinal row spanning all 4 NCP phases, not 4 tables; `invoices.commission_amt` freezes at creation, not recomputed; `sessions`/`migrations` tables are Laravel-internal and should NOT be ported to Django (Django has its own equivalents).
  - `vault/TODO.md` — phased migration/build plan, kept up to date as work progresses. Check this before planning new work.
  - `vault/C1-NUTRIMATCH-FINALv5.pdf` — the approved capstone proposal. Source of truth for clinical/domain requirements, scope, and compliance constraints.

## Domain constraints that matter for implementation

- **Calculations must match named clinical formulas** — Mifflin-St Jeor equation (BMR), TDEE derived from it, **WHO Asia-Pacific BMI thresholds** (not standard global WHO cutoffs), NRS-2002 nutritional risk scoring. These are specified in the proposal; don't substitute generic formulas.
- **Scope decision (2026-09-04): Philippine food data ONLY for now.** FNRI Food Exchange Lists is the sole food source to actually build/seed/query against. `FoodExchangeCategory`/`FoodExchangeItem` models and `MealPlanFoodItem.source_type` choices (`fel`/`fnri_fct`/`usda`/`custom`) keep `usda` as a schema option for future extensibility, but **do not build `UsdaFoodService`, USDA endpoints, or any USDA API integration** unless the user explicitly asks to revisit this. Don't propose USDA work proactively — this was a deliberate scope cut, not an oversight.
- **Data minimization still applies to whatever food source is active**: **only `food_name` (plain text) may be persisted from any external lookup — never store the full nutrient payload.** This is an explicit RA 10173 data-minimization design decision from the proposal, not an oversight — preserve it when building the FNRI integration.
- **NCP records are one longitudinal record with 4 phases**, not 4 separate tables — confirmed both in the proposal's data model and in `frontend/app/components/NCPRecords.vue`, which already implements it this way.
- **RA 10173 (Data Privacy Act) compliance is a first-class requirement**: audit logging (immutable `audit_logs` rows), RBAC, encryption in transit, informed consent. Explicitly out of scope per the proposal: formal NPC registration, end-to-end encryption, automated data retention schedules, granular consent revocation — don't add these unless asked.
- **Invoices/commission amounts freeze at creation** — don't let commission calculations recompute retroactively.

## Working conventions

- When updating the migration plan, edit `vault/TODO.md` rather than creating new planning docs.
- `frontend/` is a teammate-owned repo — check `git status`/`git log` before assuming changes are safe to push; confirm with the user before any push or force operation.
- Windows environment: use PowerShell for process management (`Stop-Process`, `Get-Process`) — Bash's process tools don't reliably see/kill native Windows processes (e.g. a stray `nuxt dev` server keeps running even after its spawning Bash task is reported stopped).
