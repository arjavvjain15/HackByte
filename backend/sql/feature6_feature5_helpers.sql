-- Feature 6 + Nearby optimization helpers

create table if not exists public.upvotes (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.reports(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  created_at timestamp default now(),
  unique (report_id, user_id)
);

create index if not exists idx_upvotes_report_id on public.upvotes(report_id);
create index if not exists idx_upvotes_user_id on public.upvotes(user_id);

create or replace function public.nearby_reports(lat float, lng float, radius_m int)
returns table (
  id uuid,
  lat float,
  lng float,
  hazard_type text,
  severity text,
  upvotes int,
  status text,
  created_at timestamp,
  distance_m float
)
language sql
as $$
  select
    r.id,
    r.lat,
    r.lng,
    r.hazard_type,
    r.severity,
    r.upvotes,
    r.status,
    r.created_at,
    6371000 * acos(
      cos(radians(lat)) * cos(radians(r.lat)) * cos(radians(r.lng) - radians(lng)) +
      sin(radians(lat)) * sin(radians(r.lat))
    ) as distance_m
  from public.reports r
  where 6371000 * acos(
      cos(radians(lat)) * cos(radians(r.lat)) * cos(radians(r.lng) - radians(lng)) +
      sin(radians(lat)) * sin(radians(r.lat))
    ) <= radius_m
  order by distance_m asc;
$$;
