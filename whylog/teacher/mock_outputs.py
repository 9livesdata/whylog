from whylog.assistant.const import AssistantType
from whylog.assistant.pattern_match import ParamGroup
from whylog.teacher.user_intent import UserConstraintIntent, UserParserIntent, UserRuleIntent


def create_sample_rule():
    identical_constr = "identical"
    different_constr = "different"
    hetero_constr = "hetero"

    to_date = "date"
    to_string = "string"
    to_int = "int"

    sample_line1 = "2016-04-12 23:54:45 Connection error occurred on comp1. Host name: host1"
    sample_line2 = "2016-04-12 23:54:40 Data migration from comp1 to comp2 failed. Host name: host2"
    sample_line3 = "2016-04-12 23:54:43 Data is missing at comp2. Loss = 150 GB. Host name: host2"

    regex1 = "^(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) Connection error occurred on (.*)\. Host name: (.*)$"
    regex2 = "^(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) Data migration from (.*) to (.*) failed\. Host name: (.*)$"
    regex3 = "^(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) Data is missing at (.*)\. Loss = (.*) GB\. Host name: (.*)$"

    # yapf: disable
    groups1 = {
        1: ParamGroup("2016-04-12 23:54:45", to_date),
        2: ParamGroup("comp1", to_string),
        3: ParamGroup("host1", to_string)
    }
    groups2 = {
        1: ParamGroup("2016-04-12 23:54:40", to_date),
        2: ParamGroup("comp2", to_string),
        3: ParamGroup("host2", to_string)
    }
    groups3 = {
        1: ParamGroup("2016-04-12 23:54:43", to_date),
        2: ParamGroup("comp2", to_string),
        3: ParamGroup("150", to_int),
        4: ParamGroup("host2", to_string)
    }

    # resource location is temporary a string, because there is no ResourceLocation class yet.
    # TODO: Change following resource locations to ResourceLocation objects
    resource_location1 = "serwer1"
    resource_location2 = "serwer2"
    resource_location3 = "serwer3"

    regex_type = AssistantType.REGEX

    parser_intent1 = UserParserIntent(
        regex_type, "connectionerror", regex1, "hydra", [1], groups1, sample_line1, 18,
        resource_location1
    )
    parser_intent2 = UserParserIntent(
        regex_type, "datamigration", regex2, "hydra", [1], groups2, sample_line2, 9,
        resource_location2
    )
    parser_intent3 = UserParserIntent(
        regex_type, "lostdata", regex3, "filesystem", [1], groups3, sample_line3, 1994,
        resource_location3
    )
    # yapf: enable

    parsers = {0: parser_intent1, 1: parser_intent2, 2: parser_intent3}
    effect_id = 2

    constraint1 = UserConstraintIntent(identical_constr, [[0, 2], [1, 2]])
    constraint2 = UserConstraintIntent(identical_constr, [[1, 3], [2, 2]])
    constraint3 = UserConstraintIntent(different_constr, [[1, 2], [1, 3]])
    constraint4 = UserConstraintIntent(hetero_constr, [[0, 3], [1, 4], [2, 4]], {"different": 1})

    constraints = [constraint1, constraint2, constraint3, constraint4]

    return UserRuleIntent(effect_id, parsers, constraints)
