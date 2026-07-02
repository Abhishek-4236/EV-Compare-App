# Production Readiness Roadmap

Last updated: 2026-06-28

## Cycle 1 Completed

### Fixed

- Critical security issue: chat session history and continuation now enforce server-side ownership.
  - Owner can read/continue their own session.
  - Anonymous users cannot read persisted server-side session history.
  - A different signed-in user cannot read or continue another user's session.

### Validation

- Backend targeted security regression: passed.
- Backend test suite: `59 passed`.
- Python compile sanity for changed files: passed.
- Frontend lint: passed.
- Frontend production build: passed.

## Cycle 2 Completed

### Fixed

- High security issue: sensitive API endpoints now have application-level rate limiting.
  - `/api/auth/*` has a stricter bucket for login/signup abuse resistance.
  - `/api/chat/*` has a separate bucket to reduce AI/provider abuse risk.
  - `/api/admin/*` has a stricter bucket to reduce upload/admin endpoint abuse risk.
  - Other `/api/*` routes have a default bucket.

### Validation

- Backend test suite: `61 passed`.
- Python compile sanity for changed backend files: passed.
- Frontend lint: passed.
- Frontend production build: passed.

## Cycle 3 Completed

### Fixed

- High security issue: admin dataset uploads now validate before saving/importing.
  - Rejects non-`.xlsx` filenames.
  - Rejects empty or oversized files.
  - Rejects invalid workbook content.
  - Rejects workbooks missing required importer columns.
  - Keeps upload size configurable through `DATASET_UPLOAD_MAX_BYTES`.

### Validation

- Backend test suite: `66 passed`.
- Python compile sanity for changed backend files: passed.
- Frontend lint: passed.
- Frontend production build: passed.

## Cycle 4 Completed

### Fixed

- High architecture/database issue: Alembic migration foundation added.
  - Added safe Alembic config that reads the existing `DATABASE_URL` from settings.
  - Added migration environment wired to existing SQLAlchemy metadata.
  - Added initial schema migration for current tables, indexes, enum, JSONB, and pgvector columns.
  - Added Alembic to backend requirements.

### Validation

- Alembic history: passed.
- Alembic offline SQL rendering: passed.
- Backend test suite: `66 passed`.
- Python compile sanity for migration files and changed backend files: passed.
- Frontend lint: passed.
- Frontend production build: passed.

## Cycle 5 Completed

### Fixed

- High privacy issue: outbound LLM prompts now redact common sensitive user data before provider calls.
  - Redacts email addresses.
  - Redacts Indian mobile numbers.
  - Redacts Aadhaar-like identifiers.
  - Redacts payment-card-like numbers.
  - Redacts obvious API key, token, password, bearer, and secret assignments.
  - Keeps raw user input available only for local parsing, database lookup, and deterministic tool logic.

### Validation

- Focused LLM privacy regression: `2 passed`.
- Backend test suite: `68 passed`.
- Python compile sanity for changed files: passed.
- Frontend lint: passed.
- Frontend production build: passed.

## Cycle 6 Completed

### Fixed

- High architecture/AI issue: answer grounding validation and confidence scoring were extracted from `EVRAGService`.
  - Added `backend/services/ev_answer_safety.py`.
  - Moved hallucination guard logic into a directly testable module.
  - Moved confidence-level scoring into the same safety/scoring boundary.
  - Kept behavior unchanged: `EVRAGService` still orchestrates the same flow, but no longer owns these safety internals.

### Validation

- Focused answer-safety regression: `3 passed`.
- Backend test suite: `71 passed`.
- Python compile sanity for changed files: passed.
- Frontend lint: passed.
- Frontend production build: passed.

## Cycle 7 Completed

### Fixed

- High architecture issue: subsidy calculation logic no longer lives inside the HTTP route layer.
  - Added `backend/services/subsidy_service.py` as the shared subsidy/TCO domain service.
  - Updated `backend/routes/subsidies.py` to act as an API adapter.
  - Updated `backend/services/ev_tools.py` to call the service directly instead of importing `routes.subsidies`.
  - Added a dependency-direction regression test so services do not re-import the subsidy route module.
  - Added a chat regression test for the subsidy/TCO tool path that previously returned `500` after extraction.

### Validation

- Focused subsidy-service regression: `3 passed`.
- Backend test suite: `75 passed`.
- Python compile sanity for changed files: passed.
- Frontend lint: passed.
- Frontend production build: passed after rerun with sandbox escalation because Vite/Rolldown hit `spawn EPERM` inside the restricted sandbox.

## Remaining Priority Issues

| Priority | Issue | Difficulty | Dependencies | Status |
|---|---|---:|---|---|
| Critical | Real/local secret hygiene around `.env` and runtime artifacts | Medium | Git cleanup decision, secret rotation decision | Remaining |
| High | External LLM prompt can include unnecessary personal data | Medium | Provider-boundary redaction | Completed in Cycle 5 |
| High | No rate limiting on auth/chat/admin upload | Medium | Middleware or proxy strategy | Completed in Cycle 2 |
| High | Admin upload validation is too weak | Medium | Dataset schema validator | Completed in Cycle 3 |
| High | No Alembic migrations | High | Current schema baseline | Completed in Cycle 4 |
| High | RAG service is too centralized | High | Intent handler design | Partially improved in Cycle 6 |
| High | Route/service coupling in subsidy tool path | Medium | Subsidy service extraction | Completed in Cycle 7 |
| Medium | Duplicate vehicle filtering/scoring logic | Medium | Shared domain service | Remaining |
| Medium | Frontend chat page is too large | High | Hook/component split plan | Remaining |
| Medium | Frontend direct Overpass dependency | Medium | Backend station adapter/cache | Remaining |
| Medium | Garage uses comma-separated vehicle IDs | High | Migration plan | Remaining |

## Scores After Cycle 7

| Area | Previous | Current | Notes |
|---|---:|---:|---|
| Production readiness | 64% | 66% | Added provider-boundary privacy redaction, began RAG modularization, and fixed route/service coupling. |
| Security | 6.2/10 | 6.5/10 | Chat ownership, rate limiting, upload validation, and LLM prompt redaction improved; cookies/secrets remain. |
| Architecture | 6.4/10 | 6.6/10 | Answer safety extracted from RAG orchestration; subsidy business logic moved out of route layer. |
| AI/RAG | 7.2/10 | 7.3/10 | Provider prompts redact obvious sensitive data, and grounding checks are now directly testable. |
| Backend | 7.1/10 | 7.3/10 | Tool and route layers now share subsidy logic through a service module. |
| Frontend | 6.0/10 | 6.0/10 | No frontend code changes. |
| Database | 5.0/10 | 5.8/10 | Alembic baseline added; schema design debt remains. |
| Overall project | 6.8/10 | 7.0/10 | One high coupling issue closed; larger RAG/frontend/database work remains. |

## Next Recommended Cycle

Next highest-priority issue: RAG service modularization.

Reason: `EVRAGService` remains the largest backend architecture risk. It coordinates parsing, tools, retrieval, memory, answer construction, provider calls, and validation in one place.
