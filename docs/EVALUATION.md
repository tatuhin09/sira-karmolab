# Evaluation and evidence limits

## Reproducible offline checks

Run `python3 -m unittest discover -s tests -v`. These tests use mocked provider responses or a temporary local server/database, never live model calls.

The original eight model-adapter tests cover disabled AI, persisted call budgets, invalid quotes/clause mappings, valid structured output, connection-failure fallback, incomplete output, fabricated quote rejection, and exhausted budgets. HTTP tests additionally cover idempotent submissions, session isolation, saved revisions/reviews, and invalid-origin rejection. Test output is the current authority for counts.

`node --check dist/app.js` checks JavaScript syntax. CI is configured to run offline Python checks and this syntax check; a configured workflow is not evidence of a successful remote CI run until GitHub reports one.

## Historical browser checks

During development, browser checks covered:

- Original response → feedback → revision → changed case → trainer note/verdict.
- History persistence on reload and language switching.
- Isolation between different browser sessions.
- Draft retention after a failed submission request.
- Home, explanation, practice, and history navigation in both languages.
- Desktop and 390-pixel mobile layouts without horizontal overflow; logo loading.
- A real accepted Gemini assessment and visibly labelled daily-limit fallback.

These checks were run in the development environment. The complete browser harness is not yet packaged for portable execution in this repository.

## Limited live model observations

Five authorized Gemini attempts were made during initial integration. Three produced accepted AI results; two used fallback, including one connection failure. These attempts were iterative development checks with changing validation/schema/timeout settings, not a controlled accuracy or availability benchmark.

Examples included a Bangla response guaranteeing a refund today and wording that refused to guarantee before approval. A guarantee was correctly flagged in an accepted structured result, while the refusal example was not flagged as a guarantee. Quote presence and the policy-clause mapping were checked by code. This is insufficient to establish broad language understanding or production reliability.

No further live calls are triggered by the tests or CI. Additional model experiments require an explicit usage budget.

## Not yet established

There is no independently labelled Bangla test set, real learner pilot, measured improvement in job performance, measured trainer-time savings, or validated commercial adoption. The local rule fallback can misread negation. Exact quotes do not prove correct semantic interpretation, and schema compliance is not educational validity.

## Pilot plan

Recruit consenting learners and trainers, agree on an actual organization's policy, and prepare independently labelled cases. Measure policy-compliant response rate, repeated errors on changed cases, and trainer review time. Include negation, already-provided evidence, missing information, ambiguous approval, and attempted instruction injection. Report denominators, failures and fallback frequency alongside any gains. Keep planned results separate from measured results.
