"""
Unit tests for user_service and order_service.

All database I/O is mocked via unittest.mock.patch so no real
sqlite3 connection is required.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Make the src package importable without an install step
# ---------------------------------------------------------------------------
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import order_service
import user_service


# ===========================================================================
# order_service tests
# ===========================================================================

class TestProcessOrder(unittest.TestCase):

    def test_basic_order_no_discount(self):
        data = {"item": "Widget", "qty": 1, "price": 10.0}
        result = order_service.process_order(data)
        self.assertEqual(result["item"], "Widget")
        self.assertEqual(result["qty"], 1)
        self.assertEqual(result["price"], 10.0)
        self.assertAlmostEqual(result["total"], 10.0)
        self.assertEqual(result["status"], "pending")

    def test_qty_over_50_applies_5pct_discount(self):
        data = {"item": "Gadget", "qty": 60, "price": 10.0}
        result = order_service.process_order(data)
        # 60 * 10.0 * 0.95 = 570
        self.assertAlmostEqual(result["total"], 570.0)

    def test_qty_over_100_applies_10pct_discount(self):
        data = {"item": "Gizmo", "qty": 101, "price": 5.0}
        result = order_service.process_order(data)
        # 101 * 5.0 * 0.9 = 454.5
        self.assertAlmostEqual(result["total"], 454.5)

    def test_qty_exactly_50_no_bulk_discount(self):
        """Boundary: qty == 50 is NOT > 50, so no discount."""
        data = {"item": "Part", "qty": 50, "price": 2.0}
        result = order_service.process_order(data)
        self.assertAlmostEqual(result["total"], 100.0)

    def test_qty_exactly_100_applies_5pct_discount(self):
        """Boundary: qty == 100 is NOT > 100, so 5 % discount applies."""
        data = {"item": "Part", "qty": 100, "price": 2.0}
        result = order_service.process_order(data)
        # 100 * 2.0 * 0.95 = 190
        self.assertAlmostEqual(result["total"], 190.0)

    def test_missing_key_raises_key_error(self):
        with self.assertRaises(KeyError):
            order_service.process_order({"item": "X", "qty": 1})  # no price


class TestProcessBulkOrder(unittest.TestCase):
    """process_bulk_order is a duplicate of process_order with status='bulk_pending'."""

    def test_basic_bulk_order(self):
        data = {"item": "Bulk Widget", "qty": 10, "price": 3.0}
        result = order_service.process_bulk_order(data)
        self.assertAlmostEqual(result["total"], 30.0)
        self.assertEqual(result["status"], "bulk_pending")

    def test_bulk_qty_over_50_discount(self):
        data = {"item": "Bulk Gadget", "qty": 75, "price": 4.0}
        result = order_service.process_bulk_order(data)
        # 75 * 4.0 * 0.95 = 285
        self.assertAlmostEqual(result["total"], 285.0)

    def test_bulk_qty_over_100_discount(self):
        data = {"item": "Bulk Gizmo", "qty": 200, "price": 1.0}
        result = order_service.process_bulk_order(data)
        # 200 * 1.0 * 0.9 = 180
        self.assertAlmostEqual(result["total"], 180.0)

    def test_bulk_missing_key_raises_key_error(self):
        with self.assertRaises(KeyError):
            order_service.process_bulk_order({"item": "X", "price": 1.0})  # no qty


class TestApplyDiscount(unittest.TestCase):

    def _base_order(self, total=100.0):
        return {"item": "Test", "qty": 1, "price": total, "total": total, "status": "pending"}

    def test_save10(self):
        order = self._base_order(100.0)
        result = order_service.apply_discount(order, "SAVE10")
        self.assertAlmostEqual(result["total"], 90.0)

    def test_save20(self):
        order = self._base_order(100.0)
        result = order_service.apply_discount(order, "SAVE20")
        self.assertAlmostEqual(result["total"], 80.0)

    def test_halfoff(self):
        order = self._base_order(200.0)
        result = order_service.apply_discount(order, "HALFOFF")
        self.assertAlmostEqual(result["total"], 100.0)

    def test_unknown_code_leaves_total_unchanged(self):
        order = self._base_order(100.0)
        result = order_service.apply_discount(order, "BOGUS")
        self.assertAlmostEqual(result["total"], 100.0)


class TestCancelOrder(unittest.TestCase):

    def test_cancel_returns_correct_payload(self):
        result = order_service.cancel_order("ORD-42", "customer request")
        self.assertEqual(result["order_id"], "ORD-42")
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(result["reason"], "customer request")

    def test_cancel_with_empty_reason(self):
        result = order_service.cancel_order("ORD-99", "")
        self.assertEqual(result["reason"], "")
        self.assertEqual(result["status"], "cancelled")


# ===========================================================================
# user_service tests
# ===========================================================================

class TestCalculateUserScore(unittest.TestCase):

    # --- activity_count <= 0 ---
    def test_zero_activity_returns_zero(self):
        self.assertEqual(user_service.calculate_user_score(0, 10, 2), 0)

    def test_negative_activity_returns_zero(self):
        self.assertEqual(user_service.calculate_user_score(-5, 10, 2), 0)

    # --- 0 < activity_count < 10 ---
    def test_low_range_no_bonus(self):
        # score = 5 * 3 = 15; bonus has no effect in this branch
        self.assertAlmostEqual(user_service.calculate_user_score(5, 100, 3), 15.0)

    def test_low_range_bonus_ignored(self):
        """Bonus is NOT applied when activity_count < 10."""
        score_no_bonus = user_service.calculate_user_score(5, 0, 3)
        score_with_bonus = user_service.calculate_user_score(5, 50, 3)
        self.assertEqual(score_no_bonus, score_with_bonus)

    # --- 10 <= activity_count < 50 ---
    def test_mid_range_no_bonus(self):
        # score = 20 * 2 * 1.5 = 60
        self.assertAlmostEqual(user_service.calculate_user_score(20, 0, 2), 60.0)

    def test_mid_range_with_bonus(self):
        # score = 20 * 2 * 1.5 + 10 * 2 = 60 + 20 = 80
        self.assertAlmostEqual(user_service.calculate_user_score(20, 10, 2), 80.0)

    # --- 50 <= activity_count < 100 ---
    def test_high_range_no_bonus(self):
        # score = 75 * 4 * 2 = 600
        self.assertAlmostEqual(user_service.calculate_user_score(75, 0, 4), 600.0)

    def test_high_range_with_bonus(self):
        # score = 75 * 4 * 2 + 5 * 3 = 600 + 15 = 615
        self.assertAlmostEqual(user_service.calculate_user_score(75, 5, 4), 615.0)

    # --- activity_count >= 100 ---
    def test_top_range_no_bonus(self):
        # score = 100 * 1 * 3 = 300
        self.assertAlmostEqual(user_service.calculate_user_score(100, 0, 1), 300.0)

    def test_top_range_with_bonus(self):
        # score = 100 * 1 * 3 + 7 * 5 = 300 + 35 = 335
        self.assertAlmostEqual(user_service.calculate_user_score(100, 7, 1), 335.0)


class TestGetUser(unittest.TestCase):
    """Mock sqlite3 so no real database is needed."""

    @patch("user_service.get_db_connection")
    def test_returns_row_when_found(self, mock_get_conn):
        fake_row = (1, "alice", "abc123hash", "alice@example.com")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = fake_row
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = user_service.get_user("alice")

        self.assertEqual(result, fake_row)
        mock_conn.close.assert_called_once()

    @patch("user_service.get_db_connection")
    def test_returns_none_when_not_found(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = user_service.get_user("ghost")

        self.assertIsNone(result)


class TestAuthenticateUser(unittest.TestCase):
    """Mock get_user to avoid any DB interaction."""

    @patch("user_service.get_user")
    def test_correct_password_returns_true(self, mock_get_user):
        import hashlib
        password = "secret"
        hashed = hashlib.md5(password.encode()).hexdigest()
        mock_get_user.return_value = (1, "bob", hashed, "bob@example.com")

        result = user_service.authenticate_user("bob", password)

        self.assertTrue(result)

    @patch("user_service.get_user")
    def test_wrong_password_returns_false(self, mock_get_user):
        import hashlib
        hashed = hashlib.md5("correct".encode()).hexdigest()
        mock_get_user.return_value = (1, "bob", hashed, "bob@example.com")

        result = user_service.authenticate_user("bob", "wrong_password")

        self.assertFalse(result)

    @patch("user_service.get_user")
    def test_user_not_found_returns_false(self, mock_get_user):
        mock_get_user.return_value = None

        result = user_service.authenticate_user("nobody", "pass")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
