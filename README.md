# Vector12

Vector12 is an early-stage clinical-trial eligibility matching platform.

The product goal is:

**Eligibility criteria → executable rules → explainable shortlist**

Vector12 is decision-support software. It does not diagnose patients or make final clinical eligibility decisions.

## Current architecture

- **API:** Python + FastAPI
- **Database:** Supabase
- **Backend hosting:** Railway
- **Source control:** GitHub
- **Frontend:** planned Next.js/Vercel
- **Eligibility compilation:** model-assisted, schema-validated
- **Patient matching:** deterministic Python rules

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest -q
```

## Endpoints

- `GET /` — service identity
- `GET /health` — liveness check
- `GET /ready` — configuration readiness check

## Safety principle

Models may help translate trial criteria into structured rules, but patient eligibility decisions are executed deterministically and remain reviewable by clinicians.
