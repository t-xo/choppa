import difflib
from pathlib import Path
import unittest

from choppa.iterators import SrxTextIterator
from choppa.srx_parser import SrxDocument


def count_diffs(expected, actual):
    plus = 0
    minus = 0
    for line in difflib.ndiff(expected, actual):
        if line.startswith("+ "):
            plus += 1
        elif line.startswith("- "):
            minus += 1
    return plus, minus


class CorpusParityTest(unittest.TestCase):
    def test_test_resources_match_expected(self):
        repo_root = Path(__file__).resolve().parents[1]
        resource_dir = repo_root / "test_resources"
        ruleset = repo_root / "segment.srx"
        document = SrxDocument(ruleset=str(ruleset))

        for input_file in sorted(resource_dir.glob("*_test_in.txt")):
            lang = input_file.name.split("_")[0]
            expected_file = resource_dir / f"{lang}_test_expected.txt"
            expected = [line.rstrip() for line in expected_file.read_text(encoding="utf-8").splitlines()]
            actual = []
            for raw_line in input_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                actual.extend(list(SrxTextIterator(document, lang, line)))
            actual = [line.rstrip() for line in actual]

            plus, minus = count_diffs(expected, actual)
            self.assertEqual(
                expected,
                actual,
                msg=f"{lang} mismatch (+{plus} -{minus})",
            )

