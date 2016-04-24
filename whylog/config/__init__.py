import itertools
import os
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from datetime import datetime

import six
import yaml

from whylog.assistant.exceptions import UnsupportedAssistantError
from whylog.assistant.regex_assistant import RegexAssistant
from whylog.config.exceptions import UnsupportedFilenameMatcher
from whylog.config.filename_matchers import RegexFilenameMatcher, RegexFilenameMatcherFactory
from whylog.config.investigation_plan import Clue, InvestigationPlan, InvestigationStep, LineSource
from whylog.config.log_type import LogType
from whylog.config.parsers import ConcatenatedRegexParser, RegexParserFactory
from whylog.config.rule import RegexRuleFactory


class ConfigFactory(object):
    WHYLOG_DIR = '.whylog'
    HOME_DIR = os.path.expanduser("~")
    ETC_DIR = '/etc'
    CONFIG_PATHS_FILE = 'config.yaml'

    @classmethod
    def load_config(cls, path):
        with open(path, "r") as config_file:
            config_paths = yaml.load(config_file)
            assistants_dict = {'regex': RegexAssistant}
            assistant_name = config_paths.pop('pattern_assistant')
            assistant_class = assistants_dict.get(assistant_name)
            if assistant_class is None:
                raise UnsupportedAssistantError(assistant_name)
            return YamlConfig(**config_paths), assistant_class

    @classmethod
    def _search_in_parents_directories(cls, path):
        if os.path.isdir(ConfigFactory.WHYLOG_DIR):
            return path
        for i in itertools.cycle([1]):
            path, suffix = os.path.split(path)
            if suffix == '':
                return None
            if os.path.isdir(os.path.join(path, ConfigFactory.WHYLOG_DIR)):
                return path

    @classmethod
    def _check_concrete_directory(cls, path):
        if os.path.isdir(path):
            return True
        return False

    @classmethod
    def _find_path_to_config(cls):
        path = ConfigFactory._search_in_parents_directories(os.getcwd())
        if path is not None:
            return os.path.join(path, ConfigFactory.WHYLOG_DIR)
        dir_to_check = [
            os.path.join(ConfigFactory.HOME_DIR, ConfigFactory.WHYLOG_DIR),
            os.path.join(ConfigFactory.ETC_DIR, ConfigFactory.WHYLOG_DIR)
        ]
        for directory in dir_to_check:
            if ConfigFactory._check_concrete_directory(directory):
                return directory

    @classmethod
    def _create_empty_file(cls, path):
        open(path, 'w').close()

    @classmethod
    def _create_new_config_dir(cls, base_path):
        path = os.path.join(base_path, ConfigFactory.WHYLOG_DIR)
        os.mkdir(path, 0o755)
        files_names = {
            'parsers_path': 'parsers.yaml',
            'rules_path': 'rules.yaml',
            'log_types_path': 'log_types.yaml'
        }
        config_paths = {}
        for key, file_name in files_names.items():
            path = os.path.join(base_path, ConfigFactory.WHYLOG_DIR, file_name)
            ConfigFactory._create_empty_file(path)
            config_paths[key] = os.path.join(base_path, path)
        config_paths['pattern_assistant'] = 'regex'
        path_to_config = os.path.join(
            base_path, ConfigFactory.WHYLOG_DIR, ConfigFactory.CONFIG_PATHS_FILE
        )
        with open(path_to_config, 'w') as config_file:
            config_file.write(yaml.safe_dump(config_paths, explicit_start=True))
        return path_to_config

    @classmethod
    def get_config(cls):
        path = ConfigFactory._find_path_to_config()
        if path is not None:
            path_to_config = os.path.join(path, ConfigFactory.CONFIG_PATHS_FILE)
            return ConfigFactory.load_config(path_to_config)
        path_to_config = ConfigFactory._create_new_config_dir(os.getcwd())
        return ConfigFactory.load_config(path_to_config)


@six.add_metaclass(ABCMeta)
class AbstractConfig(object):
    def __init__(self):
        self._parsers = self._load_parsers()
        self._parsers_grouped_by_log_type = self._index_parsers_by_log_type(
            six.itervalues(
                self._parsers
            )
        )
        self._rules = self._load_rules()
        self._log_types = self._load_log_types()

    @abstractmethod
    def _load_parsers(self):
        pass

    @abstractmethod
    def _load_rules(self):
        pass

    @abstractmethod
    def _load_log_types(self):
        pass

    @classmethod
    def _index_parsers_by_log_type(cls, parsers):
        grouped_parsers = defaultdict(list)
        for parser in parsers:
            grouped_parsers[parser.log_type].append(parser)
        return grouped_parsers

    def add_rule(self, user_rule_intent):
        created_rule = RegexRuleFactory.create_from_intent(user_rule_intent)
        self._save_rule_definition(created_rule.serialize())
        created_parsers = created_rule.get_new_parsers(self._parsers)
        self._save_parsers_definition(parser.serialize() for parser in created_parsers)
        self._rules.append(created_rule)
        for parser in created_parsers:
            self._parsers[parser.name] = parser

    def add_log_type(self, log_type):
        # TODO Can assume that exists only one LogType object for one log type name
        pass

    @abstractmethod
    def _save_rule_definition(self, rule_definition):
        pass

    @abstractmethod
    def _save_parsers_definition(self, parser_definitions):
        pass

    def create_investigation_plan(self, front_input, log_type):
        matching_parsers, effect_params = self._find_matching_parsers(
            front_input.line_content, log_type.name
        )
        suspected_rules = self._filter_rule_set(matching_parsers)
        concatenated_parsers = self._create_concatenated_parsers_for_investigation(suspected_rules)
        #TODO: creating clues base on effect_params
        #TODO: remove mocks
        effect_time = datetime(2015, 12, 3, 12, 8, 9)
        line_source = LineSource('localhost', 'node_1.log', 40)
        effect_clues = {'effect': Clue((effect_time,), 'node_1.log', line_source)}
        steps = self._create_steps_in_investigation(
            concatenated_parsers, suspected_rules, effect_clues
        )
        return InvestigationPlan(suspected_rules, steps, effect_clues)

    def get_log_type(self, front_input):
        # TODO: remove mock
        matcher = RegexFilenameMatcher('localhost', 'node_1.log', 'default')
        return LogType('default', [matcher])

    def _find_matching_parsers(self, effect_line_content, log_type_name):
        """
        This method finding all parsers from Config base which matching with effect_line_content
        """
        matching_parsers = []
        extracted_params = {}
        for parser in self._parsers_grouped_by_log_type[log_type_name]:
            params = parser.get_regex_params(effect_line_content)
            if params is not None:
                extracted_params[parser.name] = params
                matching_parsers.append(parser)
        return matching_parsers, extracted_params

    def _filter_rule_set(self, parsers_list):
        """
        This method finding all rules from Config base which can be fulfilled in
        single investigation base on parsers_list found by _find_matching_parsers
        """
        suspected_rules = []
        for parser in parsers_list:
            rules = self._rules.get(parser.name)
            if rules is not None:
                suspected_rules.extend(rules)
        return suspected_rules

    @classmethod
    def _create_concatenated_parsers_for_investigation(cls, rules):
        """
        Create concatenated parser for all log types which participate in given investigation based
        on suspected rules found by _filter_rule_set
        """
        grouped_parsers = defaultdict(list)
        inserted_parsers = set()
        for suspected_rule in rules:
            for parser in suspected_rule.get_causes_parsers():
                if parser.name not in inserted_parsers:
                    grouped_parsers[parser.log_type].append(parser)
                    inserted_parsers.add(parser.name)
        return dict(
            (log_type_name, ConcatenatedRegexParser(parsers))
            for log_type_name, parsers in six.iteritems(grouped_parsers)
        )

    def _create_steps_in_investigation(self, concatenated_parsers, suspected_rules, effect_clues):
        steps = []
        for log_type_name, parser in six.iteritems(concatenated_parsers):
            log_type = self._log_types[log_type_name]
            #TODO mocked for 003_test
            #TODO calculate effect time(or other primary key value) and earliest cause time(or other primary key value)
            #TODO base on effect_clues and suspected_rules per log type
            effect_time = datetime(2015, 12, 3, 12, 8, 9)  #TODO remove mock
            earliest_cause_time = datetime(2015, 12, 3, 12, 8, 8)  #TODO remove mock
            investigation_step = InvestigationStep(parser, effect_time, earliest_cause_time)
            steps.append((investigation_step, log_type))
        return steps


@six.add_metaclass(ABCMeta)
class AbstractFileConfig(AbstractConfig):
    def __init__(self, parsers_path, rules_path, log_type_path):
        self._parsers_path = parsers_path
        self._rules_path = rules_path
        self._log_type_path = log_type_path
        super(AbstractFileConfig, self).__init__()

    def _load_parsers(self):
        return dict(
            (parser_definition["name"], RegexParserFactory.from_dao(parser_definition))
            for parser_definition in self._load_file_with_config(self._parsers_path)
        )

    def _load_rules(self):
        loaded_rules = defaultdict(list)
        for serialized_rule in self._load_file_with_config(self._rules_path):
            rule = RegexRuleFactory.from_dao(serialized_rule, self._parsers)
            loaded_rules[serialized_rule["effect"]].append(rule)
        return loaded_rules

    def _load_log_types(self):
        matchers = defaultdict(list)
        matcher_definitions = self._load_file_with_config(self._log_type_path)
        matchers_factory_dict = {'RegexFilenameMatcher': RegexFilenameMatcherFactory}
        for definition in matcher_definitions:
            matcher_class_name = definition['matcher_class_name']
            factory_class = matchers_factory_dict.get(matcher_class_name)
            if factory_class is None:
                raise UnsupportedFilenameMatcher(matcher_class_name)
            matcher = factory_class.from_dao(definition)
            matchers[definition['log_type_name']].append(matcher)
        return dict(
            (log_type_name, LogType(log_type_name, log_type_matchers))
            for log_type_name, log_type_matchers in matchers.items()
        )

    @abstractmethod
    def _load_file_with_config(self, path):
        pass

    def _save_rule_definition(self, rule_definition):
        with open(self._rules_path, "a") as rules_file:
            rules_file.write(self._convert_rule_to_file_form(rule_definition))

    def _save_parsers_definition(self, parser_definitions):
        with open(self._parsers_path, "a") as parsers_file:
            parsers_file.write(self._convert_parsers_to_file_form(parser_definitions))

    @abstractmethod
    def _convert_rule_to_file_form(self, dict_definition):
        pass

    @abstractmethod
    def _convert_parsers_to_file_form(self, dict_definition):
        pass


class YamlConfig(AbstractFileConfig):
    def __init__(self, parsers_path, rules_path, log_types_path):
        super(YamlConfig, self).__init__(parsers_path, rules_path, log_types_path)

    def _load_file_with_config(self, path):
        with open(path, "r") as config_file:
            return list(yaml.load_all(config_file))

    def _convert_rule_to_file_form(self, rule_definition):
        return yaml.safe_dump(rule_definition, explicit_start=True)

    def _convert_parsers_to_file_form(self, parser_definitions):
        return yaml.safe_dump_all(parser_definitions, explicit_start=True)


class RuleSubset(object):
    def __init__(self, rule_dict):
        pass

    def get_logs_types(self):
        pass

    def get_rules_for_log_type(self, log_type):
        pass

    def get_parsers_for_log_type(self, log_type):
        pass
