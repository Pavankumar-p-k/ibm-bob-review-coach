# Security Review Findings

## CRITICAL

### SEC-001: Unsafe Deserialization — `pickle.loads` on untrusted input
- **File:** `src/user_service.py` line 41
- **Issue:** `pickle.loads(data_bytes)` deserializes arbitrary bytes with no validation. An attacker who controls the input can craft a malicious pickle payload that executes arbitrary OS commands during deserialization.
- **Fix:** Replace `pickle` entirely. Use a safe serialization format such as `json` for user preferences. If binary serialization is unavoidable, use a signed/authenticated format (e.g. `hmac`-verified) and validate the schema before deserializing.

---

### SEC-002: Command Injection — unsanitized `report_name` passed to shell
- **File:** `src/user_service.py` line 37
- **Issue:** `subprocess.call("python reports/" + report_name, shell=True)` passes user-supplied input directly to a shell. An attacker can inject shell metacharacters (e.g. `; rm -rf /`) to execute arbitrary commands on the host.
- **Fix:** Use `subprocess.run(["python", f"reports/{report_name}"], shell=False)` and strictly validate `report_name` against a whitelist of allowed report filenames before use.

---

### SEC-003: Information Disclosure — debug endpoint exposes all secrets
- **File:** `src/api.py` lines 50–57
- **Issue:** The unauthenticated `/debug` GET endpoint returns the database password, API key, and JWT secret in plaintext JSON. Any network-accessible client can retrieve these credentials without authentication.
- **Fix:** Remove the `/debug` endpoint entirely. If a health-check endpoint is needed, return only a `{"status": "ok"}` response with no sensitive data, and protect it with authentication.

---

## HIGH

### SEC-004: SQL Injection — string concatenation in `get_user`
- **File:** `src/user_service.py` line 20
- **Issue:** `"SELECT * FROM users WHERE username = '" + username + "'"` concatenates user input directly into an SQL query, allowing a classic SQL injection attack (e.g. `' OR '1'='1`).
- **Fix:** Use parameterized queries: `cursor.execute("SELECT * FROM users WHERE username = ?", (username,))`.

---

### SEC-005: SQL Injection — `%`-format string in `create_user`
- **File:** `src/user_service.py` lines 48–51
- **Issue:** `"INSERT INTO users … VALUES ('%s', '%s', '%s')" % (username, hashed, email)` uses Python string formatting to build the SQL statement, which is exploitable by injection through `username` or `email`.
- **Fix:** Use parameterized queries: `cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, hashed, email))`.

---

### SEC-006: SQL Injection — string concatenation in `update_user_email`
- **File:** `src/user_service.py` lines 59–60
- **Issue:** `"UPDATE users SET email = '" + new_email + "' WHERE id = " + str(user_id)` is vulnerable to injection via `new_email`; the `user_id` cast also provides no type safety beyond the Python coercion.
- **Fix:** Use parameterized queries: `cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))`.

---

### SEC-007: Hardcoded Secrets — DB password and API key in source
- **File:** `src/user_service.py` lines 9–10
- **Issue:** `DB_PASSWORD = "s3cr3tP@ssw0rd123"` and `API_KEY = "sk-prod-abc123XYZ789hardcoded"` are committed to source code. Anyone with repository access obtains production credentials.
- **Fix:** Remove hardcoded values. Load secrets at runtime from environment variables (`os.environ`) or a secrets manager (e.g. IBM Secrets Manager, HashiCorp Vault).

---

### SEC-008: Hardcoded Secret — JWT signing key in source
- **File:** `src/api.py` line 9
- **Issue:** `JWT_SECRET = "my-super-secret-jwt-key-do-not-share"` is hardcoded in the API module. A leaked JWT secret allows an attacker to forge authentication tokens for any user.
- **Fix:** Load the JWT secret from an environment variable (`os.environ["JWT_SECRET"]`) and ensure it is a cryptographically random value of at least 256 bits.

---

### SEC-009: Broken Authentication — static token issued at login
- **File:** `src/api.py` line 17
- **Issue:** A successful login always returns `"token": "static-token-123"`. This static string provides no real authentication: any code that checks this token will accept it for every user, making session management completely ineffective.
- **Fix:** Issue a properly signed, time-limited JWT (or equivalent) containing the authenticated user's identity. Validate the token on every protected request.

---

### SEC-010: Broken Access Control — unauthenticated `/user/<username>` endpoint exposes password hash
- **File:** `src/api.py` lines 20–27
- **Issue:** The `/user/<username>` endpoint requires no authentication and returns the user's `password_hash` in the response body. An anonymous attacker can enumerate user records and extract hashes for offline cracking.
- **Fix:** Require a valid authenticated session to access this endpoint, and never include `password_hash` (or any credential field) in API responses.

---

## MEDIUM

### SEC-011: Weak Cryptography — MD5 used for password hashing
- **File:** `src/user_service.py` lines 30 and 46
- **Issue:** `hashlib.md5(password.encode()).hexdigest()` is used to store and verify passwords. MD5 is cryptographically broken, extremely fast to brute-force, and has no salt, making it trivially reversible with rainbow tables.
- **Fix:** Replace with a purpose-built password hashing function: `bcrypt`, `argon2-cffi`, or `hashlib.scrypt` with a per-user random salt and appropriate work factor.

---

### SEC-012: Broken Access Control — `cancel_order` has no ownership check
- **File:** `src/api.py` lines 43–48; `src/order_service.py` lines 51–54
- **Issue:** Any caller can cancel any order by supplying an arbitrary `order_id`. There is no check that the authenticated user owns the order or has the required role.
- **Fix:** Verify that the authenticated user's identity matches the owner of the requested order before processing the cancellation; return HTTP 403 if not.

---

### SEC-013: Broken Access Control — `place_order` requires no authentication
- **File:** `src/api.py` lines 36–41
- **Issue:** The `/order` POST endpoint has no authentication guard, allowing unauthenticated clients to place orders.
- **Fix:** Add an `@login_required` decorator (or equivalent middleware) to enforce a valid session token before the handler executes.

---

### SEC-014: Flask debug mode enabled with `host="0.0.0.0"` in production
- **File:** `src/api.py` line 61
- **Issue:** `app.run(debug=True, host="0.0.0.0")` enables the Werkzeug interactive debugger and exposes a PIN-protected remote Python shell. If the PIN is leaked or brute-forced, an attacker gains full code execution on the server.
- **Fix:** Set `debug=False` (or control it via the `FLASK_DEBUG` environment variable defaulting to `False`). Use a production WSGI server (e.g. Gunicorn, uWSGI) instead of Flask's built-in development server.

---

## LOW

### SEC-015: Information Disclosure — `create_user` API has no input validation
- **File:** `src/api.py` lines 29–34
- **Issue:** `data["username"]`, `data["password"]`, and `data["email"]` are accessed with no length limits, format checks, or sanitization. Overly long or malformed inputs may cause unexpected behavior or be used in downstream injection attacks.
- **Fix:** Validate and sanitize all user-supplied fields before use: enforce maximum lengths, reject unexpected characters, and return HTTP 400 with a clear error message on invalid input.

### SEC-016: Missing input validation on `process_order` / `process_bulk_order`
- **File:** `src/order_service.py` lines 7–11, 29–33
- **Issue:** `qty` and `price` are used in arithmetic with no type or bounds checking. Negative values or non-numeric input could produce negative totals or raise unhandled exceptions that reveal internal stack traces.
- **Fix:** Validate that `qty` and `price` are positive numbers before processing. Return a structured error response (HTTP 422) for invalid inputs rather than allowing exceptions to propagate.
