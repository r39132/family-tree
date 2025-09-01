# Architecture Overview

## Data Flow

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

## Request Flow (Edge to Data)

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
  FE-->>U: "Check your email" message
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

## Firestore Data Model

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
