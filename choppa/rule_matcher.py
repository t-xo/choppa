import regex as re  # type: ignore
from typing import Union, Callable, Optional
from .srx_parser import SrxDocument
from .structures import Rule


class JavaMatcher:
    """
    Partial implementation of java's matcher class using python's regex module.
    It uses pos and endpos to respect regions while allowing lookaround context.
    """

    def __init__(self, pattern: Union[str, re.Regex], text: str, max_lookaround_len: int = 100) -> None:
        self._text: str = text
        self._text_len: int = len(self._text)
        self._start: int = 0
        self._end: int = self._text_len
        self.start: int = 0
        self.end: int = 0
        self.use_transparent_bounds = False
        self.max_lookaround_len = max_lookaround_len

        if isinstance(pattern, str):
            pattern = re.sub(r"(?<!\\)(?<=^|\||\()\^", r"(?:\\G|^)", pattern)
            self.pattern = re.compile(pattern, flags=re.M | re.U | re.V1)
        else:
            self.pattern = pattern

    def region(self, start: int, end: Optional[int] = None) -> None:
        self._start = start
        if end is None:
            self._end = self._text_len
        else:
            self._end = end

    def search(self) -> Optional[re.Match]:
        if self._start > self._text_len:
            return None

        match = self.pattern.search(self._text, pos=self._start, endpos=self._end)

        if match is not None:
            self.start = match.start()
            self.end = match.end()
            self._start = self.end + (1 if self.start == self.end else 0)

        return match

    def find(self) -> Optional[re.Match]:
        return self.search()

    def match(self) -> Optional[re.Match]:
        if self._start > self._text_len:
            return None

        match = self.pattern.match(self._text, pos=self._start, endpos=self._end)

        if match is not None:
            self.start = match.start()
            self.end = match.end()
            self._start = self.end + (1 if self.start == self.end else 0)

        return match

    def looking_at(self) -> Optional[re.Match]:
        return self.match()

    def __str__(self) -> str:
        return f"{self.pattern}: <{self._start}, {self._end}>"


class RuleMatcher:
    """
    Represents matcher finding subsequent occurrences of one rule.
    """

    def __init__(self, document: SrxDocument, rule: Rule, text: str, max_lookaround_len: int = 100) -> None:
        """
        Creates matcher.
        rule rule which will be searched in the text
        text text
        """

        self.document: SrxDocument = document
        self.rule: Rule = rule
        self.text: str = text
        self.text_len: int = len(text)
        self.before_pattern: re.Regex = document.compile(rule.before_pattern)
        self.after_pattern: re.Regex = document.compile(rule.after_pattern)
        self.before_matcher: JavaMatcher = JavaMatcher(
            self.before_pattern, self.text, max_lookaround_len=max_lookaround_len
        )
        self.after_matcher: JavaMatcher = JavaMatcher(
            self.after_pattern, self.text, max_lookaround_len=max_lookaround_len
        )
        self.found = True

    def find(self, start: Optional[int] = None) -> bool:
        """
        Finds next rule match after previously found or from a given start position.
        """

        if start is not None:
            self.before_matcher.region(start)

        self.found = False

        while not self.found and self.before_matcher.search():
            self.after_matcher.region(self.before_matcher.end)
            self.found = self.after_matcher.looking_at() is not None

        return self.found

    def hit_end(self) -> bool:
        """
        @return true if end of text has been reached while searching
        """
        return not self.found

    def get_start_position(self) -> int:
        """
        @return position in text where the last matching starts
        """

        return self.before_matcher.start

    def get_break_position(self) -> int:
        """
        @return position in text where text should be splitted according to last matching
        """
        return self.after_matcher.start

    def get_end_position(self) -> int:
        """
        @return position in text where the last matching ends
        """
        return self.after_matcher.end

    def __str__(self) -> str:
        return f"{self.before_matcher}: {self.after_matcher}"

