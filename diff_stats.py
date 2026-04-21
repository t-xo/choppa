import difflib
from pathlib import Path

EXPECTED_DIR = Path(__file__).parent / "test_resources"
OUTPUT_DIR = EXPECTED_DIR / "out"

pattern = "_test_expected.txt"

def count_diffs(expected, actual):
    plus, minus = 0, 0
    diff = difflib.ndiff(expected, actual)
    for line in diff:
        if line.startswith('+ '):
            plus += 1
        elif line.startswith('- '):
            minus += 1
    return plus, minus

def main():
    stats = []
    for expected_file in EXPECTED_DIR.glob(f"*{pattern}"):
        lang = expected_file.name.split('_')[0]
        output_file = OUTPUT_DIR / f"{lang}_test_out.txt"
        if not output_file.exists():
            print(f"Missing output for {lang}")
            continue
        with expected_file.open(encoding="utf-8") as f:
            expected_lines = [line.rstrip() for line in f]
        with output_file.open(encoding="utf-8") as f:
            actual_lines = [line.rstrip() for line in f]
        plus, minus = count_diffs(expected_lines, actual_lines)
        stats.append((lang, plus, minus))
        print(f"{lang}: +{plus} -{minus}")
    print("\nSummary:")
    for lang, plus, minus in stats:
        print(f"{lang}: +{plus} -{minus}")

if __name__ == "__main__":
    main()
