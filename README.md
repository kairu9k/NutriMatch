# NutriMatch

**Web-Based Clinical Nutrition Consultation Management System**

Capstone project — STI College Davao, BSIT. Connects clients with licensed Registered Nutritionist-Dietitians (RNDs) in the Philippines for structured **Medical Nutrition Therapy (MNT)**, built around the clinical 4-phase **Nutrition Care Process (NCP)**.

- **Backend:** Django 6.1 + Django REST Framework (`backend/`)
- **Frontend:** Nuxt 4 + Tailwind CSS (`frontend/`)
- **Database:** SQLite for local development (a file, nothing to install)

---

## How to run it on your computer

You run **two programs side by side**: the backend (port 8000) and the frontend (port 3000). The steps below take about 10 minutes the first time.

### 1. Install these first

| Tool | Version | Check with |
|---|---|---|
| [Git](https://git-scm.com/downloads) | any | `git --version` |
| [Python](https://www.python.org/downloads/) | **3.13** (tick "Add Python to PATH" when installing) | `python --version` |
| [Node.js](https://nodejs.org/) | **20 or newer** (LTS) | `node --version` |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | optional — only for the Messages page | `docker --version` |

### 2. Get the code

```bash
git clone https://github.com/kairu9k/NutriMatch.git
cd NutriMatch
```

### 3. Start the backend (terminal #1)

**Windows (PowerShell):**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

**macOS / Linux:**

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

> Always run Python through `.venv` like above (not plain `python manage.py …`), so it uses the project's packages.

- `migrate` creates the database (`backend/db.sqlite3`).
- `seed` loads the **FNRI food exchange list** and default settings (reference data the meal planner needs — not demo data).
- `createsuperuser` makes the first **admin** (asks for an email and a password). There is no demo data: create clients and RNDs by registering in the app — see [Accounts](#accounts).
- Leave this terminal open. It should say `Watching for file changes…` with no red error — the backend is now at `http://localhost:8000`. Each request your browser makes shows up here as a line.

### 4. Start the frontend (terminal #2)

```bash
cd frontend
npm install
```

Then create the frontend's `.env` file:

- Windows: `copy .env.example .env`
- macOS / Linux: `cp .env.example .env`

```bash
npm run dev
```

Open **http://localhost:3000** in your browser. Use `localhost`, not `127.0.0.1` — the backend only accepts requests from those exact addresses.

### 5. (Optional) Reminders on a schedule

Reminders (consultations, payments, meal logging, RND reminders) are also sent whenever a client opens the app, so nothing extra is needed to test them. To send them on a timer like a real server would, run in a third terminal:

```bash
.\.venv\Scripts\python.exe manage.py send_reminders --loop 300     # Windows — every 5 minutes
.venv/bin/python manage.py send_reminders --loop 300               # macOS / Linux
```

### 6. (Optional) Real-time messages — Redis

The **Messages** page needs Redis. Everything else works without it. With Docker Desktop running:

```bash
docker run -d --name nutrimatch-redis -p 6379:6379 --restart unless-stopped redis:7-alpine
```

Run it once; afterwards it starts automatically with Docker. If Messages says it can't connect, open Docker Desktop.

---

## Accounts

There is **no demo data** (removed 2026-10-19 at the adviser's request). Use real accounts:

- **Admin** — the one from `createsuperuser`, signing in at **http://localhost:3000/admin/login**. More admins: Users → **Add admin**.
- **Client** — Register at http://localhost:3000/register as a patient, verify the 6-digit code, go through onboarding.
- **RND** — Register as an RND (needs Cloudinary keys for the PRC photo), verify the code, then **approve the application as the admin** (RND Applications) — only then can the RND sign in.

Clients and RNDs sign in at **http://localhost:3000/login**. Never write real passwords in the repo.

---

## What works without any keys

You don't need any passwords or API keys to test most of the app. The `.env` you copied leaves them blank:

| Feature | Without keys | To make it fully work |
|---|---|---|
| Sign-up emails (verification code, password reset) | Nothing is sent — **the email, including the 6-digit code, is printed in the backend terminal (#1)**. Copy the code from there. | Gmail App Password in `GMAIL_HOST_USER` / `GMAIL_HOST_PASSWORD` |
| Registering a **new RND** (PRC license photo) and **profile photos** | Shows "Cloudinary is not configured". | Cloudinary keys in `CLOUDINARY_*` (ask the team lead — never commit them) |
| **Paying** an invoice (PayMongo) | Paying shows "PAYMONGO_SECRET_KEY is not configured." | PayMongo **test** keys in `PAYMONGO_SECRET_KEY` |
| Messages (real-time chat) | Can't send | Redis — [step 6](#6-optional-real-time-messages--redis) |
| Video consultation | Works (free Jitsi, no key) | — |

Registering a new **client** works without any keys — grab the verification code from the backend terminal.

---

## Things to try

**As a client** (register one): onboarding + pre-consultation screening → Find an RND → book → pay (PayMongo test keys) → My Meal Plan → log a meal → Progress Tracker.

**As an RND** (register one, approve it as admin): Dashboard → Appointments (confirm the booking) → My Patients → NCP Records → Meal Planning → Profile Settings → **Earnings**.

**As the admin** (at `/admin/login`): Dashboard to-do → **RND Applications** → Users → Appointments → Billing & Commission → Payouts → Audit Logs (filters, Export CSV). System Settings is in the account menu (bottom of the sidebar).

Found a bug? Note the account you used, the page, and what you clicked, and send a screenshot.

---

## Testing on your phone

Your phone and laptop must be on the same Wi-Fi — or connect the laptop to your phone's hotspot.

1. Find the laptop's IP address: Windows `ipconfig` (IPv4 Address, e.g. `192.168.1.23`); macOS `ipconfig getifaddr en0`.
2. In `backend/.env`, add that address (keep the existing ones):
   ```
   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.23
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.23:3000
   ```
3. In `frontend/.env`: `NUXT_PUBLIC_API_BASE=http://192.168.1.23:8000/api`
4. Start the backend with `manage.py runserver 0.0.0.0:8000` and the frontend with `npm run dev -- --host`.
5. On the phone, open `http://192.168.1.23:3000`.

If the phone says "site can't be reached", Windows Firewall is blocking it — allow Python and Node when Windows asks, or use the phone-hotspot option. Undo steps 2–3 when you're done.

---

## After you pull new changes

New code can add packages or database changes. After every `git pull`:

```bash
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # (macOS: .venv/bin/python …)
.\.venv\Scripts\python.exe manage.py migrate
cd ../frontend
npm install
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Incorrect email or password" | Use **Forgot password** (the code is emailed, or printed in terminal #1 without Gmail keys). For an admin you can also run `manage.py changepassword <email>`. |
| Pages load but say "Could not load…" | The backend (terminal #1) isn't running, or stopped with an error — check that terminal. |
| `Error: That port is already in use` | Another backend is still running. Close it, or on Windows: `Get-Process python \| Stop-Process` in PowerShell. |
| Frontend not on port 3000 (e.g. 3001) | Another `npm run dev` is still running, and the backend only accepts port 3000. Close the other one and start again. |
| `no such table` / `no such column` errors | You skipped `migrate` after pulling — run it. |
| `ModuleNotFoundError` | Run Python through `.venv` (step 3) and re-run `pip install -r requirements.txt`. |
| Messages won't send | Redis isn't running — open Docker Desktop ([step 6](#6-optional-real-time-messages--redis)). |

## Running the automated tests

```bash
cd backend
.\.venv\Scripts\python.exe manage.py test accounts billing core profiles scheduling clinical nutrition
```

(`communication` has 3 extra tests that need Redis running.)

---

## Branching & contribution workflow

- `main` is protected — nothing merges in without a pull request and review.
- Branch off `main` for your work:
  ```bash
  git checkout main
  git pull
  git checkout -b feature/<short-description>
  ```
- Push and open a PR into `main` when ready:
  ```bash
  git push -u origin feature/<short-description>
  ```
- Keep PRs scoped to one feature/fix at a time.
- Never commit `.env` files, `db.sqlite3` or anyone's passwords/keys — they're already in `.gitignore`.
