# API contract

The production frontend and API share one origin. Protected routes resolve an anonymous browser identity from an HttpOnly cookie. Call GET /api/session before protected requests; use its csrf_token plus an exact Origin header on every mutation. Production uses Secure, SameSite=Strict, Path=/ and the __Host-mood cookie name. No cross-origin API access, password login, or upload endpoints are provided.

| Method | Route | Contract |
|---|---|---|
| GET | /api/health | `{status:"ok"}` after database query; no cookie required |
| GET | /api/session | Creates/reuses anonymous session; `{csrf_token,expires_at}`; cookie expiry is absolute 30 days |
| GET | /api/specialties | Public array of `{id,label}` |
| GET | /api/quiz | Public array of `{id,text,options:[{label}]}`; option effects remain server-side |
| POST | /api/submit-quiz | Exact JSON `{specialty,answer_indexes,difficulty}`; requires valid `Idempotency-Key` of 16–80 ASCII letters/digits/underscore/hyphen; returns `{pick_id,completed,mood_vector,mood_description,candidates,result,reason}` |
| GET | /api/history | Up to 200 current-session picks, newest first; no raw answers or mood vectors |
| GET | /api/picks/<pick_id> | Reopen an owned pick's canonical project and completion status; another session receives 404 |
| POST | /api/complete | Exact JSON `{pick_id}`; marks only that owned pick completed; repeat is safe |
| GET | /api/export | `{version:1,picks:[...]}` for this session |
| DELETE | /api/history | Deletes this session's picks; returns `{deleted:true}` |
| DELETE | /api/session | Deletes anonymous identity and cascading picks, expires cookie; `{deleted:true}` |

Quiz input: exactly seven integer option indexes (Python booleans, floats, nested values and out-of-range indexes are rejected); configured specialty; difficulty easy, medium or hard. All write bodies must be application/json and at most 4096 bytes. The server supplies project titles and IDs; completion cannot spoof titles or affect another visitor.

The client reuses a request key after a failed/lost response. A same-session key with the same payload replays its recorded winner instead of creating a second pick. Reusing it for different input returns 409. Starting a fresh quiz creates a new intent. Deduplication lasts while the pick is retained: a session keeps its newest 200 picks and expires after 30 days. Catalogue removal can make a saved project unavailable with 404/409.

Errors are JSON `{error:"CODE",request_id:"uuid"}`. 400 invalid body/selection/answers; 401 session required; 403 origin/CSRF/cross-site rejection; 404 absent or unowned record; 409 idempotency conflict; 413 oversized body; 415 non-JSON write; 421 invalid Host; 429 request/session creation quota, with Retry-After. Production debug mode is disabled. Responses under /api use Cache-Control: no-store. Session bootstrap and public routes are rate limited; health is exempt for monitoring.
