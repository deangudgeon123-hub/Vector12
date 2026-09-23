alter function public.set_updated_at() set search_path = public, pg_temp;

create index if not exists criterion_results_criterion_id_idx
  on public.criterion_results(criterion_id);
