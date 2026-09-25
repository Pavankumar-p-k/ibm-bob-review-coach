# Code Quality Review Findings

## HIGH

### QUA-001: Duplicate Logic — `calculate_user_score` and `calculate_admin_score` are identical
- **File:** `src/user_service.py` lines 80–118
- **Issue:** `calculate_admin_score` (lines 100–118) is a verbatim copy of `calculate_user_score` (lines 80–98). The two functions share the same signature, the same branching tree, and the same arithmetic — the only difference is the function name. Any future change to the scoring algorithm must be applied twice, making divergence inevitable.
- **Fix:** Delete `calculate_admin_score` and replace all call sites with `calculate_user_score`. If admin scoring ever needs to differ, introduce a `role` parameter or a small multiplier table instead of duplicating the entire function body.

---

### QUA-002: Duplicate Logic — `process_order` and `process_bulk_order` share copy-pasted body
- **File:** `src/order_service.py` lines 7–49
- **Issue:** `process_bulk_order` (lines 29–49) duplicates the entire body of `process_order` (lines 7–27). The only difference between the two is the `status` field value (`"pending"` vs `"bulk_pending"`). The discount/tier logic (lines 14–17) is copy-pasted in full.
- **Fix:** Extract a private helper `_calculate_order(order_data, status)` that takes a `status` argument. Both public functions become one-liners that call the helper with the appropriate status string, eliminating the duplication entirely.

---

### QUA-003: High Complexity — `calculate_user_score` has deeply nested conditionals
- **File:** `src/user_service.py` lines 80–98
- **Issue:** The function contains four levels of nesting (function body → `if activity_count > 0` → `if/elif/elif/else` tiers → inner `if bonus`). The repeated `if bonus: score = score + (bonus * N)` pattern inside each tier makes the logic hard to follow and test independently.
- **Fix:** Flatten the tier selection using a lookup table (list of `(threshold, rate_multiplier, bonus_multiplier)` tuples) and apply the bonus in a single post-calculation step, reducing cyclomatic complexity from ~8 to ~3.

---

### QUA-004: SRP Violation — `create_user` mixes password hashing, SQL construction, and DB I/O
- **File:** `src/user_service.py` lines 43–53
- **Issue:** `create_user` is responsible for (1) hashing the password, (2) building a raw SQL string, and (3) managing a database connection and transaction — three distinct concerns in one function. This makes unit-testing the hashing step impossible without a live database.
- **Fix:** Extract password hashing into a dedicated `hash_password(password)` helper. Separate connection management into a context manager or a dedicated repository class, leaving `create_user` to orchestrate only high-level steps.

---

### QUA-005: SRP Violation — `api.py` debug endpoint exposes live credentials inline
- **File:** `src/api.py` lines 50–57
- **Issue:** The `/debug` endpoint hard-codes the same credential strings (`"s3cr3tP@ssw0rd123"`, `"sk-prod-abc123XYZ789hardcoded"`) that are already declared as module-level constants in `user_service.py`, introducing a second source-of-truth that can drift. The route also has no authentication guard, meaning any caller receives plaintext secrets.
- **Fix:** Remove the `/debug` endpoint entirely for production builds. If a debug route is genuinely needed, gate it behind an `app.debug` flag, import the constants from the source module rather than re-typing them, and return only non-sensitive diagnostic information.

---

## MEDIUM

### QUA-006: Magic Numbers — discount multipliers in `apply_discount` are unexplained literals
- **File:** `src/order_service.py` lines 60–68
- **Issue:** The multipliers `0.90`, `0.80`, and `0.50` appear inline with no named constant or comment explaining that they represent "10 % off", "20 % off", and "50 % off" respectively. A future maintainer changing `SAVE10` to give 15 % off would need to know that `0.90` = 1 − 0.10.
- **Fix:** Replace each literal with a named constant or compute it as `1 - discount_rate`. For example: `DISCOUNT_RATES = {"SAVE10": 0.10, "SAVE20": 0.20, "HALFOFF": 0.50}` and apply as `order["total"] *= (1 - DISCOUNT_RATES[discount_code])`.

---

### QUA-007: Magic Numbers — order-quantity discount thresholds in `process_order` / `process_bulk_order`
- **File:** `src/order_service.py` lines 14–17 and 35–39
- **Issue:** The threshold values `100` and `50` (bulk quantity tiers) and the multipliers `0.9` / `0.95` are bare literals with no symbolic name. Combined with the duplication noted in QUA-002, these numbers appear four times in the file.
- **Fix:** Define module-level constants such as `BULK_TIER_LARGE = 100`, `BULK_TIER_MEDIUM = 50`, `DISCOUNT_LARGE = 0.90`, `DISCOUNT_MEDIUM = 0.95` and reference them consistently.

---

### QUA-008: Dead Code — `get_order_history` is a stub that always returns `None`
- **File:** `src/order_service.py` lines 56–58
- **Issue:** `get_order_history` contains only `pass`, meaning it silently returns `None` on every call. Any caller that treats the return value as a list will receive a `TypeError` at runtime with no indication of why. There is no `TODO`, `raise NotImplementedError`, or similar marker.
- **Fix:** Replace `pass` with `raise NotImplementedError("get_order_history is not yet implemented")` so failures are explicit. Add a tracking ticket reference if work is planned.

---

### QUA-009: Missing Error Handling — `process_order` / `process_bulk_order` do bare dict key access
- **File:** `src/order_service.py` lines 9–11 and 31–33
- **Issue:** Both functions access `order_data["item"]`, `order_data["qty"]`, and `order_data["price"]` without any guard. A missing key raises an unhandled `KeyError` that propagates to the caller with no informative message.
- **Fix:** Use `order_data.get(key)` with an explicit check, or validate with a schema library (e.g. `pydantic` or `marshmallow`) at the API boundary before the data reaches service functions.

---

### QUA-010: Missing Error Handling — `create_user_api` does bare dict key access on unvalidated JSON
- **File:** `src/api.py` lines 31–34
- **Issue:** `data["username"]`, `data["password"]`, and `data["email"]` will raise `KeyError` or `TypeError` if the client sends incomplete JSON or a non-object body. There is no `try/except`, no schema validation, and no HTTP 400 response path.
- **Fix:** Call `data.get(key)` for each field and return a `400 Bad Request` with a descriptive message if any required field is absent. Centralise validation using a Flask request schema decorator or a `marshmallow` schema.

---

### QUA-011: Inconsistent Naming — mix of `user_id` (int) and `username` (str) as identifiers across functions
- **File:** `src/user_service.py` lines 16, 55, 65; `src/api.py` lines 20–27
- **Issue:** `get_user` accepts a `username` string, `update_user_email` and `delete_user` accept a numeric `user_id`, and the API layer calls `get_user(username)` but never exposes update/delete. The project has no consistent primary-key convention — some paths use the natural key, others use the surrogate key, with no adapter layer.
- **Fix:** Establish a single convention (prefer surrogate `user_id` for internal service calls, resolve `username → id` at the API boundary) and rename parameters consistently across all three files.

---

### QUA-012: Inconsistent Patterns — DB connection lifecycle differs between functions
- **File:** `src/user_service.py` lines 12–78
- **Issue:** Every database function independently calls `get_db_connection()`, creates a cursor, and calls `conn.close()` in the happy path — but none of them use a `try/finally` or context manager. If an exception is raised between `get_db_connection()` and `conn.close()`, the connection leaks. `delete_user` (line 65) is the only function that uses a parameterised query.
- **Fix:** Replace the manual open/close pattern with a `with get_db_connection() as conn:` context manager (or a `contextlib.closing` wrapper), ensuring connections are always released even on exception.

---

## LOW

### QUA-013: Magic Number — hardcoded port `5000` in `app.run`
- **File:** `src/api.py` line 61
- **Issue:** The port number `5000` is a bare literal. In environments where the port is already in use, the only fix is to change the source file.
- **Fix:** Read the port from an environment variable: `port = int(os.environ.get("PORT", 5000))` and pass it to `app.run`.

---

### QUA-014: Dead / Unused Import — `os` imported but never used in `user_service.py`
- **File:** `src/user_service.py` line 4
- **Issue:** `import os` is present at the top of the file but `os` is never referenced anywhere in the module. This adds noise and can confuse readers into thinking `os` is used for something (e.g. environment variable access for the hard-coded secrets).
- **Fix:** Remove the `import os` line. If environment-variable-based secrets are introduced later, re-add it at that point.

---

### QUA-015: Inconsistent Return Style — `authenticate_user` returns `True`/`False` but callers check truthiness of raw DB rows elsewhere
- **File:** `src/user_service.py` lines 26–33; `src/api.py` lines 16, 23–24
- **Issue:** `authenticate_user` returns a boolean, but `get_user` returns a raw database row tuple (or `None`). The API layer checks `if user:` on the tuple (line 24 of `api.py`), which relies on Python's truthiness of non-empty tuples. This inconsistency — sometimes a boolean, sometimes a truthy row — makes the contract of each function non-obvious.
- **Fix:** Define a `User` dataclass or typed dict and return it (or `None`) from `get_user`, making the type contract explicit. Update `authenticate_user` to accept and return consistent types. Document return types with type annotations throughout.
