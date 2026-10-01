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

    def test_operator_glyph_cannot_be_given_to_another_word(self):
        for glyph in MODALITY_OPERATORS.values():
            with self.assertRaises(InvariantViolation):
                self.store.pin("whirlygig", glyph)
            with self.assertRaises(InvariantViolation):
                self.store.pin("whirlygig", f"gestalt.whrlyg{glyph}")

    def test_operator_glyph_without_variation_selector_still_caught(self):
        with self.assertRaises(InvariantViolation):
            self.store.pin("whirlygig", "\U0001F5EF")  # 🗯 without U+FE0F

    def test_as_dict_snapshot_does_not_leak_into_store(self):
        self.store.pin("pattern", "gestalt.ptrn")
        snap = self.store.as_dict()
        snap["pins"]["pattern"]["symbol_id"] = "TAMPERED"
        snap["pins"]["pattern"]["history"].append({"symbol_id": "x"})
        pin = self.store.lookup("pattern")
        self.assertEqual(pin["symbol_id"], "gestalt.ptrn")
        self.assertEqual(pin["history"], [])

    def test_load_rejects_hand_edited_operator_glyph(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pins.json"
            path.write_text('{"pins": {"test": {"word": "test", '
                            '"symbol_id": "\\ud83d\\udc40", "source": "llm", '
                            '"tag": "#temp-invariant", "history": []}}}',
                            encoding="utf-8")
            with self.assertRaises(InvariantViolation):
                SessionInvariants.load(path)

    def test_load_rejects_hand_edited_operator_remap(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pins.json"
            path.write_text('{"pins": {"execute": {"word": "execute", '
                            '"symbol_id": "gestalt.x", "source": "llm", '
                            '"tag": "#temp-invariant", "history": []}}}',
                            encoding="utf-8")
            with self.assertRaises(InvariantViolation):
                SessionInvariants.load(path)


if __name__ == "__main__":
    unittest.main()
