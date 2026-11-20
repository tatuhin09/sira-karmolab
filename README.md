<p align="center"><img src="dist/logo.png" width="88" alt="SIRA Karmolab logo"></p>

# SIRA Karmolab

**Practice workplace decisions. Understand the policy. Demonstrate your skills.**

### [Open the live demo](https://sira-karmolab-tatuhin09.azurewebsites.net)

**No installation, account, or personal API key is required to try the hosted demo.**

Built by **SIRA Labs** for **International AI Builders Congress 2026**.  
**Domain:** LearnSphere AI — Education, Skills & Workforce Transformation  
**Challenge:** SkillBridge

## What is SIRA Karmolab?

SIRA Karmolab helps aspiring and newly hired customer-service staff practice workplace scenarios before handling real customers. Its first use case is e-commerce support: responding to damaged-product complaints without promising an unapproved refund, overlooking evidence, or requesting information the customer has already supplied.

Trainees write responses, inspect provisional policy-linked feedback, revise their wording, and try a related case. Trainers can review the resulting work samples. The interface supports **Bangla and English**.

## Try the demo

1. Open the [live application](https://sira-karmolab-tatuhin09.azurewebsites.net) and start the first exercise.
2. Read the fictional customer complaint and sample-store policy.
3. Select a sample response or write a reply in your own words.
4. Inspect feedback, quoted wording, and the relevant policy clause.
5. Revise your response, continue to a related case, and inspect the saved work history.
6. Explore the trainer-review demonstration controls after the follow-up exercise.

Use fictional data only. The trainer-review controls demonstrate a workflow; they do not authenticate a trainer or issue a verified certification.

## What is live today?

| Capability | Current implementation |
| --- | --- |
| Hosted application | Public HTTPS demo on Azure App Service |
| Languages | Bangla and English interfaces |
| Practice | Two-attempt journey using four fictional scenario variants |
| AI feedback | Gemini 3.1 Flash Lite with structured output |
| Evidence checks | Exact quote presence, allowed finding types and policy-clause mappings |
| Revision | Original response and edited response retained separately |
| Follow-up case | Selected using bounded rules based on response observations |
| History and review | Session-scoped responses, revisions, notes and verdicts in SQLite |
| Failure recovery | Clearly labelled local observations when AI output is unavailable or rejected |

The deployed app has **Gemini enabled on the server**. The application permits **10 attempted AI requests per UTC day**, including failed attempts. If that budget or the provider quota is exhausted, practice continues with visibly labelled local rule-based observations. Local cues are not a local LLM and can misinterpret context; final assessment remains with a trainer.

## How the AI works

```text
Sample policy + customer case + trainee response
                    ↓
Input validation and saved-submission lookup
                    ↓
One bounded Gemini request, if enabled and within budget
                    ↓
Structured output, quote and policy-clause checks
                    ↓
Provisional AI feedback or explicitly labelled local observations
                    ↓
Revision → related case → saved work → trainer review
```

The model receives only the small sample policy, current case and trainee response. The app does not run a vector database, multi-agent research pipeline, or automatic self-improvement system. A matching quote and valid JSON do not by themselves establish semantic correctness.

## Verification completed

- **14 offline tests passed locally**, covering model-output validation, budgets, idempotence, persistence, session isolation and hosted-server boundaries.
- Earlier browser checks covered the full practice flow, revision, reviews, language switching, reload, failure recovery and mobile layouts.
- The deployed HTTPS home page, scripts, logo, health endpoint and policy API returned successful responses.
- **One hosted Gemini request returned accepted AI observations.** A duplicate submission reused its saved result, and a separate session could not read that history.
- Credential, source-code and database paths were checked to return `404`; session cookies were checked to be secure.

These are integration checks, not a measured accuracy percentage, an availability SLA, or evidence of improved workplace performance. See [evaluation notes](docs/EVALUATION.md) for scope and limitations.

## Hosting and data

The demo uses **Azure App Service Free (F1)** with Python 3.12, Flask, Gunicorn and SQLite. The first visit may take longer because free hosting can sleep or reach shared resource quotas. Practice data and API-attempt counts persist under `/home/karmolab`, outside the deployed source directory.

In AI mode, the current response and bounded scenario context are sent to Google. API credentials remain in private server settings. History is separated by browser-session cookies; there are no full learner/trainer accounts. Clearing a cookie does not delete server-side records. Automatic personal-data redaction is not implemented.

## Source code and technical documentation

| Resource | Contents |
| --- | --- |
| [Local setup](docs/LOCAL_SETUP.md) | Run your own copy, optional local Gemini configuration, and test commands |
| [Architecture](docs/ARCHITECTURE.md) | Components, validation boundary and persistence |
| [Application API](docs/API.md) | Routes, request shapes, sessions and errors |
| [Evaluation](docs/EVALUATION.md) | Tests, historical checks and evidence limits |
| [Azure deployment](deployment/README.md) | Startup command, environment settings, storage and hosting limits |
| [Security](SECURITY.md) | Credential handling, data boundaries and production work remaining |
| [Code provenance](core/provenance.json) | Original SIRA contract-module path, commit and hash |

Main entry points: `start_local.py` for a local copy; `cloud_app.py` for the hosted WSGI demo. Front-end code and logo are in `dist/`; tests are in `tests/`.

Local installation and key-management instructions have been moved out of this overview. They apply to developers running their own copy, not visitors to the hosted demo.

## Reuse and AI-assisted development

A specific `research_contracts.py` request/result contract module was reused from the original SIRA codebase. The original research workers, scheduler, autonomous memory promotion and self-improvement runtime are not included. ChatGPT and Codex assisted with planning, implementation, tests, review and writing. Gemini is the runtime feedback provider.

No blanket open-source licence is granted by this repository; original-project and third-party rights remain with their respective owners.

## Next steps

Separate authenticated trainer access, organization-specific policies, a broader independently labelled Bangla evaluation set, and real learner/trainer pilots remain planned work. Learning gains, trainer-time savings, commercial demand and revenue have not yet been independently measured.

The proposed initial market is e-commerce onboarding and vocational practice. An organizational training licence or pilot is a proposed business model, not reported adoption.
