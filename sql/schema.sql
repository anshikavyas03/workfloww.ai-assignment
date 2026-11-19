-- Run this in the Supabase SQL Editor. Each app user also needs an auth.users row.
create table public.companies (
  id uuid primary key default gen_random_uuid(),
  name text not null unique check (char_length(name) between 1 and 120),
  created_at timestamptz not null default now()
);

create table public.users (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid not null unique references auth.users(id) on delete cascade,
  company_id uuid not null references public.companies(id) on delete cascade,
  full_name text not null check (char_length(full_name) between 1 and 120),
  role text not null check (role in ('manager', 'employee')),
  created_at timestamptz not null default now()
);

create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  assigned_to uuid not null references public.users(id) on delete restrict,
  created_by uuid not null references public.users(id) on delete restrict,
  title text not null check (char_length(title) between 1 and 160),
  description text not null default '' check (char_length(description) <= 2000),
  status text not null default 'pending'
    check (status in ('pending', 'in_progress', 'completed')),
  due_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index tasks_company_id_idx on public.tasks(company_id);
create index tasks_assigned_to_idx on public.tasks(assigned_to);

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end;
$$;
create trigger tasks_set_updated_at before update on public.tasks
for each row execute function public.set_updated_at();

-- Direct Supabase API callers who are employees may change only their own task's status.
-- Backend calls use the service key (no auth.uid()) and are separately checked in Python.
create or replace function public.limit_employee_task_updates()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or public.current_app_role() = 'manager' then
    return new;
  end if;
  if old.assigned_to <> (select id from public.users where auth_user_id = auth.uid())
     or new.company_id <> old.company_id
     or new.assigned_to <> old.assigned_to
     or new.created_by <> old.created_by
     or new.title <> old.title
     or new.description <> old.description
     or new.due_date is distinct from old.due_date then
    raise exception 'Employees may update only the status of their assigned task';
  end if;
  return new;
end;
$$;
create trigger tasks_limit_employee_updates before update on public.tasks
for each row execute function public.limit_employee_task_updates();

-- SECURITY DEFINER avoids an RLS recursion when looking up the caller profile.
create or replace function public.current_company_id()
returns uuid language sql stable security definer set search_path = public as $$
  select company_id from public.users where auth_user_id = auth.uid() limit 1;
$$;

create or replace function public.current_app_role()
returns text language sql stable security definer set search_path = public as $$
  select role from public.users where auth_user_id = auth.uid() limit 1;
$$;

alter table public.companies enable row level security;
alter table public.users enable row level security;
alter table public.tasks enable row level security;

create policy "members can view their company" on public.companies for select
  using (id = public.current_company_id());
create policy "members can view company users" on public.users for select
  using (company_id = public.current_company_id());
create policy "members can view company tasks" on public.tasks for select
  using (company_id = public.current_company_id());
create policy "managers create company tasks" on public.tasks for insert
  with check (
    company_id = public.current_company_id()
    and public.current_app_role() = 'manager'
    and exists (select 1 from public.users u where u.id = assigned_to
                and u.company_id = public.current_company_id())
  );
create policy "members update permitted company tasks" on public.tasks for update
  using (company_id = public.current_company_id())
  with check (company_id = public.current_company_id());
