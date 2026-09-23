create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.trials (
  id uuid primary key default gen_random_uuid(),
  external_id text not null unique,
  title text not null,
  sponsor text,
  phase text,
  recruitment_status text,
  source_url text,
  raw_payload jsonb not null default '{}'::jsonb,
  source_fetched_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trials_set_updated_at
before update on public.trials
for each row execute function public.set_updated_at();

create table public.trial_rule_sets (
  id uuid primary key default gen_random_uuid(),
  trial_id uuid not null references public.trials(id) on delete cascade,
  version integer not null check (version > 0),
  schema_version text not null,
  compiler_provider text,
  compiler_model text,
  source_hash text not null,
  rules_hash text not null,
  status text not null default 'draft'
    check (status in ('draft', 'needs_review', 'approved', 'superseded')),
  compiled_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  approved_at timestamptz,
  unique (trial_id, version)
);

create index trial_rule_sets_trial_id_idx
  on public.trial_rule_sets(trial_id);

create table public.eligibility_criteria (
  id uuid primary key default gen_random_uuid(),
  rule_set_id uuid not null references public.trial_rule_sets(id) on delete cascade,
  criterion_key text not null,
  criterion_type text not null
    check (criterion_type in ('inclusion', 'exclusion')),
  source_text text not null,
  source_locator jsonb not null default '{}'::jsonb,
  executable_rule jsonb,
  review_state text not null default 'compiled'
    check (review_state in ('compiled', 'needs_review', 'approved', 'rejected')),
  created_at timestamptz not null default now(),
  unique (rule_set_id, criterion_key)
);

create index eligibility_criteria_rule_set_id_idx
  on public.eligibility_criteria(rule_set_id);

create table public.patients (
  id uuid primary key default gen_random_uuid(),
  pseudonym text not null unique,
  source_system text,
  source_patient_ref text,
  is_synthetic boolean not null default true,
  normalized_data jsonb not null default '{}'::jsonb,
  data_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger patients_set_updated_at
before update on public.patients
for each row execute function public.set_updated_at();

create table public.patient_facts (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null references public.patients(id) on delete cascade,
  fact_type text not null
    check (fact_type in (
      'demographic',
      'diagnosis',
      'lab',
      'biomarker',
      'medication',
      'procedure',
      'treatment',
      'performance_status',
      'other'
    )),
  code_system text,
  code text,
  display text,
  value_json jsonb not null default '{}'::jsonb,
  unit text,
  effective_start timestamptz,
  effective_end timestamptz,
  source_ref text,
  provenance jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index patient_facts_patient_id_idx
  on public.patient_facts(patient_id);

create index patient_facts_code_idx
  on public.patient_facts(code_system, code);

create table public.match_runs (
  id uuid primary key default gen_random_uuid(),
  trial_id uuid not null references public.trials(id) on delete restrict,
  rule_set_id uuid not null references public.trial_rule_sets(id) on delete restrict,
  matcher_version text not null,
  dataset_hash text not null,
  status text not null default 'queued'
    check (status in ('queued', 'running', 'complete', 'failed')),
  patient_count integer not null default 0 check (patient_count >= 0),
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

create index match_runs_trial_id_idx
  on public.match_runs(trial_id);

create index match_runs_rule_set_id_idx
  on public.match_runs(rule_set_id);

create table public.patient_matches (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.match_runs(id) on delete cascade,
  patient_id uuid not null references public.patients(id) on delete restrict,
  overall_status text not null
    check (overall_status in ('likely_eligible', 'likely_ineligible', 'needs_review')),
  hard_fail_count integer not null default 0 check (hard_fail_count >= 0),
  pass_count integer not null default 0 check (pass_count >= 0),
  unknown_count integer not null default 0 check (unknown_count >= 0),
  review_count integer not null default 0 check (review_count >= 0),
  rank_score numeric,
  summary jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (run_id, patient_id)
);

create index patient_matches_run_id_idx
  on public.patient_matches(run_id);

create index patient_matches_patient_id_idx
  on public.patient_matches(patient_id);

create table public.criterion_results (
  id uuid primary key default gen_random_uuid(),
  patient_match_id uuid not null references public.patient_matches(id) on delete cascade,
  criterion_id uuid not null references public.eligibility_criteria(id) on delete restrict,
  result text not null
    check (result in ('pass', 'fail', 'unknown', 'not_applicable', 'review')),
  explanation text not null,
  patient_fact_ids uuid[] not null default '{}',
  evidence jsonb not null default '{}'::jsonb,
  evaluated_at timestamptz not null default now(),
  unique (patient_match_id, criterion_id)
);

create index criterion_results_patient_match_id_idx
  on public.criterion_results(patient_match_id);

create table public.audit_events (
  id uuid primary key default gen_random_uuid(),
  actor_type text not null
    check (actor_type in ('system', 'user', 'service')),
  actor_id text,
  action text not null,
  entity_type text not null,
  entity_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index audit_events_entity_idx
  on public.audit_events(entity_type, entity_id);

alter table public.trials enable row level security;
alter table public.trial_rule_sets enable row level security;
alter table public.eligibility_criteria enable row level security;
alter table public.patients enable row level security;
alter table public.patient_facts enable row level security;
alter table public.match_runs enable row level security;
alter table public.patient_matches enable row level security;
alter table public.criterion_results enable row level security;
alter table public.audit_events enable row level security;
