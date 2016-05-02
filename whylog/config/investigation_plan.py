from datetime import datetime

import dateutil.parser
import dateutil.tz
import six


class InvestigationPlan(object):
    """
    Represents all rules that can be fulfilled in single investigation.
    Also contains all investigation metadata, what means all pairs
    (investigationstep, logtype) neccesary for investigation
    For single log type we have single investigation step.
    """

    def __init__(self, suspected_rules, investigation_metadata, effect_clues):
        self._suspected_rules = suspected_rules
        self._investigation_metadata = investigation_metadata
        self._effect_clues = effect_clues

    def get_next_investigation_step_with_log_type(self):
        return (meta_data for meta_data in self._investigation_metadata)

    def suspected_rules(self):
        for rule in self._suspected_rules:
            yield rule

    def get_effect_clues(self):
        return self._effect_clues


class InvestigationStep(object):
    """
    Contains all parsers for single log type that can be matched in actual investigation.
    This class is responsible for finding all possible Clues from parsed logs.
    Also controls searched time range in logs file.
    """
    EARLIEST_DATE = datetime.min.replace(tzinfo=dateutil.tz.tzutc())

    def __init__(self, parser_subset, effect_time, earliest_cause_time=EARLIEST_DATE):
        self._parser_subset = parser_subset
        self.effect_time = InvestigationStep.add_zero_timezone(effect_time)
        self.earliest_cause_time = InvestigationStep.add_zero_timezone(earliest_cause_time)

    def is_line_in_time_range(self, line):
        #TODO: write method that check that line is in primary key values range
        return True

    @classmethod
    def add_zero_timezone(cls, date):
        if date.tzinfo is None:
            return date.replace(tzinfo=dateutil.tz.tzutc())
        return date

    def get_clues(self, line, offset, line_source):
        converted_params = self._parser_subset.convert_parsers_groups_from_matched_line(line)
        return dict(
            (parser_name, Clue(converted_groups, line, offset, line_source))
            for parser_name, converted_groups in six.iteritems(converted_params)
        )


class Clue(object):
    """
    Collects all the data that parser subset can extract from single log line.
    Also, contains parsed line and its source.
    """

    def __init__(self, regex_parameters, line_prefix_content, line_offset, line_source):
        self.regex_parameters = regex_parameters
        self.line_prefix_content = line_prefix_content
        self.line_offset = line_offset
        self.line_source = line_source

    def __repr__(self):
        if all(elem is None for elem in self.__dict__.values()):
            return "(Clue: UNMATCHED)"
        return "(Clue: %s, %s, %s, %s)" % (
            self.regex_parameters, self.line_prefix_content, self.line_offset, self.line_source
        )

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class LineSource(object):
    def __init__(self, host, path):
        self.host = host
        self.path = path

    def __repr__(self):
        return "(LineSource: %s:%s)" % (self.host, self.path)
