-- Run this once in the Supabase SQL Editor (Dashboard -> SQL Editor -> New query -> paste -> Run)

create table if not exists creators (
  discord_id text primary key,
  username text,
  niche text,
  platforms text,
  handles text,
  audience_size text,
  goal text,
  experience text,
  status text default 'onboarding',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists sales (
  id bigint generated always as identity primary key,
  discord_id text,
  handle text,
  amount numeric default 0,
  period text,
  updated_at timestamptz default now()
);
