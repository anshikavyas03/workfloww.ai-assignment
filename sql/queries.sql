-- The company id is derived from the authenticated user on the server, not accepted from a client.
-- :company_id represents that server-derived value.

select t.id, t.title, t.description, t.status, t.due_date, t.created_at,
       assignee.full_name as assignee_name
from public.tasks t
join public.users assignee on assignee.id = t.assigned_to
where t.company_id = :company_id
order by t.created_at desc;

select
  count(*) filter (where status = 'completed') as completed_tasks,
  count(*) filter (where status in ('pending', 'in_progress')) as pending_tasks
from public.tasks
where company_id = :company_id;
