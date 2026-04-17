-- Supabase/Postgres additions for Argo float data
-- This script is written to be safe to run on an existing Supabase project.
-- It enables required extensions and adds spatial + indexing capabilities.

-- Extensions (Supabase allows these in SQL editor / migrations)
create extension if not exists vector;
create extension if not exists postgis;

-- Spatial columns (PostGIS)
alter table public.profiles add column if not exists location geography(point, 4326);
alter table public.measurements add column if not exists location geography(point, 4326);

-- Keep `location` synced with lat/lon.
create or replace function public._argo_set_location_from_latlon()
returns trigger
language plpgsql
as $$
begin
  if new.longitude is null or new.latitude is null then
    new.location := null;
  else
    new.location := st_setsrid(st_makepoint(new.longitude, new.latitude), 4326)::geography;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_profiles_set_location on public.profiles;
create trigger trg_profiles_set_location
before insert or update of longitude, latitude
on public.profiles
for each row
execute function public._argo_set_location_from_latlon();

drop trigger if exists trg_measurements_set_location on public.measurements;
create trigger trg_measurements_set_location
before insert or update of longitude, latitude
on public.measurements
for each row
execute function public._argo_set_location_from_latlon();

create table if not exists public.feature_catalogs (
  id bigserial primary key,
  category text,
  feature_name text,
  description text,
  units text,
  data_type text,
  sensor_type text,
  mathematical_deps jsonb,
  graphical_reps jsonb,
  unique (category, feature_name)
);

-- Indexes (time + spatial + basic filters)
create index if not exists idx_floats_wmo on public.floats(wmo_id);
create index if not exists idx_profiles_wmo on public.profiles(wmo_id);
create index if not exists idx_profiles_time on public.profiles(profile_time);
create index if not exists idx_profiles_location on public.profiles using gist (location);
create index if not exists idx_measurements_wmo on public.measurements(wmo_id);
create index if not exists idx_measurements_profile on public.measurements(profile_id);
create index if not exists idx_measurements_feature on public.measurements(feature_type);
create index if not exists idx_measurements_time on public.measurements(measurement_time);
create index if not exists idx_measurements_location on public.measurements using gist (location);

-- Vector indexes for similarity search (IVFFlat)
-- Note: ivfflat requires enough rows for best performance; safe to create regardless.
create index if not exists idx_floats_embedding on public.floats using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index if not exists idx_profiles_embedding on public.profiles using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index if not exists idx_measurements_embedding on public.measurements using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Optional: prevent duplicate level inserts per profile
create unique index if not exists uq_measurements_profile_pressure on public.measurements(profile_id, pressure);

