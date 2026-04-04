create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  avatar_url text,
  is_admin boolean not null default false,
  reports_submitted integer not null default 0,
  reports_resolved integer not null default 0,
  created_at timestamp not null default now()
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, display_name, avatar_url)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name'),
    new.raw_user_meta_data ->> 'avatar_url'
  )
  on conflict (id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  photo_url text not null,
  lat double precision not null,
  lng double precision not null,
  hazard_type text,
  severity text,
  department text,
  summary text,
  complaint text,
  confidence text,
  resources jsonb,
  area text,
  area_name text,
  location text,
  location_name text,
  address text,
  upvotes integer not null default 0,
  status text not null default 'open',
  created_at timestamp not null default now(),
  resolved_at timestamp,
  constraint reports_hazard_type_check check (
    hazard_type is null or hazard_type in (
      'illegal_dumping',
      'oil_spill',
      'e_waste',
      'water_pollution',
      'blocked_drain',
      'air_pollution',
      'other'
    )
  ),
  constraint reports_severity_check check (
    severity is null or severity in ('high', 'medium', 'low')
  ),
  constraint reports_department_check check (
    department is null or department in (
      'Municipal Sanitation',
      'EPA',
      'Public Works',
      'Parks Department',
      'Drainage Authority'
    )
  ),
  constraint reports_status_check check (
    status in ('open', 'in_review', 'escalated', 'resolved')
  ),
  constraint reports_confidence_check check (
    confidence is null or confidence in ('high', 'low')
  )
);

create index if not exists idx_reports_created_at on public.reports(created_at desc);
create index if not exists idx_reports_status on public.reports(status);
create index if not exists idx_reports_severity on public.reports(severity);
create index if not exists idx_reports_hazard_type on public.reports(hazard_type);
create index if not exists idx_reports_user_id on public.reports(user_id);
create index if not exists idx_reports_area_name on public.reports(area_name);

create table if not exists public.upvotes (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.reports(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  created_at timestamp not null default now(),
  unique (report_id, user_id)
);

create index if not exists idx_upvotes_report_id on public.upvotes(report_id);
create index if not exists idx_upvotes_user_id on public.upvotes(user_id);

create table if not exists public.user_badges (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  badge_id text not null,
  earned_at timestamp not null default now(),
  unique (user_id, badge_id)
);

create index if not exists idx_user_badges_user_id on public.user_badges(user_id);

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
  distance_m float,
  distance_km text
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
    ) as distance_m,
    to_char(
      round(
        (6371000 * acos(
          cos(radians(lat)) * cos(radians(r.lat)) * cos(radians(r.lng) - radians(lng)) +
          sin(radians(lat)) * sin(radians(r.lat))
        )) / 1000.0,
        1
      ),
      'FM999990.0'
    ) || ' km' as distance_km
  from public.reports r
  where 6371000 * acos(
      cos(radians(lat)) * cos(radians(r.lat)) * cos(radians(r.lng) - radians(lng)) +
      sin(radians(lat)) * sin(radians(r.lat))
    ) <= radius_m
  order by distance_m asc;
$$;
