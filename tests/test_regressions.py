import unittest
import regex as re
from choppa.rule_matcher import JavaMatcher
from choppa.srx_parser import SrxDocument

class RegressionTest(unittest.TestCase):
    def test_negated_character_class_not_broken(self):
        # This was broken by the naive ^ substitution
        matcher = JavaMatcher(pattern=r"[^a]", text="abc")
        
        # At position 0, "a" is skipped, should match "b"
        match = matcher.find()
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), "b")
        
    def test_anchoring_at_alternatives(self):
        # ^ at alternatives should also work with \G emulation
        matcher = JavaMatcher(pattern=r"(^foo)|(bar)", text="bar")
        match = matcher.find()
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), "bar")
        
        matcher.region(0)
        matcher = JavaMatcher(pattern=r"(^foo)|(bar)", text="foo")
        match = matcher.find()
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), "foo")

    def test_multiline_behavior_default_off(self):
        # Java's default is no multiline for SRX rules. 
        # But ^ should match at the start of the search (emulating Java's anchoring bounds).
        doc = SrxDocument()
        pattern = doc.compile(r"^foo")
        
        text = "abc\nfoo"
        
        # 1. Match at the exact start of search (pos=4)
        match_at_start = pattern.search(text, pos=4)
        self.assertIsNotNone(match_at_start, "Should match at search start because of \\G emulation")
        
        # 2. Match in the middle of search (pos=0)
        # Without re.M, ^foo should NOT match at pos 4 if search started at 0.
        match_from_zero = pattern.search(text, pos=0)
        self.assertIsNone(match_from_zero, "Should NOT match after newline if not in multiline mode and search started at 1")
        
        # 3. Check that it DOES match if we explicitly enable re.M
        pattern_m = doc.compile(r"^foo", flags=re.M | re.U | re.V1)
        match_m = pattern_m.search(text, pos=0)
        self.assertIsNotNone(match_m, "Should match after newline in multiline mode")

    def test_word_boundary_at_region_start(self):
        # Verify that \b works correctly at region start (my main fix)
        matcher = JavaMatcher(pattern=r"\bfoo", text="xfoo")
        matcher.region(1)
        match = matcher.match()
        # "x" is at 0. At pos 1, \b should NOT match because "x" is a word char.
        self.assertIsNone(match)
        
        matcher = JavaMatcher(pattern=r"\bfoo", text=" foo")
        matcher.region(1)
        match = matcher.match()
        # " " is at 0. At pos 1, \b SHOULD match because " " is NOT a word char.
        self.assertIsNotNone(match)

if __name__ == "__main__":
    unittest.main()
