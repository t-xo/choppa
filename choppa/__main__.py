import sys
import argparse
from pathlib import Path
from typing import Optional

from choppa.srx_parser import SrxDocument
from choppa.iterators import SrxTextIterator, FastTextIterator


DEFAULT_RULESET = Path(__file__).parent / "data/srx/languagetool_segment.srx"
SRX_2_XSD = Path(__file__).parent / "data/xsd/srx20.xsd"

def main():
    parser = argparse.ArgumentParser(description="Choppa - SRX-based sentence tokenizer")
    parser.add_argument("-s", "--srx", type=Path, default=DEFAULT_RULESET, help="Path to SRX file")
    parser.add_argument("-l", "--lang", type=str, default="uk_two", help="Language code (e.g., en, uk_two)")
    parser.add_argument("-f", "--fast", action="store_true", help="Use FastTextIterator instead of standard one")
    parser.add_argument("-v", "--validate", action="store_true", help="Validate SRX against XSD")
    parser.add_argument("input", nargs="?", type=argparse.FileType("r", encoding="utf-8"), default=sys.stdin, help="Input file (default: stdin)")

    args = parser.parse_args()

    validate_path = SRX_2_XSD if args.validate else None
    
    try:
        document = SrxDocument(ruleset=args.srx, validate_ruleset=validate_path)
    except Exception as e:
        print(f"Error loading SRX: {e}", file=sys.stderr)
        sys.exit(1)

    iterator_class = FastTextIterator if args.fast else SrxTextIterator

    if args.input.isatty():
        print(f"Reading from stdin (Language: {args.lang}, Iterator: {iterator_class.__name__})...", file=sys.stderr)

    for line in args.input:
        line = line.strip()
        if not line:
            continue
        for segment in iterator_class(document, args.lang, line):
            print(segment)

if __name__ == "__main__":
    main()
