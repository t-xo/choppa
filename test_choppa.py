import re
from pathlib import Path

from choppa.srx_parser import SrxDocument
from choppa.iterators import SrxTextIterator

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "choppa" / "test_resources"
OUTPUT_DIR = INPUT_DIR / "out"
RULESET = BASE_DIR / "choppa" / "segment.srx"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pattern = re.compile(r"^(?P<lang>[a-z]{2})_test_in\.txt$")


def process_file(input_file: Path, output_file: Path, document: SrxDocument, lang_rule: str):
    with input_file.open("r", encoding="utf-8") as fin, \
         output_file.open("w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            for segment in SrxTextIterator(document, lang_rule, line):
                fout.write(segment + "\n")


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"INPUT_DIR not found: {INPUT_DIR}")
    if not RULESET.exists():
        raise FileNotFoundError(f"RULESET not found: {RULESET}")

    document = SrxDocument(ruleset=str(RULESET))

    for file in INPUT_DIR.iterdir():
        if not file.is_file():
            continue

        match = pattern.match(file.name)
        if not match:
            continue

        lang_rule = match.group("lang")
        output_name = f"{lang_rule}_test_out.txt"
        output_path = OUTPUT_DIR / output_name

        process_file(file, output_path, document, lang_rule)

        print(f"Processed: {file.name} (lang={lang_rule}) -> {output_path}")


if __name__ == "__main__":
    main()