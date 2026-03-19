create extension if not exists pgcrypto;

create table if not exists public.lead_metrics (
    id uuid primary key default gen_random_uuid(),
    nome text not null,
    email text not null,
    mensagem text not null,
    intent text not null check (intent in ('vendas', 'suporte', 'spam')),
    sentiment text not null check (sentiment in ('positivo', 'neutro', 'negativo')),
    fallback boolean not null default false,
    created_at timestamptz not null default timezone('utc', now())
);

alter table public.lead_metrics enable row level security;

grant usage on schema public to service_role;
grant select, insert, update, delete on table public.lead_metrics to service_role;
