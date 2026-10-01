import tempfile
import unittest
from pathlib import Path

from nych.session_invariants import (
    MODALITY_OPERATORS,
    InvariantViolation,
    SessionInvariants,
)


class SessionInvariantTests(unittest.TestCase):
    def setUp(self):
        self.store = SessionInvariants()

    def test_pin_and_lookup(self):
        self.store.pin("pattern", "gestalt.ptrn")
        pin = self.store.lookup("pattern")
        self.assertEqual(pin["symbol_id"], "gestalt.ptrn")
        self.assertEqual(pin["tag"], "#temp-invariant")

    def test_lookup_is_case_insensitive(self):
        self.store.pin("Pattern", "gestalt.ptrn")
        self.assertIsNotNone(self.store.lookup("pattern"))

    def test_unmapped_word_returns_none_not_guess(self):
        self.assertIsNone(self.store.lookup("unmapped"))

    def test_identical_repin_is_idempotent(self):
        self.store.pin("pattern", "gestalt.ptrn")
        self.store.pin("pattern", "gestalt.ptrn")  # no raise
        self.assertEqual(self.store.lookup("pattern")["history"], [])

    def test_conflicting_repin_raises_without_force(self):
        self.store.pin("pattern", "gestalt.ptrn")
        with self.assertRaises(InvariantViolation):
            self.store.pin("pattern", "gestalt.other")

    def test_forced_repin_records_history(self):
        self.store.pin("pattern", "gestalt.ptrn")
        self.store.pin("pattern", "gestalt.other", force=True)
        pin = self.store.lookup("pattern")
        self.assertEqual(pin["symbol_id"], "gestalt.other")
        self.assertEqual(pin["history"][0]["symbol_id"], "gestalt.ptrn")

    def test_modality_operators_are_permanent(self):
        for op_id, glyph in MODALITY_OPERATORS.items():
            with self.assertRaises(InvariantViolation):
                self.store.pin(op_id, "gestalt.x")
            with self.assertRaises(InvariantViolation):
                self.store.pin(glyph, "gestalt.x")
            looked = self.store.lookup(op_id)
            self.assertEqual(looked["tag"], "permanent-invariant")
            self.assertEqual(looked["symbol_id"], glyph)

    def test_save_and_load_roundtrip(self):
        self.store.pin("pattern", "gestalt.ptrn")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pins.json"
            self.store.save(path)
            loaded = SessionInvariants.load(path)
        self.assertEqual(loaded.lookup("pattern")["symbol_id"], "gestalt.ptrn")
        self.assertEqual(loaded.pinned_words(), ["pattern"])


if __name__ == "__main__":
    unittest.main()
