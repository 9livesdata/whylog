from abc import ABCMeta, abstractmethod

import yaml

from whylog.config.parsers import RegexParserFactory
from whylog.config.rule import RuleFactory


from whylog.config.parsers import RegexParser


class AbstractConfig(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_investigation_plan(self, front_input):
        pass


class YamlConfig(AbstractConfig):
    def __init__(self, parsers_path, rules_path, log_locations_path, log_type_manager=None):
        self._parsers_path = parsers_path
        self._rules_path = rules_path
        self._log_locations_path = log_locations_path

    def create_investigation_plan(self, front_input):
        pass

    def _get_log_type(self, front_input):
        pass

    def _find_matching_parsers(self, front_input, log_type):
        pass

    def _filter_rule_set(self, parsers_list):
        pass

    def _get_locations_for_logs(self, logs_types_list):
        pass

    def add_rule(self, user_rule_intent):
        rule = RuleFactory.create_rule_from_user_rule_intent(user_rule_intent)
        self._save_rule_definition(rule.get_rule_in_form_to_save())
        self._save_parsers_definition(rule.get_rule_parsers_in_form_to_save())

    def _save_rule_definition(self, rule_definition):
        with open(self._rules_path, "a") as rules_file:
            rules_file.write(yaml.safe_dump(rule_definition, explicit_start=True))

    def _save_parsers_definition(self, parser_definitions):
        with open(self._parsers_path, "a") as parsers_file:
            parsers_file.write(yaml.safe_dump_all(parser_definitions, explicit_start=True))


class InvestigationPlan(object):
    def __init__(self, front_input, rule_subset, log_location_dict):
        pass

    def get_next_investigation_step(self):
        pass


class RuleSubset(object):
    def __init__(self, rule_dict):
        pass

    def get_logs_types(self):
        pass

    def get_rules_for_log_type(self, log_type):
        pass

    def get_parsers_for_log_type(self, log_type):
        pass


class InvestigationStep(object):
    """
    Represents rules, parsers and locations of logs which are necessary
    to find and parse log files with potential causes.
    """

    def __init__(self, parsers, rules, log_location, effect_time):
        pass

    def get_clues(self, line):
        """
        Basing on parsers creates clues in investigation
        :param line: line from parsed file
        :returns: list of created clues
        """
        pass


class Clue(object):
    """
    Collects all the data that parser can extract from single log line.
    Also, contains parsed line and its source.
    """

    def __init__(self, regex_parameters, line_time, line_content, line_source):
        pass


class LogLocation(object):
    def __init__(self, filename_parser, log_type):
        pass
