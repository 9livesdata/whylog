import os.path
import re
from unittest import TestCase
import yaml
from whylog.config import YamlConfig
from whylog.config.parsers import ConcatedRegexParser, RegexParserFactory
from whylog.config.rule import RegexRuleFactory
from whylog.teacher.user_intent import UserConstraintIntent, UserParserIntent, UserRuleIntent

# Constraint types
identical_constr = "identical"
different_constr = "different"
hetero_constr = "hetero"

# convertions
to_date = "date"

content1 = "2015-12-03 12:08:09 Connection error occurred on alfa36. Host name: 2"
content2 = "2015-12-03 12:10:10 Data migration from alfa36 to alfa21 failed. Host name: 2"
content3 = "2015-12-03 12:11:00 Data is missing at alfa21. Loss = 567.02 GB. Host name: 101"
content4 = "root cause"

regex1 = "^(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) Connection error occurred on (.*)\. Host name: (.*)$"
regex2 = "^(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) Data migration from (.*) to (.*) failed\. Host name: (.*)$"
regex3 = "^(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) Data is missing at (.*)\. Loss = (.*) GB\. Host name: (.*)$"
regex4 = "^root cause$"
regex5 = "^(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) Data is missing"

parser_intent1 = UserParserIntent("connectionerror", "hydra", regex1, [1], {1: to_date})
parser_intent2 = UserParserIntent("datamigration", "hydra", regex2, [1], {1: to_date})
parser_intent3 = UserParserIntent("lostdata", "filesystem", regex3, [1], {1: to_date})
parser_intent4 = UserParserIntent("rootcause", "filesystem", regex4, [], {})
parser_intent5 = UserParserIntent("date", "filesystem", regex5, [1], {1: to_date})

parsers = {0: parser_intent1, 1: parser_intent2, 2: parser_intent3}
effect_id = 2

constraint1 = UserConstraintIntent(identical_constr, [[0, 2], [1, 2]])
constraint2 = UserConstraintIntent(identical_constr, [[1, 3], [2, 2]])
constraint3 = UserConstraintIntent(different_constr, [[1, 2], [1, 3]])
constraint4 = UserConstraintIntent(hetero_constr, [[0, 3], [1, 4], [2, 4]], {"different": 1})

constraints = [constraint1, constraint2, constraint3, constraint4]

user_intent = UserRuleIntent(effect_id, parsers, constraints)

path_test_files = ['whylog', 'tests', 'tests_config', 'test_files']


class TestBasic(TestCase):
    def test_simple_transform(self):
        rule = RegexRuleFactory.create_from_intent(user_intent)

        assert rule._effect.regex_str == regex3
        assert sorted(cause.regex_str for cause in rule._causes) == [regex1, regex2]

    def test_parser_serialization(self):
        parser1 = RegexParserFactory.create_from_intent(parser_intent1)
        parser2 = RegexParserFactory.create_from_intent(parser_intent2)
        parser3 = RegexParserFactory.create_from_intent(parser_intent3)
        parsers_list = [parser1, parser2, parser3]

        parsers_dao_list = [parser.serialize() for parser in parsers_list]
        dumped_parsers = yaml.dump_all(parsers_dao_list, explicit_start=True)
        loaded_parsers = [
            RegexParserFactory.from_dao(dumped_parser)
            for dumped_parser in yaml.load_all(dumped_parsers)
        ]
        dumped_parsers_again = yaml.dump_all(
            [parser.serialize() for parser in loaded_parsers],
            explicit_start=True
        )

        assert dumped_parsers_again == dumped_parsers

    def test_loading_single_rule_its_parsers(self):
        path = os.path.join(*path_test_files)
        parsers_path = os.path.join(path, 'parsers.yaml')
        rules_path = os.path.join(path, 'rules.yaml')
        log_type_path = os.path.join(path, 'log_type.yaml')

        config = YamlConfig(parsers_path, rules_path, log_type_path)
        assert len(config._rules) == 1
        rule = config._rules[0]
        assert sorted([cause.name for cause in rule._causes] + [rule._effect.name]) == sorted(
            parser.name for parser in config._parsers.values()
        )

    def test_concated_regex(self):
        parser1 = RegexParserFactory.create_from_intent(parser_intent1)
        parser2 = RegexParserFactory.create_from_intent(parser_intent2)
        parser3 = RegexParserFactory.create_from_intent(parser_intent3)
        parser4 = RegexParserFactory.create_from_intent(parser_intent4)
        parser5 = RegexParserFactory.create_from_intent(parser_intent5)

        concated = ConcatedRegexParser([parser1, parser2, parser3, parser4, parser5])
        assert concated._forward_parsers_indexes == {
            parser1.name: (0, 3),
            parser2.name: (4, 4),
            parser3.name: (9, 4),
            parser4.name: (14, 0),
            parser5.name: (15, 1)
        }

        assert concated.get_extracted_regex_params("aaaaa") == {}
        assert concated.get_extracted_regex_params(content1) == {
            parser1.name: [
                "2015-12-03 12:08:09", "alfa36", "2"
            ]
        }
        assert concated.get_extracted_regex_params(content2) == {
            parser2.name: [
                "2015-12-03 12:10:10", "alfa36", "alfa21", "2"
            ]
        }
        assert concated.get_extracted_regex_params(content3) == {
            parser3.name: ["2015-12-03 12:11:00", "alfa21", "567.02", "101"],
            parser5.name: ["2015-12-03 12:11:00"]
        }

        assert concated.get_extracted_regex_params(content4) == {parser4.name: []}

        assert re.match(
            "(" + regex5 + ")|(" + regex3 + ")", content3
        ).groups() == (
            '2015-12-03 12:11:00 Data is missing', '2015-12-03 12:11:00', None, None, None, None,
            None
        )
        assert re.match("(" + regex3 + ")|(" + regex5 + ")", content3).groups() == (
            '2015-12-03 12:11:00 Data is missing at alfa21. Loss = 567.02 GB. Host name: 101',
            '2015-12-03 12:11:00', 'alfa21', '567.02', '101', None, None
        )
