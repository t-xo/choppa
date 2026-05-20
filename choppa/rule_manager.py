from typing import List, Dict

from choppa.structures import LanguageRule, Rule

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .srx_parser import SrxDocument


class RuleManager:
    def __init__(
        self,
        document: "SrxDocument",
        language_rule_list: List[LanguageRule],
        max_boundary_context_length: int,
    ) -> None:
        """
        Constructor. Responsible for retrieving rules from SRX document for
        given language code, constructing patterns and storing them in
        quick accessible format.
        Adds break rules to break_rule_list and constructs
        corresponding exception rule lists in exception_rule_map
        Uses document cache to store rules and patterns.
        """
        self.document = document
        self.max_boundary_context_length = max_boundary_context_length

        self.break_rule_list: List[Rule] = []
        self.exception_rule_map: Dict[Rule, List[Rule]] = {}

        exception_rule_list: List[Rule] = []

        for language_rule in language_rule_list:
            for rule in language_rule.rules:
                if rule.is_break:
                    self.break_rule_list.append(rule)
                    self.exception_rule_map[rule] = exception_rule_list[:]
                else:
                    exception_rule_list.append(rule)

    def get_exception_rules(self, break_rule: Rule) -> List[Rule]:
        """
        @param break_rule
        @return exception rules that apply before the given break rule
        """

        return self.exception_rule_map.get(break_rule, [])
