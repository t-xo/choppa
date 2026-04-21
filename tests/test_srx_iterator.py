from choppa.iterators import SrxTextIterator, AbstractTextIterator
from choppa.srx_parser import SrxDocument

import unittest
from tests.abstract_srx_iterator import AbstractSrxTextIterator


class SrxTextIteratorTest(unittest.TestCase, AbstractSrxTextIterator):
    __test__ = True

    def get_text_iterator(self, document: SrxDocument, language_code: str, text: str) -> AbstractTextIterator:
        return SrxTextIterator(document, language_code, text)
