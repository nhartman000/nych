import unittest

from nych.addressing import extend_address, root_address
from nych.encoding import decode_sequence, encode_sequence
from nych.symbols import Symbol


class NychEncodingTests(unittest.TestCase):
    def test_extend_address_appends_dimension(self):
        base = root_address()
        extended = extend_address(base, 3.0)
        self.assertEqual(extended, (0.0, 0.0, 0.0, 0.0, 3.0))
        self.assertEqual(base, (0.0, 0.0, 0.0, 0.0))

    def test_encode_sequence_is_non_mutating_and_round_trips_glyphs(self):
        base = root_address()
        symbols = [
            Symbol("A", "alpha", base),
            Symbol("B", "beta", base),
        ]

        encoded = encode_sequence(symbols, base)

        self.assertEqual(encoded[0], ("A", (0.0, 0.0, 0.0, 0.0, 0.0)))
        self.assertEqual(encoded[1], ("B", (0.0, 0.0, 0.0, 0.0, 1.0)))
        self.assertEqual(decode_sequence(encoded), ["A", "B"])
        self.assertEqual(symbols[0].address, base)
        self.assertEqual(symbols[1].address, base)


if __name__ == "__main__":
    unittest.main()
