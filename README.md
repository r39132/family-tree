# 🌳 Family Tree

![Python](https://img.shields.io/badge/Python-3.12.3-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112%2B-009485)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![Node](https://img.shields.io/badge/Node-20.x-339933)
![Ruff](https://img.shields.io/badge/Lint-ruff-46a7f8)
![Black](https://img.shields.io/badge/Format-black-000000)
![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
![Coverage](docs/coverage.svg)

<!-- If you adopt GitHub Actions, replace repo and workflow names below -->
[![CI-CD](https://github.com/r39132/family-tree/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/r39132/family-tree/actions/workflows/ci-cd.yml)

A full‑stack repo for a **Family Tree** website you can run locally or deploy on **Google Cloud**.

- **Frontend:** Next.js (TypeScript), nature‑themed UI, pages for Login, Register (with invite code), Forgot Password, Reset Password, Tree view with CRUD and move
- **Backend:** FastAPI (Python 3.12.3), Firestore (named DB supported), JWT auth, email reset flow (SMTP or console)
- **Quality:** uv, ruff (lint/format), black config, pytest + coverage, pre-commit
- **Deploy:** Dockerfile + GitHub Actions CI/CD to Cloud Run

## Quick Start (Local)

### Prereqs
- Node 18+ and npm
- Python 3.12.3 (project pinned via `.python-version`)
- `uv` package manager (https://docs.astral.sh/uv/)
- `gcloud` SDK (if deploying or testing Firestore access locally with ADC/SA)
- Firestore database already created (named or (default))

### Configure env

Create `backend/.env` (see `backend/.env.example`) and `frontend/.env.local` (see `frontend/.env.local.example`).

For local development with a service account:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
export GOOGLE_CLOUD_PROJECT=your-project-id
export FIRESTORE_DATABASE=family-tree   # your DB id; omit or set to (default) if using the default
```

### Python env setup (uv venv)

This project uses uv-managed virtual environments. To create/sync the backend env:

```bash
cd backend
uv venv --python 3.12.3   # create a .venv with Python 3.12.3
uv sync                   # install project deps into .venv
```

Activate the venv (macOS bash):

```bash
source .venv/bin/activate
```

You can also run commands without activating by prefixing with `uv run`:

```bash
uv run python -V
uv run pytest
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

To upgrade/switch Python, update `.python-version` (root and backend) and recreate the venv:

```bash
rm -rf backend/.venv
uv venv --python 3.12.3
uv sync
```

### Git hooks (pre-commit / pre-push)

This repo uses pre-commit for formatting/linting and a pre-push test check:

- pre-commit: ruff (with --fix), ruff-format, black, end-of-file-fixer, trailing-whitespace
- pre-push: run backend pytest via uv

Install and activate hooks:

```bash
cd backend
uv run pre-commit install            # install pre-commit (pre-commit hooks)
uv run pre-commit install --hook-type pre-push  # also install pre-push

# optional: run on all files once
uv run pre-commit run --all-files
```

### Run locally

```bash
# Backend
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Frontend (in another terminal)
cd ../frontend
npm install
npm run dev
```
Frontend default: http://localhost:3000 (proxying calls to `http://localhost:8080`)

### Docker Compose (optional)

```bash
docker compose up --build
```

## CI/CD to Cloud Run

- Build & test on push
- Build container and deploy to Cloud Run (backend only) when pushing to `main`

### Required GitHub Secrets

- `GCP_PROJECT_ID`
- `GAR_LOCATION` (e.g., `us-central1`)
- `CLOUD_RUN_REGION` (e.g., `us-central1`)
- `CLOUD_RUN_SERVICE` (e.g., `family-tree-api`)
- `GCP_SA_KEY` – JSON key for a deployer service account with:
  - Artifact Registry Writer
  - Cloud Run Admin
  - Service Account User
  - (and project Viewer)

**Note:** Alternatively use Workload Identity Federation; adjust the workflow accordingly.

## Architecture Overview

### Data Flow

```mermaid
flowchart LR
  subgraph Client[Browser]
    UI[React/Next.js Pages]
  end

  subgraph API[FastAPI Backend]
    Auth[Auth & Invites]
    Tree[Tree & Relations]
    Email[SMTP/Dev Logger]
  end

  DB[(Firestore)]
  SMTP[(SMTP Server)]

  UI <--> |JWT over HTTPS| API
  Auth <--> DB
  Tree <--> DB
  Auth -- reset links --> Email
  Email --> SMTP
```

### Request Flow (Edge to Data)

```mermaid
flowchart TD
  B[Browser] -->|/login, /register, /tree, etc.| FE[Next.js pages router]
  FE -->|HTTP JSON + JWT| BE[FastAPI]
  BE -->|Firestore SDK| FS[Firestore]
  BE -->|SMTP| MT[Mail Server]
  FS --> BE
  MT --> BE
  BE --> FE --> B
```

## Sequence Diagrams (Major Flows)

### Login

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Submit username/password
  FE->>BE: POST /auth/login
  BE->>DB: users.get(username)
  DB-->>BE: user doc (hash)
  BE-->>FE: 200 { access_token }
  FE-->>U: Store token, redirect to Tree
```

### Forgot Password

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  participant SMTP as SMTP
  U->>FE: Enter username & email
  FE->>BE: POST /auth/forgot
  BE->>DB: users.get(username)
  DB-->>BE: user (or not)
  BE-->>SMTP: send reset link (dev: logs)
  BE-->>FE: 200 { ok: true }
  FE-->>U: “Check your email” message
```

### Register (with Invite)

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Fill form (invite, username, email, pw)
  FE->>BE: POST /auth/register
  BE->>DB: invites.get(code)
  DB-->>BE: invite active?
  BE->>DB: users.create(username)
  BE->>DB: invites.update(used_by, used_email, used_at, active=false)
  BE-->>FE: 200 { ok }
  FE-->>U: Redirect to login
```

### Generate Invites

```mermaid
sequenceDiagram
  participant A as Admin/User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  A->>FE: Choose count (1..10)
  FE->>BE: POST /auth/invite?count=N (JWT)
  BE->>DB: invites.add(N)
  DB-->>BE: codes
  BE-->>FE: 200 { invite_codes }
  FE-->>A: Show new codes + list view
```

### Add Member

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Fill member form (names, DOB)
  FE->>BE: POST /tree/members (JWT)
  BE->>DB: member_keys.create(name_key)
  BE->>DB: members.add({... dob_ts })
  BE-->>FE: 200 Member
  FE-->>U: Show updated tree
```

### Edit Member

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Change fields
  FE->>BE: PATCH /tree/members/{id}
  BE->>DB: members.get(id)
  BE->>DB: member_keys.swap if name changed
  BE->>DB: members.update({... dob_ts?})
  BE-->>FE: 200 Member
  FE-->>U: Confirm & update view
```

### View Member

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Open /view/{id}
  FE->>BE: GET /tree (or member fetch)
  BE->>DB: members.stream + relations.stream
  BE-->>FE: Tree payload
  FE-->>U: Render details read-only
```

### Delete Member

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Click Delete
  FE->>BE: DELETE /tree/members/{id}
  BE->>DB: relations.where(parent_id=id)
  BE-->>FE: 400 if has children
  BE->>DB: cleanup relations + member_keys + member doc
  BE-->>FE: 200 { ok }
```

### Move

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Drag/drop or choose new parent
  FE->>BE: POST /tree/move { child_id, new_parent_id|null }
  BE->>DB: relations.remove(child existing)
  BE->>DB: relations.add(new mapping)
  BE-->>FE: { ok }
  FE-->>U: Re-render tree
```

### Add/Unlink Spouse

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Firestore
  U->>FE: Select spouse
  FE->>BE: POST /tree/members/{id}/spouse
  BE->>DB: members.update(spouse_id on both)
  BE-->>FE: { ok }
  FE-->>U: Couple node rendered
```

### Logout

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  U->>FE: Click Logout
  FE->>FE: Clear JWT (local storage/cookie)
  FE-->>U: Redirect to /login
```

## Firestore Data Model (simplified)

- `users` (by `username` as document ID)
  - `email`, `password_hash`, `created_at`, `invite_code_used`, `reset_token` (optional), etc.
- `invites` (invite codes)
  - `code`, `expires_at`, `used_by` (optional), `active`
- `members` (family members)
  - fields: first_name, middle_name, last_name, dob, birth_location, residence_location, email, phone, hobbies (array)
- `relations`
  - `child_id` -> `parent_id` mapping
- A view endpoint assembles the tree in the backend.

## Move Semantics

Moving a node under a new parent updates the `relations` mapping; subtree relationships remain intact.

---

This starter is intentionally minimal but complete. Extend as needed.

## Screenshots

### Login
![Login](frontend/public/screenshots/login.png)

### Tree
![Tree](frontend/public/screenshots/tree.png)

### Add Member
![Add Member](frontend/public/screenshots/add-member.png)

### Edit Member
![Edit Member](frontend/public/screenshots/edit-member.png)

### All Invites
![All Invites](frontend/public/screenshots/invites.png)

### Available Invites
![Available Invites](frontend/public/screenshots/available-invites.png)


## Test Coverage

Recent run (pytest + coverage):

```
TOTAL 594 statements, 69% coverage

Notable modules:
- app/routes_tree.py ~79%
- app/routes_auth.py ~87%
- app/auth_utils.py 100%
- app/config.py 100%
- app/models.py ~85%
```

Run locally:

```
cd backend
uv run pytest
```
