# Local API

Base URL with the launcher: `http://127.0.0.1:8767`. Only matching localhost/127.0.0.1 Host values are accepted. These are local application APIs, not public MCP tools.

All POST endpoints require `Content-Type: application/json`, a JSON object, and a valid UUID `id`. Request bodies must be between 1 and 16,000 bytes. Origin, when supplied, must match the server origin. Answer, revision, and review-note text must be nonempty after trimming and at most 1,500 characters.

| Method and path | Input | Result |
| --- | --- | --- |
| `GET /api/policy` | None | Policy version and SIRA contract-shaped sample-policy records; establishes a session cookie |
| `GET /api/history` | Session cookie | Up to 50 attempts from that session, newest first |
| `POST /api/assess` | `id`, `case_id`, `answer` | Saved attempt with provisional assessment |
| `POST /api/revision` | `id`, `revision` | `{"saved":true}` for an attempt in the same session |
| `POST /api/review` | `id`, `note`, `verdict` | `{"saved":true}` for an attempt in the same session |

Case IDs: `initial`, `transfer`, `missing_photo`, `timing`.

Review verdicts: `pending`, `needs_practice`, `ready`. A review endpoint exists for the local prototype; it does not authenticate a separate trainer role.

Assessment request example:

```json
{
  "id": "5fe4a203-1480-4b2a-b2ce-b92f0ec56c94",
  "case_id": "initial",
  "answer": "Could you share the order number and a photo? We will send them for verification."
}
```

Assessment fields include `status: trainer_review_required`, `engine`, `review_mode`, `policy_version`, `policy_hash`, `case_message`, `findings`, `next_case`, `next_message`, and `recommendation_reason`. Modes are `local`, `ai`, and `fallback`. Only accepted Gemini results have `engine: gemini`; local results use `local_cues`.

A finding includes `kind`, `quote`, `clause`, bilingual `explanation`, and the referenced sample `policy`. An empty findings list is not a pass or certification.

Common errors: `400 invalid_request`, `403 invalid_host` or `invalid_origin`, `415 json_required`, and `404 not_found`. Missing or cross-session attempt updates are rejected. Raw provider errors and credentials are not exposed.

Use the same submission ID for a retry of the same answer/case. Changing the answer requires a new ID. This prevents avoidable duplicate model requests; it does not make an in-memory browser draft durable until the request succeeds.
