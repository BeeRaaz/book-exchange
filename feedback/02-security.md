# Layer 2 — Security

**Why this layer:** authentication exists and the basics are right (bcrypt passwords, JWTs,
ownership checks). But a few gaps would let someone stay logged in forever, brute-force accounts,
or keep using a disabled account. These protect real users and their data. (Covers #8 and #11.)

| Item | Where | Why we need it (plain terms) | Fix direction |
|------|-------|------------------------------|---------------|
| 🔴 Broken refresh-token design | `routers/auth.py:98` | Any still-valid login token can refresh *itself* forever, and there's no way to revoke it. If a token leaks, the attacker never gets logged out. | Separate, longer-lived **refresh** tokens with a `type` claim + rotation; re-check the user on refresh |
| 🔴 No rate limiting | all `/auth/*` endpoints | Nothing stops thousands of password guesses per minute on `/login`, or signup spam. | Add rate limiting (e.g. `slowapi`), strictest on `/auth/login` |
| 🟠 `is_active` is never checked | everywhere | The `is_active` flag exists but a disabled/banned user can still log in and use the API. | Reject inactive users in `get_current_user` and at login |
| 🟠 Weak input validation | `schemas.py` | `email: str` accepts `"not-an-email"`; there's no minimum password length. Bad data gets in and weak passwords are allowed. | Use `EmailStr` + field limits (min/max length, password rules) |
| 🟡 Account enumeration on register | `routers/auth.py:37-47` | Different errors for "email taken" vs "username taken" let an attacker discover who has an account. | Return one generic conflict message |
| 🟡 `python-jose` has known CVEs | `pyproject.toml` | The JWT library has published security advisories (algorithm-confusion / DoS). | Consider migrating to `pyjwt` (better maintained) |
| 🟢 bcrypt 72-byte limit not handled | `auth.py:15` | bcrypt silently ignores anything past 72 bytes, so very long passwords aren't fully used. | Validate/limit password length before hashing |
| 🟢 No logout / revocation | — | A stolen token stays valid until it expires; you can't kick it out early. | Token blocklist, or short expiry + refresh rotation |

---

### The refresh-token issue, briefly

**Today** (`routers/auth.py`) — `/refresh` accepts a normal access token and mints another one:

```python
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest):
    decoded = decode_access_token(payload.token)     # any valid access token works
    token = create_access_token({"sub": decoded["sub"], "user_id": decoded.get("user_id")})
    return TokenResponse(access_token=token)
```

Problems: the same token type is used for login *and* refresh, so a session can be extended
indefinitely; the user isn't re-loaded (a deleted/disabled user keeps working); and there's no
revocation. The standard fix is two token types — a short-lived **access** token and a
longer-lived **refresh** token (with a `type` claim) — and to re-check the user on refresh.
