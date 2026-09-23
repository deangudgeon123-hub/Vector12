# Vector12

Vector12 is an early-stage clinical-trial eligibility matching platform.

**Eligibility criteria → executable rules → explainable shortlist**

Vector12 is decision-support software. It does not diagnose patients or make final clinical eligibility decisions.

## Current architecture

- API: Python + FastAPI
- Database: Supabase
- Backend hosting: Railway
- Source control: GitHub
- Frontend: planned Next.js/Vercel
- Eligibility compilation: OpenAI-assisted, strict-schema validated
- Patient matching: deterministic Python rules

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Run tests with:

```bash
python -m pytest -q
```

## Endpoints

- `GET /` — service identity
- `GET /health` — liveness check
- `GET /ready` — configuration readiness
- `GET /v1/eligibility/schema` — current eligibility compiler schema
- `POST /v1/eligibility/compile` — translate source eligibility text into validated rules

## Safety principle

Models may translate trial criteria into structured rules, but patient eligibility decisions are executed deterministically and remain reviewable by clinicians. Ambiguous criteria are routed to review rather than guessed.
