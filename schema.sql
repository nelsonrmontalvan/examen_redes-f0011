-- ============================================================
-- IF0011 Redes de Computadoras · Examen I (práctica)
-- Registro de intentos de los estudiantes
--
-- CÓMO USAR:
--   1) Cree su proyecto en https://supabase.com (plan Free)
--   2) Vaya a SQL Editor, pegue TODO este archivo y ejecute
--   3) Reemplace 'TU_CORREO_UCR' por su correo UCR (abajo)
--   4) Cree su usuario profesor: Authentication > Users > Add user
--      (use exactamente el mismo correo de abajo)
--   5) Copie URL + anon key en config.js
-- ============================================================

-- ---------- Tabla de intentos ----------
create table if not exists public.intentos (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  nombre text not null,
  carnet text not null,
  grupo text,
  pts_teoria integer not null check (pts_teoria between 0 and 50),
  pts_subnet integer not null check (pts_subnet between 0 and 10),
  pts_practicos integer not null check (pts_practicos between 0 and 40),
  pts_total integer not null check (pts_total between 0 and 100)
);

create index if not exists idx_intentos_carnet on public.intentos (carnet);
create index if not exists idx_intentos_created on public.intentos (created_at desc);

-- ---------- Seguridad (RLS) ----------
alter table public.intentos enable row level security;

-- Los estudiantes (anónimos) SOLO pueden INSERTAR un intento.
-- No pueden ver NADA de nadie.
drop policy if exists "estudiantes insertan intento" on public.intentos;
create policy "estudiantes insertan intento"
  on public.intentos
  for insert
  with check (true);

-- Solo el PROFESOR autenticado puede LEER los intentos.
-- >>> REEMPLACE TU_CORREO_UCR por su correo institucional <<<
drop policy if exists "profesor lee intentos" on public.intentos;
create policy "profesor lee intentos"
  on public.intentos
  for select
  to authenticated
  using (auth.jwt() ->> 'email' = 'TU_CORREO_UCR');

-- Por seguridad: nadie puede actualizar ni borrar registros desde la app.
revoke update, delete on public.intentos from anon, authenticated;