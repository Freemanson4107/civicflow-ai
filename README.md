# CivicFlow AI — Public Service Navigation Platform

AI-powered guidance for healthcare, benefits, and government services across
**India, USA, and Brazil**.

---

## What's actually working right now

| USP | Status | How |
|---|---|---|
| 1. Life Event Detection | ✅ Working | TF-IDF + Logistic Regression, trained on 560 synthetic examples across 7 categories. 100% accuracy on held-out rows from the *same* generator (synthetic data is clean — expect lower on messy real input; swap-in path to DistilBERT documented below). |
| 2. Benefit Matching Engine | ✅ Working — hybrid by design | **Eligibility is decided by deterministic rules only** (exact age range, income cap, employment match, family-size minimum from each program's published criteria) — no model ever decides pass/fail. **Among benefits a citizen already qualifies for**, a trained GradientBoostingRegressor (`benefit_priority_model.joblib`, R²=0.97 on synthetic priority labels — see caveat below) ranks them by income-need depth, life-event category match, and family size. This mirrors how real eligibility-screening tools split the problem: rules gate, ML ranks. |
| 3. Queue Forecasting | ✅ Working | RandomForest (wait-time, MAE 6.3 min) + GradientBoosting (crowd-level, 81% accuracy) trained on synthetic queue records across 12 offices. |
| 4. Document Readiness | ✅ Working — with a disclosed limitation | Tesseract OCR + a trained TF-IDF/LogisticRegression classifier (`document_type_model.joblib`) replacing the old keyword matcher. On genuinely novel phrasing (not seen during training) it correctly identifies **7/10** held-out test sentences — real generalization, not perfect. Most misses are between near-duplicate label pairs in the taxonomy itself (e.g. "Income Proof" vs "Last Pay Stubs" are the same real-world document under two names — see `data/generate_document_ocr.py` docstring). Confidence is returned alongside every prediction so low-confidence guesses can be surfaced as "unknown" rather than asserted. |
| 5. Journey Optimizer | ✅ Working — genuinely model-composed | No model of its own (by design — visit-time/document-order logic should stay deterministic, not probabilistic). It calls the **trained queue model** to scan an office's next two weeks of hours and recommend the actual lowest-predicted-wait slot (replacing a previous hardcoded "Tue/Wed 9-10am" claim that wasn't derived from anything), and accepts the **life-event model's** category + confidence to flag time-sensitive cases. Both upstream model outputs are echoed in the response payload (`queue_forecast`, `life_event_signal`) so the composition is demonstrable, not just asserted in prose. |
| Map visualization | ✅ Working | Leaflet map, color-coded by live crowd-level prediction. |
| Auth | ✅ Working, hardened | See Security section below. |

## What's intentionally simplified (and why) — be upfront about this when presenting

- **Synthetic data, not real government data.** I generated realistic synthetic
  datasets for all 5 AI systems (life events, benefits, queue history, offices)
  so the whole pipeline runs end-to-end. Swap in real datasets without
  changing any code — just match the CSV/JSON schemas in `/data`.
- **DistilBERT/MiniLM → TF-IDF+LogReg.** The brief suggested transformer
  models; this build uses a lightweight sklearn classifier instead because
  it trains in under a second with no GPU/internet and is a drop-in
  `predict_proba()` interface. To upgrade: replace the pipeline in
  `data/train_life_event_model.py` with a `sentence-transformers` embedding
  + classifier head, save with the same `.joblib` interface, and
  `app/routers/life_event.py` doesn't need to change.
- **XGBoost/LightGBM → RandomForest/GradientBoosting** for the same
  no-internet reason. Both are explicitly listed as acceptable in the
  original spec. Swapping to `xgboost.XGBRegressor`/`XGBClassifier` is a
  one-line import change in `data/train_queue_model.py`.
- **Auth.js/Clerk → custom JWT auth.** Built fully custom (see Security
  below) so it's self-contained and doesn't depend on a third-party
  service's API keys for the demo. Swapping to Clerk/Auth.js later is
  straightforward since the frontend already isolates all auth calls in
  `lib/api.ts`.
- **Benefit Priority Model's training labels are a domain heuristic, not real
  casework outcomes.** No public dataset of "which eligible applicants
  actually needed a benefit most urgently" exists for a civic demo. The
  label formula (income depth + category match + family size + noise) is
  disclosed in full in `data/generate_benefit_priority.py`. The model is
  real and trained — it generalizes a multi-factor scoring function instead
  of hardcoding one — but the *ground truth* it learned from is a designed
  proxy, not observed reality. Swap in real intake-outcome data later
  without changing `app/routers/benefits.py` — just match the feature
  columns in the training CSV.
- **Document Type Classifier's test accuracy on its own train/test split
  looks like 100%, which is misleading on its own.** That number reflects
  held-out *rows from the same synthetic generator*, which share template
  phrasing with the training rows. On a small hand-written set of novel
  phrasings *not* in the generator, it gets 7/10 right — a more honest
  number, included here instead of hidden. See the model's row in the
  feature table above for what the misses actually are.

---

## Security (you asked for this to be strong — here's what's implemented)

- **Password hashing:** bcrypt, cost factor 12, via `passlib`. Plaintext
  passwords are never stored or logged.
- **Server-side password policy:** min 10 chars, upper+lower+digit+symbol —
  enforced in the backend (`core/security.py::password_meets_policy`),
  regardless of what the frontend does.
- **JWT access tokens:** short-lived (15 min), HS256-signed, carry a unique
  `jti` per token.
- **Refresh tokens:** 7-day expiry, stored **hashed** (SHA-256) in the
  database — the raw token is never persisted. Rotated on every use: each
  refresh invalidates the previous token, mitigating replay of a stolen
  refresh token.
- **Account lockout:** 5 failed login attempts locks the account for 15
  minutes — mitigates brute-force / credential-stuffing.
- **Enumeration protection:** signup and login return generic error
  messages that don't reveal whether an email already exists.
- **Rate limiting:** `slowapi` on auth endpoints (5 req/min on login) and a
  global default limit.
- **Security headers:** `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`, and HSTS in production —
  applied via middleware in `app/main.py`.
- **CORS locked down** to explicit allowed origins (no wildcard `*`).
- **No stack traces leaked:** a generic exception handler returns a flat
  500 message to clients; real errors only go to server logs.
- **Token storage on frontend:** access token kept in memory only (never
  `localStorage`, to reduce XSS token-theft surface); refresh token in
  `sessionStorage` as a pragmatic demo choice — **for a real production
  deploy, change this to an httpOnly Secure cookie set by the backend.**
  This is flagged in `lib/api.ts`.

**Before going to production, also do:** rotate `SECRET_KEY` out of `.env`
into a secrets manager, add email verification on signup, add 2FA, and run
this through a dependency vulnerability scan (`pip-audit` / `npm audit`).

---

## Quickstart (local)

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# generate a real secret:
python3 -c "import secrets; print(secrets.token_hex(32))"
# paste it into .env as SECRET_KEY
uvicorn app.main:app --reload
# API docs: http://localhost:8000/api/docs
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
# http://localhost:3000
```

### Regenerate datasets / retrain models (optional — already pre-trained in repo)
```bash
cd data
python3 generate_life_events.py
python3 generate_benefits.py
python3 generate_queue_and_offices.py
python3 generate_benefit_priority.py
python3 generate_document_ocr.py
python3 train_life_event_model.py
python3 train_queue_model.py
python3 train_benefit_priority_model.py
python3 train_document_type_model.py
```

---

## Deploying live (for your submission)

**Frontend → Vercel**
1. Push this repo to GitHub.
2. Import the `frontend/` folder as a project in Vercel.
3. Set env var `NEXT_PUBLIC_API_URL` to your deployed backend URL.
4. Deploy — Vercel auto-detects Next.js (`vercel.json` included).

**Backend → Render**
1. New Web Service on Render, point at `backend/`, it'll pick up `render.yaml`.
   This service deploys via **Docker** (see `backend/Dockerfile`), not Render's
   native Python runtime — the Document Readiness feature needs the real
   `tesseract-ocr` system binary, which `pip install` alone can't provide.
   Docker lets the build `apt-get install tesseract-ocr` so the binary
   actually exists in production, not just locally.
2. Render auto-generates `SECRET_KEY` and provisions a free Postgres DB
   (`DATABASE_URL` wired automatically).
3. Update `ALLOWED_ORIGINS` to your real Vercel URL once you have it.
4. Update `NEXT_PUBLIC_API_URL` on Vercel to point at the Render URL, redeploy frontend.

Both have free tiers, so this is deployable with zero budget before your
June 21 deadline.

---

## Folder structure
```
civicflow-ai/
├── data/                     # dataset generators + model training scripts
├── backend/
│   ├── app/
│   │   ├── core/             # config, security, db, auth deps, queue_predictor (shared model logic)
│   │   ├── models/           # ORM models + Pydantic schemas
│   │   ├── routers/          # auth, profile, life-event, benefits, queue, offices, documents, journey
│   │   ├── ml/                # trained .joblib models + data JSON the API loads
│   │   └── main.py
│   └── requirements.txt
└── frontend/
    ├── app/                  # landing, login, signup, dashboard (Next.js App Router)
    ├── components/           # ServiceMap (Leaflet)
    └── lib/api.ts             # auth + API client
```

## Demo script (for judges)
1. Land on homepage → show the "route to support" hero element.
2. Sign up as a USA-region user.
3. On dashboard, type: *"I lost my job and have two kids."*
4. Show life-event detection firing → confidence score.
5. Show ranked benefit matches (these are all benefits the user already
   qualifies for — eligibility was decided by hard rules — ranked by a
   trained priority model), click one → show a roadmap that pulls a real
   model-recommended visit time from the queue forecaster, plus the
   document checklist.
6. Scroll to live map → point out green/amber/red crowd levels driven by
   the queue-forecasting model.
7. Mention: same flow works unchanged for India/Brazil — flip the region
   at signup.

## Pitch deck one-liner
*"Google Maps got you from A to B. CivicFlow AI gets you from 'I don't know
where to start' to 'I'm approved' — across any public service, in any
country."*
