import pathlib
import regex as re  # type: ignore
from xml.sax.handler import ContentHandler
from xml.sax import parse as sax_parse

from typing import Union, Dict, List, Optional
import xmlschema  # type: ignore

from .structures import Rule, LanguageRule, LanguageMap
from .rule_manager import RuleManager


class SrxDocument:
    def __init__(
        self,
        cascade: bool = True,
        ruleset: Union[pathlib.Path, None, str, io.StringIO, io.BytesIO] = None,
        validate_ruleset: Union[pathlib.Path, None, str] = None,
        parameter_map: Optional[Dict[str, Any]] = None,
        default_pattern_flags: int = 0,
    ) -> None:
        """
        Creates empty document.
        cascade True if document is cascading
        ruleset a path to the srx xml file to be loaded, or an open reader, or string.
        validate_ruleset a filepath to xsd (or None, to disable validation) to validate against DTD
        parameter_map optional parameters for transformation (e.g. map_rule_name)
        """
        from .version import SrxVersion
        from .transformers import SrxTransformer
        import io

        self.cascade = cascade
        self.language_map_list: List[LanguageMap] = []
        self.regex_cache: Dict[str, re.Regex] = {}
        self.rule_manager_cache: Dict[str, RuleManager] = {}
        self.default_pattern_flags: int = default_pattern_flags

        if ruleset is not None:
            if isinstance(ruleset, (str, pathlib.Path)) and not ruleset.startswith("<"):
                with open(str(ruleset), "r", encoding="utf-8") as f:
                    xml_content = f.read()
            elif hasattr(ruleset, "read"):
                xml_content = ruleset.read()
                if isinstance(xml_content, bytes):
                    xml_content = xml_content.decode("utf-8")
            else:
                xml_content = str(ruleset)

            try:
                version = SrxVersion.detect(io.StringIO(xml_content))
                if version == SrxVersion.VERSION_1_0:
                    xml_content = SrxTransformer.transform(xml_content, parameter_map)
            except Exception:
                pass

            if validate_ruleset is not None:
                schema: xmlschema.XMLSchema = xmlschema.XMLSchema(str(validate_ruleset))
                schema.validate(xml_content)

            sax_parse(io.StringIO(xml_content), SRXHandler(document=self))

    def add_language_map(self, pattern: str, language_rule: LanguageRule) -> None:
        """
        Add language map to this document.
        """
        self.language_map_list.append(LanguageMap(pattern, language_rule))

    def compile(self, regex: str, flags: Optional[int] = None) -> re.Regex:
        """
        Compiles given pattern as regex.Regex (V1), caches it.
        Fixes Java-style anchors and character classes.
        Fixes Java-style anchors and character classes.
        Default flags are Unicode and VERSION1. re.M is NOT included by default.
        Uses document's default_pattern_flags if no flags provided.
        """
        if flags is None:
            flags = re.U | re.V1 | self.default_pattern_flags

        key: str = f"PATTERN_{regex}_{flags}"

        pattern: Optional[re.Regex] = self.regex_cache.get(key, None)

        if pattern is None:
            regex = re.sub(r"(?<!\\)(?<=^|\||\()\^", r"(?:\\G|^)", regex)

            regex = regex.replace(r"\h", r"\p{H}").replace(r"\v", r"\p{V}")

            pattern = re.compile(regex, flags=flags)
            self.regex_cache[key] = pattern

        return pattern

    def get_rule_manager(
        self, language_rule_list: List[LanguageRule], max_lookbehind_construct_length: int
    ) -> RuleManager:
        key: str = f"RULE_MANAGER_{language_rule_list}_{max_lookbehind_construct_length}"

        rule_manager: Optional[RuleManager] = self.rule_manager_cache.get(key, None)

        if rule_manager is None:
            rule_manager = RuleManager(self, language_rule_list, max_lookbehind_construct_length)
            self.rule_manager_cache[key] = rule_manager

        return rule_manager

    def get_language_rule_list(self, language_code: str) -> List[LanguageRule]:
        """
        If cascade is true then returns all language rules matching given
        language code. If cascade is false returns first language rule matching
        given language code. If no matching language rules are found returns
        empty list.

        language_code language code, for example en_US
        matching language rules

        """

        matching_language_rule_list: List[LanguageRule] = []
        for language_map in self.language_map_list:
            if language_map.matches(language_code):
                matching_language_rule_list.append(language_map.language_rule)
                if not self.cascade:
                    break
        return matching_language_rule_list


class SRXHandler(ContentHandler):
    """
    Represents SRX 2.0 document parser. Responsible for creating and initializing
    Document according to given SRX. Uses SAX.
    """

    def __init__(self, document: SrxDocument) -> None:
        self.break_rule: bool = False
        self.before_break: list = []
        self.after_break: list = []
        self.language_rule: Optional[LanguageRule] = None
        self.language_rule_map: Dict[str, LanguageRule] = {}
        self.element_name: Optional[str] = None
        self.document = document

    def startDocument(self):
        self.reset_rule()

    def reset_rule(self):
        self.break_rule = False
        self.before_break = []
        self.after_break = []

    def startElement(self, name, attrs):
        self.element_name = name

        if name == "header":
            self.document.cascade = attrs.get("cascade") == "yes"
        elif name == "languagerule":
            language_rule_name: str = attrs.get("languagerulename")
            self.language_rule = LanguageRule(language_rule_name)
            self.language_rule_map[language_rule_name] = self.language_rule
        elif name == "languagemap":
            language_pattern: str = attrs.get("languagepattern")
            language_rule_name: str = attrs.get("languagerulename")
            self.document.add_language_map(language_pattern, self.language_rule_map.get(language_rule_name))
        elif name == "rule":
            self.break_rule = attrs.get("break") != "no"

    def endElement(self, name):
        self.element_name = None

        if name == "rule":
            rule = Rule(self.break_rule, "".join(self.before_break), "".join(self.after_break))
            self.language_rule.add_rule(rule)
            self.reset_rule()

    def characters(self, content):
        if self.element_name == "beforebreak":
            self.before_break.append(content)
        elif self.element_name == "afterbreak":
            self.after_break.append(content)
