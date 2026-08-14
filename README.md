# TeamFlow AI

A team project-management platform with an AI assistant that answers questions
about uploaded project documents. The application logic is deliberately simple.
The point of the project is the engineering around it: clean backend
architecture, a typed React frontend, containerization, CI/CD, Infrastructure-
as-Code on AWS, and observability.

This repository is built in stages. This is the backend foundation (Stage 2).

## Architecture (target)

```
React + TypeScript  ->  Nginx / Load Balancer  ->  FastAPI
                                                      |
                        +-----------------------------+-----------------------------+
                        |                             |                             |
                   Service layer                  Redis + worker              pgvector + LLM
                        |
                   Repository layer
                        |
                   PostgreSQL
```

## Backend layering

Every request flows through four layers, and each layer has one job:

```
API (FastAPI routers)      validate input, shape output, no logic
   -> Service              business rules, owns the transaction
      -> Repository        the only layer that talks to the database
         -> PostgreSQL
```

Why this matters: business code never imports FastAPI and never writes SQL, so
each layer is testable on its own. The service takes its repository through its
constructor (dependency injection), so a unit test passes in a fake repository
and never needs a real database.

## Run it locally

You need Docker and Docker Compose.

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Then open:

- http://localhost:8000/api/v1/health  (liveness)
- http://localhost:8000/api/v1/docs    (interactive OpenAPI docs)

Create a user:

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","full_name":"Your Name","password":"supersecret"}'
```

## Data model (Stage 3)

Eight tables with real foreign keys, indexes, and delete behaviour:

```
organizations
   |
   +-- users            (organization_id, SET NULL on org delete)
   +-- projects         (organization_id, CASCADE on org delete)
          |
          +-- tasks         (project_id CASCADE; assignee_id -> users SET NULL)
          |      +-- comments  (task_id CASCADE; author_id -> users SET NULL)
          +-- documents     (project_id CASCADE)

notifications   (user_id CASCADE)
audit_logs      (actor_id -> users SET NULL)
```

Delete rules are deliberate: deleting a project removes its tasks, comments, and
documents (they cannot exist without it), but deleting a user who authored a
comment keeps the comment and just nulls the author, so history survives.

Indexes exist where the real queries are: unique on user email, composite on
(project_id, status) for the task board, (user_id, is_read) for unread
notifications, and (entity_type, entity_id) for audit lookups.

## Migrations

The schema is managed by Alembic, not by the app. The container runs
`alembic upgrade head` on startup (see entrypoint.sh) before serving requests.

To create a new migration after changing a model:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe change"
docker compose exec backend alembic upgrade head
```

## Run the tests

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
ruff check .
mypy app
```

## Build roadmap

- [x] Stage 1: Repository architecture
- [x] Stage 2: Backend foundation (config, logging, errors, DB, one entity end to end, health, tests, Dockerfile, compose)
- [x] Stage 3: PostgreSQL models + Alembic migrations (organizations, projects, tasks, comments, documents, notifications, audit logs)
- [x] Stage 4: Authentication + RBAC (JWT login, refresh tokens, protected routes, role checks)
- [x] Stage 5: Frontend foundation (React, TypeScript, Vite, Tailwind, routing, authenticated sign-in)
- [ ] Stage 6: Projects / tasks / comments
- [ ] Stage 7: Redis + background worker (notifications)
- [ ] Stage 8: Document upload (S3 locally via MinIO)
- [ ] Stage 9: AI / RAG assistant (pgvector, embeddings, LLM)
- [ ] Stage 10: Testing (pytest integration, Vitest, Playwright)
- [ ] Stage 11: Nginx reverse proxy
- [ ] Stage 12: GitHub Actions CI/CD
- [ ] Stage 13: Terraform (VPC, RDS, ECR, ECS, ALB, IAM, S3, CloudWatch)
- [ ] Stage 14: AWS deployment
- [ ] Stage 15: Kubernetes + Helm
- [ ] Stage 16: Prometheus + Grafana
- [ ] Stage 17: Security hardening
- [ ] Stage 18: Architecture diagram + CV write-up
