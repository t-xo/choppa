# choppa
Python SRX segmenter compatible with Okapi SRX regular expressions.

In a nutshell, it allows you to tokenize texts into sentences (but generally, it's rule-based so that you can chop anything textual).

Shipped with `segment.srx` set of segmentation rules for different languages, crafted by the team of [languagetool](https://github.com/languagetool-org/languagetool).

# Quick Start

```bash
pip3 install git+https://github.com/lang-uk/choppa.git

cat << EOF | python3 -m choppa
Жоден сучасний електронний прилад не обходиться без мікрочипів. Мікрочіп, інакше кажучи, мікросхема - це набір електронних схем на невеликому плоскому шматку кремнію.
EOF
```

See [choppa/__main__.py](choppa/__main__.py) for a Python usage example.

## Iterator choices

Use `LargeFileSrxTextIterator` for one very large file. It accepts a path or an
open text reader and streams through a fixed-size buffer, so the whole file does
not need to live in memory.

```python
from choppa import LargeFileSrxTextIterator, SrxDocument

document = SrxDocument(ruleset="segment.srx")

with LargeFileSrxTextIterator(document, "en", "huge.txt") as segments:
    for segment in segments:
        print(segment)
```

Use `ManyFilesSrxTextIterator` for a very large batch of smaller files. It reads
one file at a time, releases it, and keeps the parsed SRX document and compiled
regex cache warm for the entire batch.

```python
from pathlib import Path
from choppa import ManyFilesSrxTextIterator, SrxDocument

document = SrxDocument(ruleset="segment.srx")
files = Path("corpus").glob("*.txt")

for source, segment in ManyFilesSrxTextIterator(document, "en", files, include_source=True):
    print(source, segment)
```

The command line can stream a whole file as one document:

```bash
python -m choppa --whole-file --lang en huge.txt
```

# Current status and plans
That port currently covers:
* All structures (`structures.py`) necessary for the parser to operate (`Rule`, `LanguageRule`, `LanguageMap`)
* Abstract, Accurate (legacy), SrxTextIterator, LargeFileSrxTextIterator, and ManyFilesSrxTextIterator (`iterators.py`), which segment text into chunks according to the SRX rules
* Extra classes required for the SrxTextIterator (`TextManager`, `RuleManager`)
* Some utils (`utils.py`), for regex mangling
* SAX based parser (`srx_parser.py`) to read SRX rules from xml files ([**SRX2.0 only**](https://github.com/loomchild/segment#srx-file))
* SrxDocument (again `srx_parser.py`) class which allows you to manage rules and cache regexes
* A region-aware regex matcher used by the SRX iterators.
* Tests for everything above (and beyond)
* Additional tokenizer tests from LanguageTool for Ukrainian language
* [Type hints](https://docs.python.org/3/library/typing.html)

I also _pythonized_ the code to some extent (by removing some setters/getters, _snake_casing_ methods, and variables and adapting data structures).


# Important notes

Please pay attention to the fact that only Accurate and SrxTextIterator-style iterators are currently implemented. Accurate Iterator should work well on relatively small documents (i.e. **do not use** it on multi GB plaintext corpora!). SrxTextIterator supports streaming input and evaluates SRX break and exception rules directly at candidate boundaries. If you need other iterators or are keen to optimize that beast — I'm always open for the pull requests. Similarly, I've only implemented SAX reader for rules and I'm using `xmlschema` package for schema validation.

Also, I don't have any plan of porting UI at all. You can reuse some of UI's available.
