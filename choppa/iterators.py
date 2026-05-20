import io
from os import PathLike
from typing import Any, Iterable, List, Tuple, Union, Optional

from .structures import LanguageRule
from .srx_parser import SrxDocument
from .rule_matcher import RuleMatcher, rule_matches_at
from .text_manager import TextManager
from .rule_manager import RuleManager


MAX_INT_VALUE: int = 2 ** 31 - 1


class AbstractTextIterator:
    """
    Represents abstract text iterator. Responsible for implementing remove
    operation.
    """

    DEFAULT_BUFFER_LENGTH: int = 1024 * 1024
    DEFAULT_MAX_BOUNDARY_CONTEXT_LENGTH: int = 100

    def to_string(self, language_rule_list: List[LanguageRule]) -> str:
        result = []

        for language_rule in language_rule_list:
            result.append(language_rule.name)

        return "".join(result)

    def __iter__(self):
        return self

    def __next__(self) -> str:
        raise StopIteration


class AccurateSrxTextIterator(AbstractTextIterator):
    def __init__(
        self,
        document: SrxDocument,
        language_code: str,
        text: str,
        max_boundary_context_length: int = AbstractTextIterator.DEFAULT_MAX_BOUNDARY_CONTEXT_LENGTH,
    ) -> None:
        """
        Legacy alert: this is the implementation of the legacy accurate iterator
        from the original segment package. It's been known for slow speed on a large
        texts and doesn't allow to work on streams. Use SrxTextIterator instead

        Creates text iterator that obtains language rules form given document
        using given language code. To retrieve language rules calls
        SrxDocument.getLanguageRuleList(String).

        document document containing language rules
        language_code language code to select the rules
        text
        """

        self.language_rule_list: List[LanguageRule] = document.get_language_rule_list(language_code)
        self.text: str = text
        self.segment: Optional[str] = None
        self.start_position: int = 0
        self.end_position: int = 0

        self.document = document
        self.rule_manager: RuleManager = self.document.get_rule_manager(
            self.language_rule_list, max_boundary_context_length
        )
        self.rule_matcher_list: List[RuleMatcher] = []
        self._boundary_cache = {}

    def __next__(self) -> str:
        """
        Finds the next match.
        Returns the next segment, or null if it does not exist
        """

        if self.has_next():
            if self.segment is None:
                self.init_matchers()

            found: bool = False

            while len(self.rule_matcher_list) and not found:
                min_matcher: RuleMatcher = self.get_min_matcher()
                self.end_position = min_matcher.get_break_position()
                if self.end_position > self.start_position:
                    found = self.is_exception(min_matcher)
                    if found:
                        self.cut_matchers()

                self.move_matchers()

            if not found:
                self.end_position = len(self.text)

            self.segment = self.text[self.start_position : self.end_position]
            self.start_position = self.end_position

            return self.segment
        else:
            raise StopIteration

    def has_next(self) -> bool:
        """
        Returns true when more segments are available
        """
        return self.start_position < len(self.text)

    def init_matchers(self) -> None:
        self.rule_matcher_list = []
        for rule in self.rule_manager.break_rule_list:
            matcher = RuleMatcher(document=self.document, rule=rule, text=self.text)
            self.rule_matcher_list.append(matcher)

        for matcher in self.rule_matcher_list[:]:
            matcher.find()
            if matcher.hit_end():
                self.rule_matcher_list.remove(matcher)

    def move_matchers(self) -> None:
        """
        Moves iterators to the next position if necessary.

        """
        for matcher in self.rule_matcher_list[:]:
            while matcher.get_break_position() <= self.end_position:
                matcher.find()
                if matcher.hit_end():
                    self.rule_matcher_list.remove(matcher)
                    break

    def cut_matchers(self) -> None:
        """
        Move matchers that start before previous segment end.
        """

        for matcher in self.rule_matcher_list[:]:
            if matcher.get_start_position() < self.end_position:
                matcher.find(self.end_position)
                if matcher.hit_end():
                    self.rule_matcher_list.remove(matcher)

    def get_min_matcher(self) -> Optional[RuleMatcher]:
        """
        Returns an iterator of the first match hit
        """

        min_position: int = MAX_INT_VALUE
        min_matcher: Optional[RuleMatcher] = None
        for matcher in self.rule_matcher_list:
            if matcher.get_break_position() < min_position:
                min_position = matcher.get_break_position()
                min_matcher = matcher
        return min_matcher

    def is_exception(self, rule_matcher: RuleMatcher) -> bool:
        for rule in self.rule_manager.get_exception_rules(rule_matcher.rule):
            if rule_matches_at(self.document, rule, self.text, rule_matcher.get_break_position(), self._boundary_cache):
                return False
        return True


class FastTextIterator(AccurateSrxTextIterator):
    """
    Backward-compatible iterator name that uses direct SRX boundary matching.
    """

    def __init__(
        self,
        document: SrxDocument,
        language_code: str,
        text: str,
        max_boundary_context_length: int = AbstractTextIterator.DEFAULT_MAX_BOUNDARY_CONTEXT_LENGTH,
        default_pattern_flags: int = 0,
    ) -> None:
        self.default_pattern_flags = default_pattern_flags
        super().__init__(document, language_code, text, max_boundary_context_length)


class LargeFileSrxTextIterator(AbstractTextIterator):
    """
    Iterator optimized for one very large input file.

    It opens path-like sources lazily and delegates segmentation to
    SrxTextIterator's buffered reader path, so the full file does not need to be
    loaded into memory.
    """

    DEFAULT_BUFFER_LENGTH: int = 8 * 1024 * 1024
    DEFAULT_MARGIN: int = 8 * 1024

    def __init__(
        self,
        document: SrxDocument,
        language_code: str,
        source: Union[str, PathLike, io.TextIOBase],
        encoding: str = "utf-8",
        buffer_length: int = DEFAULT_BUFFER_LENGTH,
        margin: int = DEFAULT_MARGIN,
        max_boundary_context_length: int = AbstractTextIterator.DEFAULT_MAX_BOUNDARY_CONTEXT_LENGTH,
        default_pattern_flags: int = 0,
    ) -> None:
        if buffer_length <= margin:
            raise ValueError("buffer_length must be larger than margin.")

        self._owns_reader = isinstance(source, (str, PathLike))
        self._reader = (
            open(source, "r", encoding=encoding)
            if self._owns_reader
            else source
        )
        self._iterator = SrxTextIterator(
            document=document,
            language_code=language_code,
            text=self._reader,
            buffer_length=buffer_length,
            max_boundary_context_length=max_boundary_context_length,
            margin=margin,
            default_pattern_flags=default_pattern_flags,
        )

    def __next__(self) -> str:
        try:
            return next(self._iterator)
        except StopIteration:
            self.close()
            raise

    def has_next(self) -> bool:
        return self._iterator.has_next()

    def close(self) -> None:
        if self._owns_reader and not self._reader.closed:
            self._reader.close()

    def __enter__(self) -> "LargeFileSrxTextIterator":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class ManyFilesSrxTextIterator(AbstractTextIterator):
    """
    Iterator optimized for very large batches of smaller files.

    Each file is read and segmented independently, then released before the next
    file is loaded. The supplied SrxDocument is reused for the entire batch, so
    compiled SRX patterns and rule managers stay cached across files.
    """

    def __init__(
        self,
        document: SrxDocument,
        language_code: str,
        sources: Iterable[Union[str, PathLike, io.TextIOBase, Tuple[Any, str]]],
        encoding: str = "utf-8",
        include_source: bool = False,
        skip_empty: bool = True,
        max_boundary_context_length: int = AbstractTextIterator.DEFAULT_MAX_BOUNDARY_CONTEXT_LENGTH,
    ) -> None:
        self.document = document
        self.language_code = language_code
        self.sources = iter(sources)
        self.encoding = encoding
        self.include_source = include_source
        self.skip_empty = skip_empty
        self.max_boundary_context_length = max_boundary_context_length
        self._source_index = 0
        self._current_source: Any = None
        self._current_iterator: Optional[AccurateSrxTextIterator] = None

    def __next__(self):
        while True:
            if self._current_iterator is not None:
                try:
                    segment = next(self._current_iterator)
                    if self.include_source:
                        return self._current_source, segment
                    return segment
                except StopIteration:
                    self._current_iterator = None
                    self._current_source = None

            self._load_next_source()

    def _load_next_source(self) -> None:
        while True:
            source = next(self.sources)
            self._source_index += 1
            source_id, text = self._read_source(source)

            if text or not self.skip_empty:
                self._current_source = source_id
                self._current_iterator = AccurateSrxTextIterator(
                    self.document,
                    self.language_code,
                    text,
                    self.max_boundary_context_length,
                )
                return

    def _read_source(
        self,
        source: Union[str, PathLike, io.TextIOBase, Tuple[Any, str]],
    ) -> Tuple[Any, str]:
        if isinstance(source, tuple):
            source_id, text = source
            return source_id, text

        if isinstance(source, (str, PathLike)):
            with open(source, "r", encoding=self.encoding) as reader:
                return source, reader.read()

        source_id = getattr(source, "name", self._source_index)
        return source_id, source.read()


class SrxTextIterator(AbstractTextIterator):
    """
    Represents text iterator splitting text according to rules in SRX file.

    The algorithm idea is as follows:

    <pre>
    1. Rule matcher list is created based on SRX file and language. Each rule
       matcher is responsible for matching before break and after break regular
       expressions of one break rule.
    2. Each rule matcher is matched to the text. If the rule was not found the
       rule matcher is removed from the list.
    3. First rule matcher in terms of its break position in text is selected.
    4. List of exception rules corresponding to break rule is retrieved.
    5. If none of exception rules is matching in break position then
       the text is marked as split and new segment is created. In addition
       all rule matchers are moved so they start after the end of new segment
       (which is the same as break position of the matched rule).
    6. All the rules that have break position behind last matched rule
       break position are moved until they pass it.
    7. If segment was not found the whole process is repeated.
    </pre>

    In streaming version of this algorithm character buffer is searched.
    When the end of it is reached or break position is in the margin
    (break position &gt; buffer size - margin) and there is more text,
    the buffer is moved in the text until it starts after last found segment.
    If this happens rule matchers are reinitialized and the text is searched again.
    Streaming version has a limitation that read buffer must be at least as long
    as any segment in the text.

    The Python implementation checks SRX exception rules at candidate
    boundaries directly.

    @author loomchild, Dmytro Chaplynskyi
    """

    DEFAULT_MARGIN: int = 128

    def __init__(
        self,
        document: SrxDocument,
        language_code: str,
        text: Union[str, io.TextIOBase],
        buffer_length: int = AbstractTextIterator.DEFAULT_BUFFER_LENGTH,
        max_boundary_context_length: int = AbstractTextIterator.DEFAULT_MAX_BOUNDARY_CONTEXT_LENGTH,
        margin: int = DEFAULT_MARGIN,
        default_pattern_flags: int = 0,
    ) -> None:
        """
        Creates text iterator that obtains language rules from given document
        using given language code. This is streaming constructor - it reads
        text from reader using buffer with given size and margin. Single
        segment cannot be longer than buffer size.
        If rule is matched but its position is in the margin
        (position &gt; buffer_length - margin) then the matching is ignored,
        and more text is read and rule is matched again.
        This is needed because incomplete rule can be located at the end of the
        buffer and never matched.
        """

        self.buffer_length: int = buffer_length
        self.max_boundary_context_length: int = max_boundary_context_length
        self.margin: int = margin

        if buffer_length > 0 and buffer_length <= margin:
            raise ValueError(
                f"Margin: {margin} must be smaller than buffer itself: {buffer_length}."
            )

        if isinstance(text, str):
            self.text_manager: TextManager = TextManager(text=text)
            self.margin = 0
        else:
            self.text_manager = TextManager(reader=text, buffer_length=buffer_length)
            self.margin = margin

        self.document: SrxDocument = document
        self.language_rule_list: List[LanguageRule] = document.get_language_rule_list(language_code)
        self.segment: Optional[str] = None
        self.start_position: int = 0
        self.end_position: int = 0
        self.rule_manager: RuleManager = self.document.get_rule_manager(
            self.language_rule_list, self.max_boundary_context_length
        )
        self.default_pattern_flags: int = default_pattern_flags
        self._boundary_cache = {}

    def init_matchers(self) -> None:

        self.rule_matcher_list: List[RuleMatcher] = []
        for rule in self.rule_manager.break_rule_list:
            matcher: RuleMatcher = RuleMatcher(
                document=self.document,
                rule=rule,
                text=self.text_manager.get_text(),
            )
            matcher.find()
            if not matcher.hit_end():
                self.rule_matcher_list.append(matcher)

    def move_matchers(self) -> None:
        """
        Moves iterators to the next position if necessary.
        """
        for matcher in self.rule_matcher_list[:]:
            while matcher.get_break_position() <= self.end_position:
                matcher.find()
                if matcher.hit_end():
                    self.rule_matcher_list.remove(matcher)
                    break

    def cut_matchers(self) -> None:
        """
        Move matchers that start before previous segment end.
        """

        for matcher in self.rule_matcher_list[:]:
            if matcher.get_start_position() < self.end_position:
                matcher.find(self.end_position)
                if matcher.hit_end():
                    self.rule_matcher_list.remove(matcher)

    def get_min_matcher(self) -> Optional[RuleMatcher]:
        """
        Returns an iterator of the first match hit
        """

        min_position: int = MAX_INT_VALUE
        min_matcher: Optional[RuleMatcher] = None
        for matcher in self.rule_matcher_list:
            if matcher.get_break_position() < min_position:
                min_position = matcher.get_break_position()
                min_matcher = matcher

        return min_matcher

    def is_exception(self, rule_matcher: RuleMatcher) -> bool:
        """
        Returns true if there are no exception rules preventing given
        rule matcher from breaking the text.
        @param ruleMatcher rule matcher
        @return true if rule matcher breaks the text
        """

        for rule in self.rule_manager.get_exception_rules(rule_matcher.rule):
            if rule_matches_at(
                self.document,
                rule,
                self.text_manager.get_text(),
                rule_matcher.get_break_position(),
                self._boundary_cache,
            ):
                return False
        return True

    def __next__(self) -> str:
        """
        Finds the next match.
        Returns the next segment, or null if it does not exist
        """

        if self.has_next():
            if self.segment is None:
                self.init_matchers()

            found: bool = False

            while not found:
                min_matcher: Optional[RuleMatcher] = self.get_min_matcher()

                if min_matcher is None and not self.text_manager.has_more_text():
                    found = True
                    self.end_position = len(self.text_manager.get_text())
                else:
                    if self.text_manager.has_more_text() and (
                        min_matcher is None
                        or min_matcher.get_break_position() > self.text_manager.buffer_length - self.margin
                    ):
                        if self.start_position == 0:
                            raise Exception(
                                "Buffer too short"
                                + " - it must be at least as long as the"
                                + " longest segment in the text; "
                                + "try using the bufferLength option"
                            )

                        self.text_manager.read_text(self.start_position)
                        self.start_position = 0
                        self._boundary_cache = {}
                        self.init_matchers()
                        min_matcher = self.get_min_matcher()

                    self.end_position = min_matcher.get_break_position()

                    if self.end_position > self.start_position:
                        found = self.is_exception(min_matcher)

                        if found:
                            self.cut_matchers()

                self.move_matchers()

            self.segment = self.text_manager.get_text()[self.start_position : self.end_position]
            self.start_position = self.end_position

            return self.segment
        else:
            raise StopIteration

    def has_next(self) -> bool:
        return self.text_manager.has_more_text() or self.start_position < len(self.text_manager.get_text())
