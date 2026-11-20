# Architecture

## Scope

Karmolab is a local, request-driven training prototype. It serves the browser interface and its API from the same loopback Python HTTP server. It requires no background agent service, package installation, vector store, or local LLM.

## Components

| File | Responsibility |
| --- | --- |
| `start_local.py` | Explicit AI opt-in; reads a named key from a private file without executing it; launches the server |
| `run.py` | Host/origin checks, JSON request limits, UUID validation, session cookies, static files and API dispatch |
| `assessment.py` | Three sample-policy clauses, four scenario variants, local cue rules and bounded next-case choice |
| `ai_review.py` | Gemini request, explicit response schema, quote/clause validation, persisted UTC-day call budget and fallback |
| `store.py` | Assessments, original responses, revisions and reviews keyed by session and submission UUID |
| `core/research_contracts.py` | Original SIRA bounded request/result contracts used by local assessment and policy responses |
| `dist/` | Bangla/English browser experience, layout, logo and API client |

## Model boundary

Only the fixed policy, current scenario, already-provided information, and current trainee response are sent to Gemini. The prompt treats customer and trainee text as untrusted data. `responseSchema` constrains output shape; deterministic checks validate allowed finding types, exact quote presence, matching policy-clause IDs, and bounded explanations.

Finding types are `promise`, `repeat`, `missing`, and `verification`. The first three map to policy constraints, while verification language is an observation and does not prove a response is correct. Missing-information findings may have an empty quote. Semantic correctness, completeness, and consistent interpretation still require a trainer.

The API call has no automatic retry and does not follow redirects. Failed attempts consume the configured daily budget. Provider failures return local observations and a fixed safe reason code. Local cues can misread negation or context and must not be treated as semantic AI.

## State and replay

The browser obtains a session cookie through the policy/history APIs. HTTP-only, SameSite=Strict cookies separate ordinary browser-session histories. A submission UUID identifies an attempt. Replaying the same ID with the same answer/case returns its saved result; a different answer/case is rejected. A process-level assessment lock serializes lookup, assessment and persistence to prevent duplicate simultaneous model calls in this single-process prototype.

SQLite stores the response and an assessment snapshot, including case message, policy version/hash, engine/mode, findings, next-case recommendation, and safe fallback reason where relevant. Revisions and trainer notes/verdicts update the attempt. A separate SQLite file stores daily API counts. A revision is saved, not automatically re-evaluated.

## Limits

The loopback server and exact Host checks deliberately prevent treating this as a ready-made internet service. Full account authentication, trainer-role authorization, organization isolation, TLS termination, backup/retention/deletion controls, production request scheduling and observability remain future work. The local session cookie is not proof of learner identity. No automatic model improvement occurs from stored trainer reviews.
