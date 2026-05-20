import unittest
from choppa.rule_matcher import RuleMatcher, RegexRegionMatcher, rule_matches_at
from choppa.srx_parser import SrxDocument, Rule


class RuleMatcherTest(unittest.TestCase):
    def test_rule_matcher(self):
        document: SrxDocument = SrxDocument()
        rule: Rule = Rule(True, "ab+", "ca+")
        text: text = "abaabbcabcabcaa"
        matcher: RuleMatcher = RuleMatcher(document, rule, text)
        self.assertFalse(matcher.hit_end())
        self.assertTrue(matcher.find())
        self.assertFalse(matcher.hit_end())
        self.assertEqual(3, matcher.get_start_position())
        self.assertEqual(6, matcher.get_break_position())
        self.assertEqual(8, matcher.get_end_position())
        self.assertTrue(matcher.find())
        self.assertFalse(matcher.hit_end())
        self.assertEqual(7, matcher.get_start_position())
        self.assertEqual(9, matcher.get_break_position())
        self.assertEqual(11, matcher.get_end_position())
        self.assertTrue(matcher.find())
        self.assertFalse(matcher.hit_end())
        self.assertEqual(10, matcher.get_start_position())
        self.assertEqual(12, matcher.get_break_position())
        self.assertEqual(15, matcher.get_end_position())
        self.assertFalse(matcher.find())
        self.assertTrue(matcher.hit_end())
        self.assertTrue(matcher.find(6))
        self.assertEqual(7, matcher.get_start_position())
        self.assertEqual(9, matcher.get_break_position())
        self.assertEqual(11, matcher.get_end_position())

    def test_region_matcher_find(self):
        matcher: RegexRegionMatcher = RegexRegionMatcher(pattern=r"foo", text="foobarfoo")

        match = matcher.find()
        self.assertEqual(matcher.start, 0)
        self.assertEqual(matcher.end, 3)

        match = matcher.find()
        self.assertEqual(matcher.start, 6)
        self.assertEqual(matcher.end, 9)

        match = matcher.find()
        self.assertEqual(match, None)
        self.assertEqual(matcher._start, 9)
        self.assertEqual(matcher._end, 9)

    def test_region_matcher_looking_at(self):
        matcher: RegexRegionMatcher = RegexRegionMatcher(pattern=r"foo", text="foobarfoo")

        match = matcher.looking_at()
        self.assertEqual(matcher.start, 0)
        self.assertEqual(matcher.end, 3)

        match = matcher.looking_at()
        self.assertEqual(match, None)
        self.assertEqual(matcher._start, 3)
        self.assertEqual(matcher._end, 9)

        match = matcher.find()
        self.assertEqual(matcher.start, 6)
        self.assertEqual(matcher.end, 9)

    def test_region_matcher_empty(self):
        matcher: RegexRegionMatcher = RegexRegionMatcher(pattern=r"", text="123")

        match = matcher.find()
        self.assertEqual(matcher.start, 0)
        self.assertEqual(matcher.end, 0)

        match = matcher.find()
        self.assertEqual(matcher.start, 1)
        self.assertEqual(matcher.end, 1)

        match = matcher.find()
        self.assertEqual(matcher.start, 2)
        self.assertEqual(matcher.end, 2)

        match = matcher.find()
        self.assertEqual(matcher.start, 3)
        self.assertEqual(matcher.end, 3)

        match = matcher.find()
        self.assertEqual(match, None)

    def test_caret_matcher(self):
        matcher: RegexRegionMatcher = RegexRegionMatcher(pattern=r"^\d", text="123")

        match = matcher.find()
        self.assertEqual(matcher.start, 0)
        self.assertEqual(matcher.end, 1)

        match = matcher.find()
        self.assertEqual(matcher.start, 1)
        self.assertEqual(matcher.end, 2)

        match = matcher.find()
        self.assertEqual(matcher.start, 2)
        self.assertEqual(matcher.end, 3)

        match = matcher.find()
        self.assertEqual(match, None)

    def test_caret_alt_matcher(self):
        matcher: RegexRegionMatcher = RegexRegionMatcher(pattern=r"(^foo)|(bar)", text="foobarfoo")

        match = matcher.find()
        self.assertEqual(matcher.start, 0)
        self.assertEqual(matcher.end, 3)

        match = matcher.find()
        self.assertEqual(matcher.start, 3)
        self.assertEqual(matcher.end, 6)

        match = matcher.find()
        self.assertEqual(matcher.start, 6)
        self.assertEqual(matcher.end, 9)

        match = matcher.find()
        self.assertEqual(match, None)

    def test_rule_matches_at_boundary(self):
        document = SrxDocument()
        rule = Rule(False, r"[Pp]rof\.", r"\s")
        text = "12345 Prof. foobar"

        self.assertTrue(rule_matches_at(document, rule, text, 11))
        self.assertFalse(rule_matches_at(document, rule, text, 12))

    def test_rule_matches_at_boundary_after_long_prefix(self):
        document = SrxDocument()
        rule = Rule(False, r"[Pp]rof\.", r"\s")
        text = "".join("AAAAAAA " * 100) + "Prof. foobar"

        self.assertTrue(rule_matches_at(document, rule, text, 805))
        self.assertFalse(rule_matches_at(document, rule, text, 806))
