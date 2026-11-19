# Multi-Tenant Task Management API

A small task-management system for multiple companies. Managers create tasks for people in their company; employees can update the status of tasks assigned to them.

## Structure

- `typescript/tasks.ts` — typed task utilities and API client (Task A)
- `backend/models.py` — Pydantic request/response models
- `backend/main.py` — FastAPI routes and dependency wiring
- `backend/service.py` — business rules and Supabase access
- `sql/schema.sql` — database schema, indexes, triggers, and RLS policies
- `sql/queries.sql` — required reporting queries

The split is intentional: HTTP details stay in `main.py`, validation stays in `models.py`, and task rules/data access stay in `service.py`.

## Setup

### 1. Database

1. Create a Supabase project and run `sql/schema.sql` in its SQL Editor.
2. Create Supabase Auth users, then create a matching `public.users` profile for each user. The `auth_user_id` field must equal the Auth user UUID.
3. Copy the project URL and **service role key**. Keep the key private; do not put it in source control or a frontend application.

### 2. API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
cd ..
uvicorn backend.main:app --reload
```

Interactive documentation is available at `http://127.0.0.1:8000/docs`.

Every API request needs a Supabase user access token:

```http
Authorization: Bearer <supabase-access-token>
```

### 3. TypeScript

```bash
npm install
npm run check
npm run test:ts
```

### 4. Python tests

From the repository root, with the virtual environment active:

```bash
pytest backend/tests
```

## Endpoints

| Method | Path | Access |
| --- | --- | --- |
| `POST` | `/tasks` | Manager only; assignee must be in the same company |
| `GET` | `/tasks` | Signed-in company member; receives only their company tasks |
| `PATCH` | `/tasks/{id}` | Manager or the assigned employee; changes status |

## Security approach

The client never supplies a trusted `company_id`. FastAPI validates the Supabase Bearer token, looks up the matching application profile, and uses that profile's `company_id` for every task query. Therefore changing a query string, body field, or path identifier cannot switch the company context.

RLS provides a second layer for direct database/API access: policies compare every task's `company_id` to the caller's company, derived from `auth.uid()`. A user from Company A consequently cannot read or write a Company B row even if they manipulate a request. The service role key is used only by the backend and is never exposed to a browser. Since a service role bypasses RLS, the backend repeats the same company checks before every operation.

## Assumptions

- Supabase Auth is the source of identity.
- A user has one company membership for this assignment.
- A manager may update any task in their company; an employee may update only a task assigned to them.
