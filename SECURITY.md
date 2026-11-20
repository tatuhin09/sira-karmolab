# Security and deployment boundaries

This is a loopback-only training prototype, not a production internet service. Use fictional data. Do not expose this server publicly by changing the bind address or disabling Host checks without first designing authentication, trainer-role authorization, TLS, abuse controls, provider quotas, and a data policy.

## Credentials

- Never commit API keys or private environment files.
- The optional launcher reads a named key from a private local file or process environment; it never needs keys in browser JavaScript.
- `.env.example` contains placeholders only and is not automatically loaded.
- Runtime SQLite files and local submission artifacts are ignored and excluded from this source publication.

## Data

AI mode transmits the current trainee response and bounded policy/scenario context to Google. The application does not automatically redact personal data. Session cookies separate normal history access but are not accounts, roles, or proof of identity. The trainer controls are available inside the same local session. Runtime SQLite files are not encrypted by the application. Clearing browser cookies does not delete server data.

## Model output

Response-schema, exact-quote and clause checks constrain output; they do not guarantee semantic accuracy. Provider failure or quota exhaustion produces visibly labelled local cues. A trainer must review the full response before making a consequential competence decision.

## Reporting

For a security issue, use the repository owner's GitHub profile contact options. Do not post credentials, private learner data, or exploitable sensitive details in a public issue. No dedicated security mailbox or formal response SLA has been established.
