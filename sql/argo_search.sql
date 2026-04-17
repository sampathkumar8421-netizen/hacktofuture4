-- pgvector-powered semantic search RPCs (Supabase-friendly)

create or replace function public.match_floats(
  query_embedding vector(768),
  match_count int default 10
)
returns table (
  wmo_id int,
  platform_type text,
  total_profiles int,
  start_date timestamptz,
  end_date timestamptz,
  start_lat double precision,
  end_lat double precision,
  start_lon double precision,
  end_lon double precision,
  similarity double precision
)
language sql
stable
as $$
  select
    f.wmo_id,
    f.platform_type,
    f.total_profiles,
    f.start_date,
    f.end_date,
    f.start_lat,
    f.end_lat,
    f.start_lon,
    f.end_lon,
    1 - (f.embedding <=> query_embedding) as similarity
  from public.floats f
  where f.embedding is not null
  order by f.embedding <=> query_embedding
  limit match_count;
$$;

create or replace function public.match_profiles(
  query_embedding vector(768),
  match_count int default 10,
  filter_wmo_id int default null
)
returns table (
  profile_id bigint,
  wmo_id int,
  cycle_number int,
  profile_time timestamptz,
  latitude double precision,
  longitude double precision,
  similarity double precision
)
language sql
stable
as $$
  select
    p.id as profile_id,
    p.wmo_id,
    p.cycle_number,
    p.profile_time,
    p.latitude,
    p.longitude,
    1 - (p.embedding <=> query_embedding) as similarity
  from public.profiles p
  where p.embedding is not null
    and (filter_wmo_id is null or p.wmo_id = filter_wmo_id)
  order by p.embedding <=> query_embedding
  limit match_count;
$$;

