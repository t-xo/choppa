import unittest
import io
import regex as re
from choppa.srx_parser import SrxDocument
from choppa.iterators import SrxTextIterator, FastTextIterator
from choppa.version import SrxVersion
from choppa.utils import remove_capturing_groups

class ExtensiveTest(unittest.TestCase):
    def test_remove_capturing_groups(self):
        self.assertEqual(remove_capturing_groups(r"(abc)"), r"(?:abc)")
        self.assertEqual(remove_capturing_groups(r"(?:abc)"), r"(?:abc)")
        self.assertEqual(remove_capturing_groups(r"\((abc)"), r"\((?:abc)")
        # \Q \E handled by side effect (escapes every char including alphanumeric)
        # Matches Java's Util.java implementation
        self.assertEqual(remove_capturing_groups(r"\Q(abc)\E"), r"\(\a\b\c\)")

    def test_srx_version_detection(self):
        srx1 = '<srx version="1.0"><body></body></srx>'
        srx2 = '<srx version="2.0" xmlns="http://www.lisa.org/srx20"><body></body></srx>'
        
        self.assertEqual(SrxVersion.detect(io.StringIO(srx1)), SrxVersion.VERSION_1_0)
        self.assertEqual(SrxVersion.detect(io.StringIO(srx2)), SrxVersion.VERSION_2_0)

    def test_srx1_transformation(self):
        # A simple SRX 1.0 document
        srx1_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<srx version="1.0">
    <header segmentsubflows="yes"/>
    <body>
        <languagerules>
            <languagerule languagerulename="Default">
                <rule break="yes">
                    <beforebreak>\.</beforebreak>
                    <afterbreak>\s</afterbreak>
                </rule>
            </languagerule>
        </languagerules>
        <maprules>
            <maprule maprulename="Default">
                <languagemap languagepattern=".*" languagerulename="Default"/>
            </maprule>
        </maprules>
    </body>
</srx>"""
        # Parsing this should automatically transform it
        document = SrxDocument(ruleset=srx1_content)
        self.assertEqual(document.cascade, False) # cascade="no" is added by transformer
        
        lang_rules = document.get_language_rule_list("en")
        self.assertEqual(len(lang_rules), 1)
        self.assertEqual(lang_rules[0].name, "Default")
        self.assertEqual(len(lang_rules[0].rules), 1)
        self.assertEqual(lang_rules[0].rules[0].before_pattern, r"\.")

    def test_fast_iterator_parity(self):
        srx_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<srx version="2.0">
    <header cascade="yes"/>
    <body>
        <languagerules>
            <languagerule languagerulename="Default">
                <rule break="no">
                    <beforebreak>Mr\.</beforebreak>
                    <afterbreak>\s</afterbreak>
                </rule>
                <rule break="yes">
                    <beforebreak>\.</beforebreak>
                    <afterbreak>\s</afterbreak>
                </rule>
            </languagerule>
        </languagerules>
        <maprules>
            <languagemap languagepattern=".*" languagerulename="Default"/>
        </maprules>
    </body>
</srx>"""
        document = SrxDocument(ruleset=srx_content)
        text = "Mr. Smith is here. He is happy."
        
        # Standard Iterator
        it_std = SrxTextIterator(document, "en", text)
        segments_std = list(it_std)
        
        # Fast Iterator
        it_fast = FastTextIterator(document, "en", text)
        segments_fast = list(it_fast)
        
        self.assertEqual(segments_std, segments_fast)
        self.assertEqual(segments_std, ["Mr. Smith is here.", " He is happy."])

if __name__ == "__main__":
    unittest.main()
