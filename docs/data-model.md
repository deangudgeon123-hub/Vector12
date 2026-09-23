# Data model

Vector12 keeps trial logic, patient facts, match outputs, and audit history separate so every decision can be explained and reproduced.

## Core entities

- `trials`: source trial metadata and raw imported payload.
- `trial_rule_sets`: immutable, versioned compiled eligibility rule sets.
- `eligibility_criteria`: one source criterion plus its executable representation and provenance.
- `patients`: pseudonymized patient records. V1 is designed for synthetic/public data.
- `patient_facts`: normalized facts with coding, units, dates, source references, and provenance.
- `match_runs`: one deterministic matcher execution against an approved rule set.
- `patient_matches`: patient-level outcome for a run.
- `criterion_results`: criterion-by-criterion PASS/FAIL/UNKNOWN/NOT_APPLICABLE/REVIEW evidence.
- `audit_events`: append-style operational audit trail.

## Safety constraints

The schema does not require direct identifiers such as names, addresses, NHS numbers, emails, or phone numbers. Production handling of identifiable clinical data will require a separately approved information-governance and deployment design.

All V1 tables have Row Level Security enabled. No client-side access policies are created yet, so access remains default-deny until authentication and tenancy are deliberately designed.
