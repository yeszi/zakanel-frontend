-- =====================================================================
-- Migrasi: RBAC + JWT + Audit Log (tamper-evident)
-- Jalankan sekali di Supabase: Dashboard > SQL Editor > New query > Run
-- Aman dijalankan ulang (memakai IF NOT EXISTS).
-- =====================================================================

-- 1) Kolom status akun (dipakai untuk menolak penerbit yang dicabut)
alter table public.users add column if not exists status text not null default 'active';
alter table public.users add column if not exists is_active boolean not null default true;

-- 2) Kolom kepemilikan & status pada batch (sesuai rancangan Bab III)
alter table public.batch_sertifikat add column if not exists penerbit_id bigint references public.users(id);
alter table public.batch_sertifikat add column if not exists status text default 'pending';
alter table public.batch_sertifikat add column if not exists tx_hash text;

-- 3) Tabel audit log
create table if not exists public.audit_logs (
    id              bigserial primary key,
    logged_at       text        not null,            -- waktu ISO-8601 (TEXT agar ikut di-hash persis)
    created_at      timestamptz not null default now(),
    actor_id        bigint,                          -- null untuk publik / login gagal
    actor_username  text,
    actor_role      text,                            -- admin | penerbit | publik
    action          text        not null,            -- LOGIN_SUCCESS, PENERBIT_ADD, CERT_PUBLISH, CERT_VERIFY, ...
    target_type     text,
    target_id       text,
    detail          text        not null default '{}', -- JSON kanonik (TEXT agar hash bisa dihitung ulang)
    tx_hash         text,
    ip_address      text,
    status          text        not null default 'success', -- success | failed | denied
    prev_hash       char(64)    not null,
    entry_hash      char(64)    not null unique
);
create index if not exists audit_logs_action_idx on public.audit_logs (action);
create index if not exists audit_logs_actor_idx  on public.audit_logs (actor_id);
create index if not exists audit_logs_created_idx on public.audit_logs (created_at desc);

-- 4) Audit log bersifat APPEND-ONLY: tolak UPDATE dan DELETE di level database
create or replace function public.audit_logs_block_change()
returns trigger language plpgsql as $$
begin
    raise exception 'audit_logs bersifat append-only: % tidak diizinkan', tg_op;
end;
$$;

drop trigger if exists audit_logs_no_update on public.audit_logs;
create trigger audit_logs_no_update before update or delete on public.audit_logs
    for each row execute function public.audit_logs_block_change();

-- 5) Aktifkan Row Level Security. Backend memakai service_role key sehingga tetap bisa
--    INSERT/SELECT; anon key dari browser tidak bisa membaca/menulis tabel-tabel ini.
alter table public.audit_logs enable row level security;
alter table public.users enable row level security;
alter table public.batch_sertifikat enable row level security;
alter table public.sertifikat enable row level security;
