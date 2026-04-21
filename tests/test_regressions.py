import unittest
import regex as re
from choppa.rule_matcher import JavaMatcher
from choppa.srx_parser import SrxDocument

class RegressionTest(unittest.TestCase):
    def test_negated_character_class_not_broken(self):
        matcher = JavaMatcher(pattern=r"[^a]", text="abc")

        match = matcher.find()
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), "b")
        
    def test_anchoring_at_alternatives(self):
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
        doc = SrxDocument()
        pattern = doc.compile(r"^foo")
        
        text = "abc\nfoo"

        match_at_start = pattern.search(text, pos=4)
        self.assertIsNotNone(match_at_start, "Should match at search start because of \\G emulation")

        match_from_zero = pattern.search(text, pos=0)
        self.assertIsNone(match_from_zero, "Should NOT match after newline if not in multiline mode and search started at 1")

        pattern_m = doc.compile(r"^foo", flags=re.M | re.U | re.V1)
        match_m = pattern_m.search(text, pos=0)
        self.assertIsNotNone(match_m, "Should match after newline in multiline mode")

    def test_word_boundary_at_region_start(self):
        matcher = JavaMatcher(pattern=r"\bfoo", text="xfoo")
        matcher.region(1)
        match = matcher.match()
        self.assertIsNone(match)
        
        matcher = JavaMatcher(pattern=r"\bfoo", text=" foo")
        matcher.region(1)
        match = matcher.match()
        self.assertIsNotNone(match)

if __name__ == "__main__":
    unittest.main()
