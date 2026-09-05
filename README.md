# NutriMatch

**Web-Based Clinical Nutrition Consultation Management System**

Capstone project — STI College Davao, BSIT. Connects clients with licensed Registered Nutritionist-Dietitians (RNDs) in the Philippines for structured **Medical Nutrition Therapy (MNT)**, built around the clinical 4-phase **Nutrition Care Process (NCP)**: Assessment → Diagnosis (PES statement) → Intervention → Monitoring & Evaluation, per the Academy of Nutrition and Dietetics methodology.

Full capstone proposal: [`vault/C1-NUTRIMATCH-FINALv5.pdf`](vault/C1-NUTRIMATCH-FINALv5.pdf)

Three roles: **client**, **RND**, **admin**.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Nuxt 4, Tailwind CSS, Pinia, Lucide icons |
| Backend | Django 6.1.1, Django REST Framework, SimpleJWT |
| Database | SQLite (dev) → PostgreSQL (planned before deployment) |
| Payments | PayMongo (PH payment gateway) |
| Video consults | Daily.co |

> The original proposal specified Laravel 11 + Nuxt.js 3.10 + MySQL 8. The team moved to Django + Nuxt 4 — a deliberate stack change, not a deviation to walk back.

## Repo layout

```
NutriMatch/
├── frontend/   # Nuxt 4 app
├── backend/    # Django project + REST API
├── vault/      # Reference docs: DBML schema, capstone proposal PDF, build plan, static UI mockups
└── CLAUDE.md   # Working notes for AI-assisted development on this repo
```

## Getting started

### Prerequisites
- Node.js 20+ and npm
- Python 3.13+
- Git

### Backend setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in SECRET_KEY at minimum; payment/video keys can stay blank for local dev

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API is served at `http://localhost:8000/api/`. Django admin at `http://localhost:8000/admin/`.

### Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # NUXT_PUBLIC_API_BASE defaults to http://localhost:8000/api
npm run dev
```

App runs at `http://localhost:3000`.

Run both dev servers side by side (two terminals) for the frontend to actually reach the backend.

## Current status

Backend: auth, RND/client profiles, appointment scheduling, pre-consultation screening, NCP records, food exchange lookup (FNRI/Philippine data only), messaging, billing (PayMongo), and video session provisioning (Daily.co) are all built and API-mounted.

Frontend: wired so far — login/registration (both roles), the shared dashboard layout, appointments (booking lifecycle for both client and RND), and profile settings. Most other dashboard pages are still on mock data pending their turn, and several client-facing pages (RND search, booking flow, client home dashboard, etc.) haven't been built yet.

See [`vault/TODO.md`](vault/TODO.md) for the up-to-date phase-by-phase build plan — check it before starting new work.

## Domain notes worth knowing before you touch clinical code

- **BMR/TDEE/BMI/nutritional-risk calculations use named clinical formulas** (Mifflin-St Jeor, WHO Asia-Pacific BMI thresholds, NRS-2002) — don't substitute generic formulas without checking the proposal PDF.
- **NCP records are one longitudinal row spanning all 4 phases**, not four separate tables/records.
- **Philippine food data only, for now** — FNRI Food Exchange Lists is the sole food source built/seeded/queried. USDA integration is a deliberate, explicit scope cut, not an oversight — don't build it without checking first.
- **Data minimization (RA 10173)**: only `food_name` (plain text) is ever persisted from an external food lookup — never the full nutrient payload.
- **Invoice commission amounts freeze at creation** and are never recomputed retroactively.

`vault/database.txt` (DBML schema) is the authoritative reference for the data model — more precise than any other source, including this README.

## Branching & contribution workflow

- `main` is protected — nothing merges into it without a pull request and review.
- Create a feature branch off `main` for your work:
  ```bash
  git checkout main
  git pull
  git checkout -b feature/<short-description>
  ```
- Commit, push your branch, and open a PR into `main` when ready:
  ```bash
  git push -u origin feature/<short-description>
  ```
- Keep PRs scoped to one feature/fix where possible — makes review and testing faster.
- Don't commit `.env` files, `db.sqlite3`, `node_modules/`, or `.venv/` — all already gitignored, but double-check `git status` before staging if you're unsure.

## License

Academic capstone project — not licensed for external/commercial use.
