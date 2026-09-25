# Test Coverage Findings

## Functions With No Tests (before this task)

| Function | File | Notes |
|---|---|---|
| `process_order` | `order_service.py` | No tests for basic path, qty discount thresholds, or missing keys |
| `process_bulk_order` | `order_service.py` | Duplicate of `process_order`; no tests existed |
| `apply_discount` | `order_service.py` | No tests for any discount code (SAVE10, SAVE20, HALFOFF) or unknown code |
| `cancel_order` | `order_service.py` | No tests |
| `get_order_history` | `order_service.py` | Stub (returns `None`); not tested |
| `serialize_order` | `order_service.py` | No tests |
| `deserialize_order` | `order_service.py` | No tests |
| `get_user` | `user_service.py` | No tests; requires mocked DB |
| `authenticate_user` | `user_service.py` | No tests; depends on `get_user` |
| `calculate_user_score` | `user_service.py` | No tests for any activity_count branch |
| `calculate_admin_score` | `user_service.py` | Duplicate of `calculate_user_score`; no tests |
| `create_user` | `user_service.py` | No tests; requires mocked DB |
| `update_user_email` | `user_service.py` | No tests; requires mocked DB |
| `delete_user` | `user_service.py` | No tests; requires mocked DB |
| `get_all_users` | `user_service.py` | No tests; requires mocked DB |
| `run_report` | `user_service.py` | No tests; command injection risk |
| `load_user_preferences` | `user_service.py` | No tests; unsafe deserialization risk |
| `login` (Flask route) | `api.py` | No tests |
| `get_user_api` (Flask route) | `api.py` | No tests |
| `create_user_api` (Flask route) | `api.py` | No tests |
| `place_order` (Flask route) | `api.py` | No tests |
| `cancel_order_api` (Flask route) | `api.py` | No tests |
| `debug_info` (Flask route) | `api.py` | No tests |

---

## Generated Tests

**File:** `sample_app/tests/test_services.py`

### `TestProcessOrder`
- `test_basic_order_no_discount` — qty = 1, verifies item/qty/price/total/status fields
- `test_qty_over_50_applies_5pct_discount` — qty = 60, expects 5 % reduction
- `test_qty_over_100_applies_10pct_discount` — qty = 101, expects 10 % reduction
- `test_qty_exactly_50_no_bulk_discount` — boundary: qty = 50 is not > 50
- `test_qty_exactly_100_applies_5pct_discount` — boundary: qty = 100 is not > 100
- `test_missing_key_raises_key_error` — missing "price" key raises `KeyError`

### `TestProcessBulkOrder`
- `test_basic_bulk_order` — basic path, checks `status == "bulk_pending"`
- `test_bulk_qty_over_50_discount` — same 5 % threshold as `process_order`
- `test_bulk_qty_over_100_discount` — same 10 % threshold as `process_order`
- `test_bulk_missing_key_raises_key_error` — missing "qty" key raises `KeyError`

### `TestApplyDiscount`
- `test_save10` — SAVE10 code applies 10 % off
- `test_save20` — SAVE20 code applies 20 % off
- `test_halfoff` — HALFOFF code halves the total
- `test_unknown_code_leaves_total_unchanged` — unknown code has no effect

### `TestCancelOrder`
- `test_cancel_returns_correct_payload` — verifies order_id, status, reason
- `test_cancel_with_empty_reason` — empty reason string is preserved

### `TestCalculateUserScore`
- `test_zero_activity_returns_zero` — edge case: 0 activity
- `test_negative_activity_returns_zero` — edge case: negative activity
- `test_low_range_no_bonus` — 0 < count < 10, no bonus applied in branch
- `test_low_range_bonus_ignored` — confirms bonus is not applied when count < 10
- `test_mid_range_no_bonus` — 10 ≤ count < 50, bonus = 0
- `test_mid_range_with_bonus` — 10 ≤ count < 50, bonus > 0 adds `bonus * 2`
- `test_high_range_no_bonus` — 50 ≤ count < 100, bonus = 0
- `test_high_range_with_bonus` — 50 ≤ count < 100, bonus > 0 adds `bonus * 3`
- `test_top_range_no_bonus` — count ≥ 100, bonus = 0
- `test_top_range_with_bonus` — count ≥ 100, bonus > 0 adds `bonus * 5`

### `TestGetUser`
- `test_returns_row_when_found` — mocks `get_db_connection`; cursor returns a fake row
- `test_returns_none_when_not_found` — mocks cursor to return `None`

### `TestAuthenticateUser`
- `test_correct_password_returns_true` — mocks `get_user` with matching MD5 hash
- `test_wrong_password_returns_false` — mocks `get_user`; wrong password returns `False`
- `test_user_not_found_returns_false` — mocks `get_user` returning `None`
